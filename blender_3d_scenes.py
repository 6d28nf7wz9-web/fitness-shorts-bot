"""Shared Blender 3D renderer for FitFuel Shorts and AI Long.
Creates lit, camera-framed 3D scenes (not 2D Pillow drawings). Run via:
blender -b -P blender_3d_scenes.py -- --kind exercise_biomechanics --duration 5 --output clip.mp4 --orientation portrait --text "Push-up"
"""
import bpy, math, os, sys, argparse
from mathutils import Vector

def args():
    av=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--kind",default="exercise_biomechanics")
    p.add_argument("--duration",type=float,default=5)
    p.add_argument("--output",required=True)
    p.add_argument("--orientation",choices=["portrait","landscape"],default="portrait")
    p.add_argument("--text",default="FITFUEL SCIENCE")
    p.add_argument("--exercise",default="")
    return p.parse_args(av)

A=args(); W,H=(720,1280) if A.orientation=="portrait" else (1280,720)
FPS=24; FRAMES=max(48,int(A.duration*FPS))
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.eevee.use_gtao=True; scene.eevee.gtao_distance=3; scene.eevee.gtao_factor=1.35
scene.render.resolution_x=W; scene.render.resolution_y=H; scene.render.resolution_percentage=100
scene.render.fps=FPS; scene.frame_start=1; scene.frame_end=FRAMES
scene.render.image_settings.file_format="FFMPEG"; scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"; scene.render.ffmpeg.constant_rate_factor="MEDIUM"
scene.render.filepath=os.path.abspath(A.output); scene.render.use_file_extension=True
scene.render.image_settings.color_mode="RGB"
scene.world.color=(0.012,0.018,0.03)
try: scene.view_settings.view_transform="AgX"
except: pass

def material(name,color,metal=0,rough=.32,emission=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF"); bs.inputs["Base Color"].default_value=(*color,1); bs.inputs["Metallic"].default_value=metal; bs.inputs["Roughness"].default_value=rough
    if emission:
        if "Emission Color" in bs.inputs: bs.inputs["Emission Color"].default_value=(*color,1)
        elif "Emission" in bs.inputs: bs.inputs["Emission"].default_value=(*color,1)
        bs.inputs["Emission Strength"].default_value=emission
    return m
skin=material("Porcelain white anatomical mannequin",(.78,.84,.9),.12,.24)
dark=material("Matte graphite shorts",(.018,.027,.04),.05,.4)
muscle=material("Activated muscle coral",(.95,.075,.045),.08,.26,.25)
green=material("Secondary activation lime",(.08,.9,.25),.04,.22,.35)
blue=material("Joint indicator electric blue",(.02,.48,.95),.1,.2,.45)
organ=material("Anatomical organ rose",(.62,.12,.2),.05,.3)
organ2=material("Organ highlight",(.95,.34,.27),.04,.26)
foodred=material("Food tomato red",(.72,.035,.025),.02,.22)
foodgreen=material("Food leaf green",(.08,.34,.06),0,.4)
gold=material("Nutrition golden",(.92,.52,.08),.05,.28)
floor=material("Studio charcoal",(.012,.019,.03),.15,.42)
white=material("Typography white",(.88,.94,1),0,.4,0.1)

def uv(name,loc,scale,mat,seg=40):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=24,radius=1,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(mat)
    bpy.ops.object.shade_smooth(); return o

def capsule(name,a,b,r,mat,r2=None):
    a,b=Vector(a),Vector(b); mid=(a+b)/2; length=(b-a).length
    bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=r,radius2=(r if r2 is None else r2),depth=length,location=mid)
    o=bpy.context.object; o.name=name; o.rotation_mode="QUATERNION"; o.rotation_quaternion=(b-a).to_track_quat("Z","Y"); o.data.materials.append(mat)
    bevel=o.modifiers.new("Soft anatomical transitions","BEVEL"); bevel.width=min(r*.45,.09); bevel.segments=4
    o.modifiers.new("Weighted smooth normals","WEIGHTED_NORMAL")
    uv(name+" joint A",a,(r,r,r),mat); uv(name+" joint B",b,(r2 or r,r2 or r,r2 or r),mat)
    return o

def text_obj(body,loc,size,mat):
    cu=bpy.data.curves.new("Scene title","FONT"); cu.body=body[:52]; cu.size=size; cu.align_x="CENTER"; cu.extrude=.002
    ob=bpy.data.objects.new("Scene title",cu); bpy.context.collection.objects.link(ob); ob.location=loc; ob.data.materials.append(mat)
    ob.rotation_euler=(math.radians(90),0,0); return ob

