"""1080x1920 anatomical 3D explainer preview with voice-timeline cues.
Run: blender -b --python blender_asset_preview.py
"""
import bpy, json, math, os, sys, subprocess
from pathlib import Path
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_pipeline import build_render_manifest
from anatomy_geometry_audit import audit_geometry

OUT=Path(os.getenv("FITFUEL_3D_OUT","output/3d_preview"))
ASSET_DIR=Path("assets_3d/generated")
W,H=1080,1920
FPS=24
AUDIO_INFO=Path("output/audio_info.json")
try:
    AUDIO_ITEMS=json.loads(AUDIO_INFO.read_text(encoding="utf-8"))
    if not isinstance(AUDIO_ITEMS,list): AUDIO_ITEMS=[]
except Exception:
    AUDIO_ITEMS=[]
VOICE_TOTAL=sum(max(0.0,float(x.get("seconds",0))) for x in AUDIO_ITEMS)
DURATION=max(8.0,VOICE_TOTAL) if VOICE_TOTAL else 8.0
FRAMES=int(FPS*DURATION)

def mat(name,color,metallic=0,roughness=.42, subsurface=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*color,1)
    b.inputs["Metallic"].default_value=metallic; b.inputs["Roughness"].default_value=roughness
    if "Subsurface Weight" in b.inputs: b.inputs["Subsurface Weight"].default_value=subsurface
    return m

def smooth_sphere(name,loc,scale,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=32,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(material)
    bpy.ops.object.shade_smooth(); return o

def cylinder_between(name,a,b,radius,material,vertices=48):
    a,b=Vector(a),Vector(b); d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=d.length,location=(a+b)/2)
    o=bpy.context.object; o.name=name; o.rotation_euler=d.to_track_quat("Z","Y").to_euler()
    o.data.materials.append(material); bevel=o.modifiers.new("Soft anatomical edges","BEVEL")
    bevel.width=min(radius*.22,.035); bevel.segments=3; o.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    bpy.ops.object.shade_smooth(); return o

def tapered_tendon(name,a,b,r1,r2,material):
    a,b=Vector(a),Vector(b); d=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=r1,radius2=r2,depth=d.length,location=(a+b)/2)
    o=bpy.context.object; o.name=name; o.rotation_euler=d.to_track_quat("Z","Y").to_euler()
    o.data.materials.append(material); bevel=o.modifiers.new("Tendon edge softness","BEVEL")
    bevel.width=.018; bevel.segments=3; bpy.ops.object.shade_smooth(); return o

def curve_line(name,points,bevel,material):
    c=bpy.data.curves.new(name,"CURVE"); c.dimensions="3D"; c.bevel_depth=bevel; c.bevel_resolution=4
    s=c.splines.new("BEZIER"); s.bezier_points.add(len(points)-1)
    for p,co in zip(s.bezier_points,points):
        p.co=co; p.handle_left_type="AUTO"; p.handle_right_type="AUTO"
    o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o); o.data.materials.append(material); return o

def label(body,loc,size,material,align="CENTER"):
    bpy.ops.object.text_add(location=loc,rotation=(math.radians(90),0,0))
    o=bpy.context.object; o.name="Label_"+body.replace(" ","_"); o.data.body=body
    o.data.size=size; o.data.align_x=align; o.data.extrude=.001; o.data.materials.append(material)
    return o

def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def export(objects,path):
    try: bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
    except Exception: pass
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects: o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=str(path),export_format="GLB",use_selection=True)

def narration_timeline():
    """Map four visual beats to actual voice duration, with a safe demo fallback."""
    cues=[]
    audio=AUDIO_ITEMS
    total=0.0
    if isinstance(audio,list) and audio:
        for item in audio:
            try: total += max(0.0,float(item.get("seconds",0)))
            except Exception: pass
    if total <= 0: total=DURATION
    names=["ANATOMY OVERVIEW","TENDON & JOINT","FORCE DIRECTION","MUSCLE CONTRACTION"]
    if isinstance(audio,list) and audio:
        cursor=0.0
        for i,item in enumerate(audio):
            span=max(.1,float(item.get("seconds",0)))
            name=names[min(i,len(names)-1)] if len(audio)<=4 else f"NARRATION SCENE {i+1}"
            cues.append({"cue":name,"scene":item.get("scene",i+1),
                         "audio_file":item.get("file"),"start":round(cursor,3),
                         "end":round(cursor+span,3)})
            cursor+=span
    else:
        span=DURATION/4
        for i,name in enumerate(names):
            cues.append({"cue":name,"start":round(i*span,3),"end":round((i+1)*span,3)})
    return cues

