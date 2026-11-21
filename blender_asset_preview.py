"""1080x1920 anatomical 3D explainer preview with voice-timeline cues.
Run: blender -b --python blender_asset_preview.py
"""
import bpy, json, math, os, sys
from pathlib import Path
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_pipeline import build_render_manifest

OUT=Path(os.getenv("FITFUEL_3D_OUT","output/3d_preview"))
ASSET_DIR=Path("assets_3d/generated")
W,H=1080,1920
FPS=24
DURATION=8.0
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
    """Build scene/voice cue boundaries from actual audio_info when available."""
    cues=[]
    audio_path=Path("output/audio_info.json")
    audio=[]
    if audio_path.exists():
        try: audio=json.loads(audio_path.read_text(encoding="utf-8"))
        except Exception: audio=[]
    if not isinstance(audio,list) or not audio: audio=[{"seconds":DURATION}]
    cursor=0.0
    names=["ANATOMY OVERVIEW","TENDON & JOINT","FORCE DIRECTION","MUSCLE CONTRACTION"]
    for i,item in enumerate(audio[:4]):
        try: seconds=max(.5,float(item.get("seconds",DURATION/len(audio))))
        except Exception: seconds=DURATION/len(audio)
        cues.append({"cue":names[min(i,len(names)-1)],"start":round(cursor,3),"end":round(cursor+seconds,3),"audio_index":i})
        cursor+=seconds
    scale=DURATION/max(cursor,.001)
    for cue in cues:
        cue["start"]=round(cue["start"]*scale,3); cue["end"]=round(cue["end"]*scale,3)
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
    shoulder=smooth_sphere("Shoulder joint", (0,0,6.0),(.68,.43,.62),cartilage); anatomy.append(shoulder)
    elbow=smooth_sphere("Elbow joint", (0,0,1.35),(.58,.4,.55),cartilage); anatomy.append(elbow)
    # Bone shafts remain behind the muscle belly.
    humerus=cylinder_between("Humerus bone",(0,.13,5.75),(0,.13,1.65),.19,bone); anatomy.append(humerus)
    # Muscle belly and visible fascicle striations.
    belly=smooth_sphere("Biceps muscle belly",(0,-.22,3.65),(.57,.42,1.68),muscle); anatomy.append(belly)
    for side in (-1,1):
        for j in range(5):
            x=side*(.12+j*.065)
            line=curve_line("Muscle fascicle",[(x,-.59,2.55),(x*1.1,-.64,3.55),(x*.72,-.58,4.7)],.018,muscle_hi)
            anatomy.append(line)
    # Proximal and distal tendons visibly attach muscle to the joint/bone.
    upper_t=tapered_tendon("Proximal tendon",(0,-.16,5.05),(0,-.12,5.73),.12,.2,tendon)
    lower_t=tapered_tendon("Distal tendon",(0,-.16,2.15),(0,-.12,1.55),.095,.18,tendon)
    anatomy += [upper_t,lower_t]
    # Joint cartilage rings.
    for z in (6.0,1.35):
        ring=smooth_sphere("Joint cartilage",(0,-.22,z),(.39,.19,.32),cyan); anatomy.append(ring)

    # Force vector arrow to the upper-right of the muscle; animated pulse/rotation.
    shaft=cylinder_between("Force vector shaft",(.95,-.45,2.5),(1.5,-.45,4.25),.055,cyan)
    tip=tapered_tendon("Force vector arrowhead",(1.5,-.45,4.25),(1.68,-.45,4.65),.17,.005,cyan)
    force=[shaft,tip]
    for o in force:
        o.keyframe_insert(data_path="location",frame=1)
        o.location.z+=.18; o.keyframe_insert(data_path="location",frame=FRAMES//2)
        o.location.z-=.18; o.keyframe_insert(data_path="location",frame=FRAMES)

    # Animation: small contraction pulses and true 3D turn around the long axis.
    root=bpy.data.objects.new("Anatomy_Animation_Root",None); bpy.context.collection.objects.link(root)
    for o in anatomy: o.parent=root
    root.rotation_mode="XYZ"
    for frame,angle,stretch in ((1,-.08,1.0),(FPS*2,.0,1.045),(FPS*4,.08,1.0),(FPS*6,0,1.035),(FRAMES, -.08,1.0)):
        root.rotation_euler=(0,angle,math.sin(frame/FRAMES*math.pi*2)*.025)
        root.scale=(1,1,stretch); root.keyframe_insert(data_path="rotation_euler",frame=frame)
        root.keyframe_insert(data_path="scale",frame=frame)

    # Layout: title, diagram, callout rails and captions occupy separate safe zones.
    label("HOW MUSCLE FORCE WORKS",(0,-1.25,8.15),.43,white)
    label("BICEPS  /  ANATOMY STUDY",(0,-1.25,7.55),.22,muted)
    label("SHOULDER JOINT",(1.25,-.9,6.2),.19,white,"LEFT")
    label("PROXIMAL TENDON",(1.25,-.9,5.45),.17,muted,"LEFT")
    label("MUSCLE BELLY",(-1.55,-.9,3.65),.2,white,"RIGHT")
    label("DISTAL TENDON",(1.15,-.9,2.05),.17,muted,"LEFT")
    label("ELBOW JOINT",(1.1,-.9,1.1),.19,white,"LEFT")
    label("FORCE / TENSION", (1.2,-.9,4.75),.17,cyan,"LEFT")
    label("CONTRACT  •  TRANSFER FORCE  •  MOVE",(0,-1.25,-.05),.19,cyan)

    # Leader lines connect labels to the correct structures.
    curve_line("Shoulder callout",[(.25,-.78,6.0),(.92,-.78,6.0),(1.18,-.78,6.18)],.012,muted)
    curve_line("Muscle callout",[(-.2,-.78,3.65),(-.9,-.78,3.65),(-1.42,-.78,3.65)],.012,muted)
    curve_line("Elbow callout",[(.25,-.78,1.35),(.8,-.78,1.35),(1.02,-.78,1.15)],.012,muted)

    # Camera: portrait orthographic framing with all content inside the safe area.
    bpy.ops.object.camera_add(location=(0,-15,4.05))
    cam=bpy.context.object; cam.name="Portrait camera"; cam.data.type="ORTHO"; cam.data.ortho_scale=10.4
    aim(cam,(0,0,4.05)); bpy.context.scene.camera=cam
    for loc,power,size in (((-4,-7,9),1700,7),((4,-3,6),1100,5),((0,1,8),900,4)):
        bpy.ops.object.light_add(type="AREA",location=loc); light=bpy.context.object
        light.data.energy=power; light.data.shape="DISK"; light.data.size=size; aim(light,(0,0,3.5))

    scene=bpy.context.scene
    try: scene.render.engine="BLENDER_EEVEE_NEXT"
    except Exception: scene.render.engine="BLENDER_EEVEE"
    if hasattr(scene,"eevee"): scene.eevee.taa_render_samples=8\n    scene.render.resolution_x=W; scene.render.resolution_y=H; scene.render.resolution_percentage=100
    scene.render.fps=FPS; scene.frame_start=1; scene.frame_end=FRAMES
    scene.world.color=(.018,.028,.045); scene.view_settings.view_transform="Standard"
    scene.render.image_settings.file_format="FFMPEG"; scene.render.ffmpeg.format="MPEG4"
    scene.render.ffmpeg.codec="H264"; scene.render.ffmpeg.constant_rate_factor="MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset="GOOD"; scene.render.filepath=str(OUT/"preview.mp4")
    scene.render.resolution_percentage=100

    cues=narration_timeline()
    # Subtitle/cue timing metadata is exported for the main compositor to align with TTS.
    (OUT/"narration_sync.json").write_text(json.dumps({"fps":FPS,"duration":DURATION,"cues":cues},indent=2)+"\n",encoding="utf-8")
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
    print("Rendered 1080x1920 anatomy preview:",OUT/"preview.mp4")

if __name__=="__main__": main()