def setup_camera(target,scale):
    bpy.ops.object.camera_add(location=(4.5,-8,4.2)); cam=bpy.context.object; cam.data.type="ORTHO"; cam.data.ortho_scale=scale
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler(); scene.camera=cam
    for loc,power,size in [((1,-4,7),1500,5),((-4,-1,3),950,4),((2,4,6),1800,3)]:
        bpy.ops.object.light_add(type="AREA",location=loc); l=bpy.context.object; l.data.energy=power; l.data.shape="DISK"; l.data.size=size
        l.rotation_euler=(Vector(target)-l.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.06)); bpy.context.object.data.materials.append(floor)

def exercise_scene():
    # 3D side-view athlete with sculpted torso, shoulder caps, arms, thighs, calves and black shorts.
    # The white porcelain body and emissive muscle overlays intentionally follow the supplied CGI reference.
    hip=(-.05,0,1.35); shoulder=(-.95,0,1.55); head=(-1.42,0,1.68)
    torso=uv("Sculpted torso",(-.52,0,1.48),(.72,.34,.29),skin)
    chest=uv("Pectoral muscle overlay",(-.82,-.30,1.58),(.34,.055,.19),muscle)
    abs1=uv("Abdominal wall",(-.30,-.29,1.39),(.28,.045,.19),skin)
    pelvis=uv("Pelvis",(.0,0,1.30),(.34,.31,.25),skin)
    shorts=uv("Graphite training shorts",(.12,0,1.23),(.38,.33,.22),dark)
    hd=uv("Head",head,(.22,.22,.25),skin)
    neck=capsule("Neck",(-1.12,0,1.56),(-1.28,0,1.64),.105,skin)
    # Legs extend behind athlete in plank position.
    thigh= capsule("Near thigh",(.22,-.20,1.28),(1.02,-.20,.98),.19,skin,.14)
    quad=uv("Quadriceps activation",(.61,-.34,1.12),(.34,.055,.13),muscle)
    ham=uv("Hamstring activation",(.64,.20,1.10),(.31,.05,.12),green)
    calf=capsule("Near calf",(1.02,-.20,.98),(1.68,-.20,.34),.125,skin,.085)
    foot=uv("Near foot",(1.78,-.20,.22),(.30,.14,.09),skin)
    capsule("Far thigh",(.22,.19,1.27),(1.02,.19,.98),.18,skin,.14)
    capsule("Far calf",(1.02,.19,.98),(1.68,.19,.34),.12,skin,.08)
    uv("Far foot",(1.78,.19,.22),(.29,.13,.085),skin)
    # Arms support the body; elbow joints and palms rest on studio floor.
    for side,y in [("Near",-.34),("Far",.34)]:
        sh=(-.94,y,1.52); el=(-.64,y,.78); wr=(-.38,y,.12)
        uv(side+" deltoid",sh,(.20,.17,.19),muscle)
        capsule(side+" upper arm",sh,el,.115,skin,.09)
        uv(side+" triceps activation",(-.78,y-.045 if y<0 else y+.045,1.12),(.11,.06,.25),green)
        capsule(side+" forearm",el,wr,.09,skin,.075)
        uv(side+" palm",(-.25,y,.10),(.20,.14,.055),skin)
        for j in range(4):
            uv(side+" finger "+str(j),(-.10+j*.035,y-.08+j*.05,.075),(.11,.025,.025),skin,24)
        for n,p in [("Shoulder",sh),("Elbow",el),("Wrist",wr)]:
            uv(side+" "+n,p,(.055,.055,.055),blue,24)
    # Animate one complete controlled push-up cycle: torso/chest move, limbs stay planted.
    for frame in range(1,FRAMES+1):
        phase=2*math.pi*(frame-1)/FRAMES
        down=.5-.5*math.cos(phase)
        dz=-.22*down
        for o in [torso,chest,abs1,pelvis,shorts,hd,neck,thigh,quad,ham]:
            o.location.z += dz
        # keyframe delta is applied through location so all hero geometry remains genuinely 3D.
        for o in [torso,chest,abs1,pelvis,shorts,hd,neck,thigh,quad,ham]:
            o.keyframe_insert(data_path="location",frame=frame)
    text_obj("TARGET MUSCLES  /  CONTROLLED REP",(.0,-.65,2.15),.12,white)
    setup_camera((.0,0,1.0),4.9 if A.orientation=="portrait" else 4.2)