def main():
    OUT.mkdir(parents=True,exist_ok=True); ASSET_DIR.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    navy=mat("Deep navy",(.012,.028,.052),roughness=.7)
    panel=mat("Panel",(.025,.065,.095),roughness=.62)
    bone=mat("Bone ivory",(.82,.76,.61),roughness=.42)
    cartilage=mat("Cartilage",(.22,.72,.72),roughness=.38,subsurface=.08)
    muscle=mat("Muscle belly",(.52,.055,.105),roughness=.3,subsurface=.12)
    muscle_hi=mat("Muscle fascicles",(.94,.22,.29),roughness=.28,subsurface=.12)
    tendon=mat("Tendon",(.88,.66,.46),roughness=.52)
    cyan=mat("Force cyan",(.06,.82,.95),metallic=.15,roughness=.25)
    white=mat("Typography",(.91,.96,1),roughness=.4)
    muted=mat("Secondary type",(.43,.69,.78),roughness=.5)

    # Studio stage and vertical composition.
    bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,-.55))
    floor=bpy.context.object; floor.name="Studio floor"; floor.data.materials.append(navy)
    bpy.ops.mesh.primitive_plane_add(size=14,location=(0,3,4),rotation=(math.radians(90),0,0))
    wall=bpy.context.object; wall.name="Backdrop"; wall.data.materials.append(panel)

    # Simplified, clearly labelled teaching schematic: upper arm muscle between joints.
    anatomy=[]
    shoulder=smooth_sphere("Shoulder joint", (0,0,6.0),(.52,.36,.50),cartilage); anatomy.append(shoulder)
    elbow=smooth_sphere("Elbow joint", (0,0,1.35),(.46,.34,.43),cartilage); anatomy.append(elbow)
    # Bone shafts remain behind the muscle belly; the forearm is a separate
    # articulated assembly so elbow flexion is visible rather than implied.
    humerus=cylinder_between("Humerus bone",(.34,.10,5.75),(.34,.10,1.65),.145,bone); anatomy.append(humerus)
    radius=cylinder_between("Radius bone",(-.13,.02,1.34),(-.08,.02,-1.02),.085,bone)
    ulna=cylinder_between("Ulna bone",(.16,.10,1.34),(.11,.10,-1.02),.095,bone)
    wrist=smooth_sphere("Wrist joint",(.015,.04,-1.08),(.19,.18,.17),cartilage)
    forearm=[radius,ulna,wrist]
    elbow_pivot=bpy.data.objects.new("Elbow_Flexion_Pivot",None)
    bpy.context.collection.objects.link(elbow_pivot)
    elbow_pivot.location=(0,0,1.35)
    for part in forearm:
        world=part.matrix_world.copy()
        part.parent=elbow_pivot
        part.matrix_world=world
    for frame,angle in ((1,0.0),(int(FRAMES*.25),-.38),(int(FRAMES*.5),-.92),(int(FRAMES*.75),-.55),(FRAMES,0.0)):
        elbow_pivot.rotation_euler[1]=angle
        elbow_pivot.keyframe_insert(data_path="rotation_euler",frame=frame)
    anatomy.extend(forearm)
    # Muscle belly and visible fascicle striations.
    belly=smooth_sphere("Biceps muscle belly",(0,-.22,3.65),(.43,.31,1.52),muscle); anatomy.append(belly)
    for side in (-1,1):
        for j in range(5):
            x=side*(.12+j*.065)
            line=curve_line("Muscle fascicle",[(x,-.59,2.55),(x*1.1,-.64,3.55),(x*.72,-.58,4.7)],.018,muscle_hi)
            anatomy.append(line)
    # Proximal and distal tendons visibly attach muscle to the joint/bone.
    upper_t=tapered_tendon("Proximal tendon",(0,-.16,5.05),(0,-.12,5.73),.12,.2,tendon)
    lower_t=tapered_tendon("Distal tendon",(0,-.16,2.15),(0,-.12,1.55),.095,.18,tendon)
    anatomy += [upper_t,lower_t]
    world=lower_t.matrix_world.copy()
    lower_t.parent=elbow_pivot
    lower_t.matrix_world=world
    # Joint cartilage rings.
    for z in (6.0,1.35):
        ring=smooth_sphere("Joint cartilage",(0,-.22,z),(.39,.19,.32),cyan); anatomy.append(ring)

    # Force vector arrow to the upper-right of the muscle; animated pulse/rotation.
    shaft=cylinder_between("Force vector shaft",(.48,-.50,.92),(.48,-.50,-.78),.038,cyan)
    tip=tapered_tendon("Force vector arrowhead",(.48,-.50,-.78),(.48,-.50,-1.08),.115,.003,cyan)
    force=[shaft,tip]
    for o in force:
        world=o.matrix_world.copy()
        o.parent=elbow_pivot
        o.matrix_world=world
        for frame,scale in ((1,.85),(FRAMES//2,1.12),(FRAMES,.85)):
            o.scale=(scale,scale,scale)
            o.keyframe_insert(data_path="scale",frame=frame)

    # Muscle belly shortens and bulges independently; elbow pivot drives forearm.
    base_scale=belly.scale.copy()
    for frame,zs,xs in ((1,1.0,1.0),(FRAMES//4,.94,1.06),(FRAMES//2,.88,1.12),(3*FRAMES//4,.94,1.06),(FRAMES,1.0,1.0)):
        belly.scale=(base_scale.x*xs,base_scale.y,base_scale.z*zs)
        belly.keyframe_insert(data_path="scale",frame=frame)
    root=bpy.data.objects.new("Anatomy_Animation_Root",None)
    bpy.context.collection.objects.link(root)

    # Cue boundaries are needed before visibility keyframes are authored.
    cues=narration_timeline()
    # Compact portrait-safe labels; callouts reveal in their narration beat.
    label("MUSCLE FORCE",(0,-1.25,8.18),.27,white)
    label("BICEPS / ANATOMY STUDY",(0,-1.25,7.68),.16,muted)
    cue_ranges=[(c["start"],c["end"]) for c in cues]
    callouts=[
      ("SHOULDER JOINT",(-2.12,-1.0,6.15),.135,"LEFT",0),
      ("PROXIMAL TENDON",(2.12,-1.0,5.42),.125,"RIGHT",0),
      ("MUSCLE BELLY",(-2.12,-1.0,3.72),.14,"LEFT",3),
      ("DISTAL TENDON",(2.12,-1.0,2.0),.125,"RIGHT",1),
      ("ELBOW JOINT",(-2.12,-1.0,1.22),.135,"LEFT",1),
      ("FORCE / TENSION",(2.12,-1.0,4.35),.125,"RIGHT",2)]
    for body,loc,size,align,idx in callouts:
        obj=label(body,loc,size,cyan if "FORCE" in body else white,align)
        if cues:
            st,en=cue_ranges[min(idx,len(cue_ranges)-1)]
            for frame,hidden in ((1,True),(max(1,int(st*FPS)+1),False),
                                 (max(1,int(en*FPS)),False),(min(FRAMES,int(en*FPS)+1),True)):
                obj.hide_render=hidden
                obj.keyframe_insert(data_path="hide_render",frame=frame)
            if obj.animation_data and obj.animation_data.action:
                for fc in obj.animation_data.action.fcurves:
                    for key in fc.keyframe_points: key.interpolation="CONSTANT"
    label("CONTRACTION > TENSION > MOVEMENT",(0,-1.25,-.05),.13,cyan)
    curve_line("Shoulder callout",[(.25,-.78,6.0),(.82,-.78,6.0),(1.08,-.78,6.15)],.01,muted)
    curve_line("Muscle callout",[(-.48,-.78,3.65),(-.82,-.78,3.65),(-1.08,-.78,3.72)],.01,muted)
    curve_line("Elbow callout",[(.25,-.78,1.35),(.82,-.78,1.35),(1.08,-.78,1.22)],.01,muted)

    # Audit articulated forearm anchors at every authored flexion pose before rendering.\n    geometry_issues=audit_geometry()\n    if geometry_issues:\n        raise RuntimeError("Anatomy geometry audit failed: "+"; ".join(geometry_issues))\n    print("ANATOMY_GEOMETRY_AUDIT PASS: forearm anchors remain seated across flexion poses")\n\n    # Camera: portrait orthographic framing with all content inside the safe area.
    bpy.ops.object.camera_add(location=(0,-15,4.05))
    cam=bpy.context.object; cam.name="Portrait camera"; cam.data.type="ORTHO"; cam.data.ortho_scale=10.4
    aim(cam,(0,0,4.05)); bpy.context.scene.camera=cam
    for loc,power,size in (((-4,-7,9),1700,7),((4,-3,6),1100,5),((0,1,8),900,4)):
        bpy.ops.object.light_add(type="AREA",location=loc); light=bpy.context.object
        light.data.energy=power; light.data.shape="DISK"; light.data.size=size; aim(light,(0,0,3.5))

    scene=bpy.context.scene
    try: scene.render.engine="BLENDER_EEVEE_NEXT"
    except Exception: scene.render.engine="BLENDER_EEVEE"
    if hasattr(scene,"eevee"): scene.eevee.taa_render_samples=8
    scene.render.resolution_x=W; scene.render.resolution_y=H; scene.render.resolution_percentage=100
    scene.render.fps=FPS; scene.frame_start=1; scene.frame_end=FRAMES
    scene.world.color=(.018,.028,.045); scene.view_settings.view_transform="Standard"
    scene.render.image_settings.file_format="FFMPEG"; scene.render.ffmpeg.format="MPEG4"
    scene.render.ffmpeg.codec="H264"; scene.render.ffmpeg.constant_rate_factor="MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset="GOOD"; scene.render.filepath=str(OUT/"preview.mp4")
    scene.render.resolution_percentage=100

    cues=narration_timeline()
    # Export exact source audio timing; missing TTS is explicitly marked as silent.
    sync={"fps":FPS,"duration":DURATION,"audio_attached":False,
          "audio_files":[],"timing_source":"silent_demo_fallback","cues":cues}
    (OUT/"narration_sync.json").write_text(json.dumps(sync,indent=2)+"\n",encoding="utf-8")
    # Render markers are aligned to voice segment boundaries.
    for cue in cues:
        frame=max(1,min(FRAMES,int(cue["start"]*FPS)+1))
        scene.timeline_markers.new(cue["cue"],frame=frame)

    # Export only clean anatomy parts as a reusable GLB.
    export(anatomy+[root],ASSET_DIR/"biceps_anatomy_preview.glb")
    catalog={"catalog_version":1,"assets":[
      {"asset_id":"biceps-anatomy-preview","category":"scientific","file":"generated/biceps_anatomy_preview.glb","source":"procedural-preview","license":"project-generated","review_status":"pending","scientific_accuracy_required":True,"notes":"Simplified educational schematic; not clinical-grade anatomy; requires expert review."},
      {"asset_id":"force-vector-arrow","category":"scientific","file":"generated/biceps_anatomy_preview.glb","source":"procedural-preview","license":"project-generated","review_status":"pending","scientific_accuracy_required":True,"notes":"Illustrative force vector only; direction/magnitude must be validated for the narrated exercise."}
    ]}
    Path("assets_3d/catalog.json").write_text(json.dumps(catalog,indent=2)+"\n",encoding="utf-8")
    scenes=[{"narration":"The biceps muscle connects through tendons across the shoulder and elbow joints.","visual_title":"Biceps Anatomy"},
            {"narration":"Muscle tension transfers force through the tendon and moves the forearm.","visual_title":"Force Direction"}]
    manifest=build_render_manifest(scenes,catalog=catalog)
    (OUT/"scene_asset_plan.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"preview.blend"))
    bpy.ops.render.render(animation=True)
    # Mux real TTS clips in their declared scene order when supplied by voice.py.
    if AUDIO_ITEMS:
        audio_paths=[Path(x.get("file","")) for x in AUDIO_ITEMS]
        if any(not p.is_file() or p.stat().st_size<1000 for p in audio_paths):
            raise RuntimeError("audio_info.json exists but one or more real narration MP3s are missing")
        concat=OUT/"voice_concat.txt"
        concat.write_text("".join("file '"+str(p.resolve())+"'\n" for p in audio_paths),encoding="utf-8")
        voice=OUT/"voice_track.m4a"
        subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(concat),"-c:a","aac","-b:a","192k",str(voice)],check=True)
        silent=OUT/"preview_silent.mp4"
        os.replace(OUT/"preview.mp4",silent)
        subprocess.run(["ffmpeg","-y","-v","error","-i",str(silent),"-i",str(voice),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-t",str(DURATION),"-movflags","+faststart",str(OUT/"preview.mp4")],check=True)
        sync.update({"audio_attached":True,"audio_files":[str(p) for p in audio_paths],"timing_source":"real_scene_tts"})
        (OUT/"narration_sync.json").write_text(json.dumps(sync,indent=2)+"\n",encoding="utf-8")
    print("Rendered 1080x1920 anatomy preview:",OUT/"preview.mp4")

if __name__=="__main__": main()
