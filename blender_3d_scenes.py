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

A=args()
FAST_PREVIEW=os.getenv("FITFUEL_PREVIEW_FAST","0")=="1"
W,H=((480,854) if A.orientation=="portrait" else (854,480)) if FAST_PREVIEW else ((1080,1920) if A.orientation=="portrait" else (1920,1080))
FPS=12 if FAST_PREVIEW else 30
SAMPLES=4 if FAST_PREVIEW else 32
FRAMES=max(8,int(math.ceil(A.duration*FPS)))
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.eevee.use_gtao=not FAST_PREVIEW
scene.eevee.gtao_distance=2; scene.eevee.gtao_factor=1.15
scene.render.resolution_x=W; scene.render.resolution_y=H; scene.render.resolution_percentage=100
scene.eevee.taa_render_samples=SAMPLES
scene.render.image_settings.color_mode="RGB"
scene.render.image_settings.color_depth="8"
scene.render.ffmpeg.audio_codec="AAC"
scene.render.ffmpeg.video_bitrate=12000
scene.render.ffmpeg.gopsize=30
scene.render.fps=FPS; scene.frame_start=1; scene.frame_end=FRAMES
scene.render.image_settings.file_format="FFMPEG"; scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"; scene.render.ffmpeg.constant_rate_factor="MEDIUM"
scene.render.filepath=os.path.abspath(A.output); scene.render.use_file_extension=True
scene.render.image_settings.color_mode="RGB"
scene.world.color=(0.012,0.018,0.03)
scene.view_settings.look="AgX - Medium High Contrast"
scene.render.use_motion_blur=True
scene.render.motion_blur_shutter=0.35
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
    # Reference-style biomechanics overlays: green neutral alignment, red deviation,
    # and a cyan shoulder-to-wrist guide. These are luminous 3D curves, not flat stickers.
    def guide(name, points, mat, width=.012):
        cu=bpy.data.curves.new(name,"CURVE"); cu.dimensions="3D"; cu.bevel_depth=width; cu.bevel_resolution=4
        sp=cu.splines.new("POLY"); sp.points.add(len(points)-1)
        for bp,co in zip(sp.points,points): bp.co=(*co,1)
        ob=bpy.data.objects.new(name,cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat)
        return ob
    # Neutral plank reference through shoulder, hip and ankle; red curved spine cue.
    guide("GREEN neutral alignment", [(-.96,-.48,1.52),(-.05,-.48,1.30),(1.66,-.48,.34)], green, .014)
    guide("RED lumbar deviation cue", [(-.96,-.50,1.52),(-.55,-.50,1.28),(-.05,-.50,1.42),(.48,-.50,1.12),(1.66,-.50,.34)], muscle, .010)
    guide("CYAN vertical wrist shoulder guide", [(-.94,-.58,1.52),(-.38,-.58,.12)], blue, .009)
    # Small elbow-angle rays and a subtle angle arc around the near elbow.
    guide("Elbow angle upper ray", [(-.94,-.60,1.52),(-.64,-.60,.78)], blue, .008)
    guide("Elbow angle lower ray", [(-.64,-.60,.78),(-.38,-.60,.12)], blue, .008)
    for j in range(7):
        a=math.radians(205+j*22)
        uv("Elbow angle marker",(-.64+.12*math.cos(a),-.62,.78+.12*math.sin(a)),(.012,.012,.012),blue,12)
    # Animate one complete controlled push-up cycle: torso/chest move, limbs stay planted.
    animated=[torso,chest,abs1,pelvis,shorts,hd,neck,thigh,quad,ham]
    rest={o.name:o.location.copy() for o in animated}
    for frame in range(1,FRAMES+1):
        phase=2*math.pi*(frame-1)/FRAMES
        down=.5-.5*math.cos(phase)
        dz=-.22*down
        for o in animated:
            base=rest[o.name]
            o.location=(base.x,base.y,base.z+dz)
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
    # A clear 3D protein-food plate: grilled chicken, tofu cubes, eggs and vegetables.
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.86,depth=.10,location=(0,0,.18))
    plate=bpy.context.object; plate.name="Ceramic plate"; plate.data.materials.append(white)

    chicken_mat=material("Grilled chicken breast",(.58,.25,.075),.02,.30)
    tofu_mat=material("Fresh tofu",(.88,.78,.57),0,.42)
    egg_white=material("Egg white",(.96,.94,.84),0,.24)
    yolk=material("Egg yolk",(.98,.57,.045),0,.28)
    broccoli=material("Broccoli green",(.055,.28,.055),0,.48)
    rice=material("Cooked rice",(.91,.88,.77),0,.55)

    # Grilled chicken breast, shaped as a plump fillet with visible sear marks.
    breast=uv("Grilled chicken breast",(-.34,-.02,.39),(.39,.22,.105),chicken_mat)
    breast.rotation_euler[2]=-.18
    for i in range(4):
        x=-.55+i*.13
        capsule("Chicken sear mark",(x,-.19,.475),(x+.07,-.16,.48),.009,dark,.009)

    # Distinct tofu cubes on the right side of the plate.
    for i,(x,y) in enumerate([(.30,-.02),(.49,.12),(.28,.22),(.48,-.13)]):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,.39))
        cube=bpy.context.object; cube.name="Tofu cube "+str(i+1); cube.scale=(.15,.14,.13)
        cube.data.materials.append(tofu_mat)
        bevel=cube.modifiers.new("Soft tofu edges","BEVEL"); bevel.width=.035; bevel.segments=4
        cube.modifiers.new("Tofu weighted normals","WEIGHTED_NORMAL")

    # Two clearly recognizable boiled egg halves with yellow yolks.
    for i,x in enumerate([-.12,.10]):
        uv("Boiled egg white "+str(i+1),(x,-.43,.36),(.17,.13,.075),egg_white)
        uv("Boiled egg yolk "+str(i+1),(x,-.45,.425),(.075,.075,.025),yolk)

    # Green vegetables and a small grain portion complete the balanced plate.
    for i in range(5):
        a=i*math.tau/5
        uv("Broccoli floret "+str(i),(.02+.58*math.cos(a),.30+.30*math.sin(a),.36),(.09,.085,.075),broccoli,24)
    for i in range(9):
        x=.05+(i%3)*.065; y=.52+(i//3)*.045
        uv("Rice grain "+str(i),(x,y,.34),(.035,.022,.018),rice,16)

    text_obj("PROTEIN FOODS  /  CHICKEN  /  TOFU  /  EGGS",(.0,-.68,1.28),.075,white)
    setup_camera((0,0,.48),3.5 if A.orientation=="portrait" else 3.0)


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


def muscle_scene():
    # Layered muscle-fiber cutaway: fascicles, striations and activation pulses.
    base=uv("Muscle belly",(0,0,1.0),(0.82,.34,.42),organ)
    for i in range(9):
        x=-.62+i*.155
        fiber=uv("Longitudinal muscle fascicle "+str(i),(x,-.30,1.0),(.075,.055,.31),muscle if i%3 else green,32)
        fiber.rotation_euler[1]=-.22
        for j in range(5):
            z=.76+j*.12
            uv("Fiber striation",(x,-.365,z),(.052,.012,.009),gold,16)
    # Animated activation wave travels through the bundle.
    for i in range(12):
        p=uv("Activation signal "+str(i),(-.72+i*.13,-.40,.62),(.025,.018,.025),blue,16)
        for fr in range(1,FRAMES+1):
            q=(fr-1)/max(1,FRAMES-1)
            p.location.x=-.72+((i*.13+q*1.5)%1.44)
            p.keyframe_insert(data_path="location",frame=fr)
    text_obj("MUSCLE ANATOMY  /  ACTIVATION",(.0,-.58,1.75),.105,white)
    setup_camera((0,0,1),3.7 if A.orientation=="portrait" else 3.2)

def protein_scene():
    # Amino-acid chain assembly beside a muscle cell.
    uv("Muscle cell",(0,0,1),(.72,.34,.56),blue)
    uv("Cell nucleus",(-.12,-.34,1),(.25,.07,.22),organ)
    chain=[]
    for i in range(11):
        a=i*.56
        p=(.78*math.cos(a),-.38,1+.42*math.sin(a))
        chain.append(p); uv("Amino acid "+str(i),p,(.075,.065,.075),[gold,green,muscle][i%3],24)
    for a,b in zip(chain,chain[1:]):
        capsule("Peptide bond",a,b,.025,white,.025)
    text_obj("AMINO ACIDS  /  PROTEIN SYNTHESIS",(.0,-.58,1.85),.09,white)
    setup_camera((0,0,1),3.8 if A.orientation=="portrait" else 3.2)

def energy_scene():
    # Mitochondrion and animated ATP energy particles.
    uv("Mitochondrion outer membrane",(0,0,1),(.88,.38,.43),gold)
    uv("Mitochondrion inner matrix",(0,-.30,1),(.72,.10,.30),organ)
    for i in range(7):
        x=-.55+i*.18
        capsule("Cristae membrane",(x,-.405,.82),(x+.10,-.405,1.18),.025,white,.025)
    for i in range(16):
        a=i*math.tau/16
        p=uv("ATP particle "+str(i),(1.12*math.cos(a),-.05,1+0.72*math.sin(a)),(.045,.045,.045),green,16)
        for fr in range(1,FRAMES+1):
            q=(fr-1)/FRAMES*math.tau
            p.location=(1.12*math.cos(a+q),-.05,1+.72*math.sin(a+q))
            p.keyframe_insert(data_path="location",frame=fr)
    text_obj("CELLULAR ENERGY  /  ATP",(.0,-.58,1.78),.11,white)
    setup_camera((0,0,1),3.9 if A.orientation=="portrait" else 3.2)

def hydration_scene():
    # Water molecules crossing a muscle-cell membrane.
    uv("Muscle cell membrane",(0,0,1),(.78,.32,.55),blue)
    uv("Cell interior",(0,-.29,1),(.63,.08,.40),skin)
    for i in range(15):
        x=-1.2+(i%5)*.12; z=.55+(i//5)*.42
        p=uv("Water molecule "+str(i),(x,-.1,z),(.045,.045,.045),blue,20)
        for fr in range(1,FRAMES+1):
            q=(fr-1)/max(1,FRAMES-1)
            p.location=(x+q*.8,-.12,z+.04*math.sin(q*math.tau+i))
            p.keyframe_insert(data_path="location",frame=fr)
    text_obj("HYDRATION  /  FLUID BALANCE",(.0,-.58,1.82),.105,white)
    setup_camera((0,0,1),3.9 if A.orientation=="portrait" else 3.2)

def recovery_scene():
    # Sleep/recovery concept: moonlit rest scene and repairing muscle fibers.
    uv("Repairing muscle tissue",(0,0,.9),(.85,.30,.35),organ)
    for i in range(8):
        x=-.62+i*.17
        capsule("Repair fiber",(x,-.32,.72),(x+.08,-.32,1.08),.035,green,.035)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=.34,location=(-.65,.05,1.65))
    moon=bpy.context.object; moon.name="Sleep moon"; moon.data.materials.append(gold)
    uv("Moon shadow",(-.49,-.27,1.72),(.30,.08,.32),floor)
    for i in range(12):
        a=i*math.tau/12
        uv("Recovery signal",(1.0*math.cos(a),-.1,1+.7*math.sin(a)),(.025,.025,.025),blue,16)
    text_obj("SLEEP  /  RECOVERY  /  ADAPTATION",(.0,-.58,2.0),.085,white)
    setup_camera((0,0,1),4.0 if A.orientation=="portrait" else 3.3)

def process_scene():
    # A 3-stage scientific pathway connected by a moving signal.
    nodes=[(-.85,1.0),(0,1.0),(.85,1.0)]
    for i,(x,z) in enumerate(nodes):
        uv(["Trigger node","Process node","Outcome node"][i],(x,0,z),(.25,.22,.25),[gold,blue,green][i])
        text_obj(["TRIGGER","PROCESS","RESULT"][i],(x,-.36,z-.48),.10,white)
    for i in range(2):
        capsule("Causal pathway", (nodes[i][0]+.27,-.05,1),(nodes[i+1][0]-.27,-.05,1),.035,white,.035)
    signal=uv("Moving causal signal",(-.58,-.28,1),(.07,.07,.07),muscle)
    for fr in range(1,FRAMES+1):
        q=(fr-1)/max(1,FRAMES-1)
        signal.location=(-.58+q*1.16,-.28,1+.08*math.sin(q*math.tau))
        signal.keyframe_insert(data_path="location",frame=fr)
    text_obj("HOW THE BODY WORKS",(.0,-.58,1.85),.12,white)
    setup_camera((0,0,1),4.0 if A.orientation=="portrait" else 3.2)

def main():
    kind=A.kind.lower()
    if kind=="exercise_biomechanics": exercise_scene()
    elif kind=="muscle_anatomy": muscle_scene()
    elif kind in ("digestion_fiber","digestive_system"): digestion_scene()
    elif kind=="food_nutrition": food_scene()
    elif kind=="protein_synthesis": protein_scene()
    elif kind=="energy_metabolism": energy_scene()
    elif kind=="hydration": hydration_scene()
    elif kind=="recovery_sleep": recovery_scene()
    else: process_scene()
    scene.frame_set(1)
    scene.render.filepath=os.path.abspath(A.output)
    os.makedirs(os.path.dirname(os.path.abspath(A.output)),exist_ok=True)
    bpy.ops.render.render(animation=True)
    print("FITFUEL_3D_RENDER_OK",kind,A.output)

main()