def digestion_scene():
    # 3D organ set: esophagus, stomach, liver and intestinal loops with moving food bolus.
    uv("Liver",(-.55,0,1.45),(.48,.25,.20),organ2)
    stomach=uv("Stomach",(.02,0,1.12),(.28,.22,.38),organ)
    uv("Stomach highlight",(.08,-.20,1.12),(.13,.035,.25),organ2)
    # curved esophagus and intestinal coils are bevelled 3D curves.
    def tube(name,pts,bevel,mat):
        cu=bpy.data.curves.new(name,"CURVE"); cu.dimensions="3D"; cu.bevel_depth=bevel; cu.bevel_resolution=5
        sp=cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts)-1)
        for bp,co in zip(sp.bezier_points,pts): bp.co=co; bp.handle_left_type="AUTO"; bp.handle_right_type="AUTO"
        ob=bpy.data.objects.new(name,cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat); return ob
    tube("Esophagus",[(-.05,0,1.85),(-.02,0,1.62),(.0,0,1.42)],.065,organ2)
    for row in range(3):
        z=.65-row*.14
        tube("Small intestine coil "+str(row),[( -.30,0,z),(-.12,0,z+.09),(.08,0,z-.03),(.25,0,z+.08),(.34,0,z-.04)],.045,organ2)
    tube("Large intestine",[(-.38,0,.78),(-.42,0,.38),(.36,0,.38),(.40,0,.78)],.085,organ)
    bolus=uv("Moving food bolus",(-.04,-.12,1.78),(.07,.07,.07),gold)
    for f in range(1,FRAMES+1):
        q=(f-1)/(FRAMES-1); bolus.location.z=1.78-.78*q; bolus.keyframe_insert(data_path="location",frame=f)
    text_obj("DIGESTION  /  ABSORPTION",(.0,-.62,2.1),.12,white)
    setup_camera((0,0,1.05),3.8 if A.orientation=="portrait" else 3.4)

def food_scene():
    # Three-dimensional plated meal with distinct produce, protein and carbohydrate forms.
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.86,depth=.10,location=(0,0,.18))
    plate=bpy.context.object; plate.name="Ceramic plate"; plate.data.materials.append(white)
    for i in range(7):
        a=i*math.tau/7
        uv("Roasted vegetable "+str(i),(math.cos(a)*.48,math.sin(a)*.48,.36),(.19,.16,.10),foodgreen if i%2 else foodred)
    for i in range(4):
        uv("Protein portion "+str(i),(-.28+i*.15,-.13,.40),(.14,.12,.075),gold)
    for i in range(5):
        uv("Grain serving "+str(i),(.20+i*.075,.20,.34),(.055,.05,.045),gold,24)
    for f in range(1,FRAMES+1):
        p=(f-1)/(FRAMES-1)
        for i,o in enumerate([x for x in bpy.data.objects if x.name.startswith(("Roasted vegetable","Protein portion","Grain serving"))]):
            if f==1: o.scale*=.01
            o.scale=(.19,.16,.10) if o.name.startswith("Roasted") else ((.14,.12,.075) if o.name.startswith("Protein") else (.055,.05,.045))
            o.keyframe_insert(data_path="scale",frame=f)
    text_obj("WHOLE FOOD  /  NUTRIENT DENSITY",(.0,-.7,1.25),.10,white)
    setup_camera((0,0,.45),3.5 if A.orientation=="portrait" else 3.0)

def cell_scene():
    # Macro cell / mitochondrion scene for metabolism, hormones and recovery topics.
    uv("Translucent cell body",(0,0,1.0),(.72,.42,.58),blue)
    uv("Nucleus",(-.1,-.35,1.0),(.27,.10,.25),organ)
    for i in range(5):
        a=i*math.tau/5
        o=uv("Mitochondrion "+str(i),(.42*math.cos(a),.42*math.sin(a),1+.25*math.sin(a)),(.20,.11,.08),gold)
        o.rotation_euler[1]=a
    for i in range(12):
        a=i*math.tau/12
        particle=uv("Nutrient molecule "+str(i),(1.05*math.cos(a),1.05*math.sin(a),1),(.035,.035,.035),green,20)
        for f in range(1,FRAMES+1):
            phase=(f-1)/FRAMES*math.tau
            particle.location=(1.05*math.cos(a+phase),1.05*math.sin(a+phase),1+.06*math.sin(phase*2))
            particle.keyframe_insert(data_path="location",frame=f)
    text_obj("CELLULAR PROCESS  /  ENERGY",(.0,-.65,1.9),.10,white)
    setup_camera((0,0,1),3.7 if A.orientation=="portrait" else 3.1)

def main():
    kind=A.kind.lower()
    if kind=="exercise_biomechanics" or kind=="muscle_anatomy": exercise_scene()
    elif kind in ("digestion_fiber","digestive_system"): digestion_scene()
    elif kind in ("food_nutrition","protein_synthesis"): food_scene()
    else: cell_scene()
    scene.frame_set(1)
    scene.render.filepath=os.path.abspath(A.output)
    os.makedirs(os.path.dirname(os.path.abspath(A.output)),exist_ok=True)
    bpy.ops.render.render(animation=True)
    print("FITFUEL_3D_RENDER_OK",kind,A.output)

main()
