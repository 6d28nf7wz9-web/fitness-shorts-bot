"""Render a proof-of-concept 3D exercise mannequin (Blender background mode).
This is a prototype visual asset generator, not a medical-grade anatomy model.
Run: blender -b -P blender_3d_prototype.py
"""
import bpy, math, os
from mathutils import Vector

# Reset scene
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    pass
scene=bpy.context.scene
# Ubuntu apt provides Blender 4.0.x; its Eevee engine identifier is BLENDER_EEVEE.
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=int(os.getenv('ANIM_W','720')); scene.render.resolution_y=int(os.getenv('ANIM_H','1280'))
scene.render.resolution_percentage=100
scene.render.fps=24; scene.frame_start=1; scene.frame_end=96
scene.render.image_settings.file_format='PNG'
scene.world.color=(0.018,0.025,0.04)
try:
    scene.view_settings.view_transform='AgX'
except Exception:
    scene.view_settings.view_transform='Standard'

def mat(name,color,metal=0,rough=.35,emission=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    if emission: p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emission
    return m
skin=mat('Pearl anatomical mannequin',(0.72,.79,.86),.18,.28)
joint=mat('Joint graphite',(.08,.13,.2),.25,.3)
active=mat('Activated muscle orange',(1,.18,.035),.05,.25,.45)
cyan=mat('FitFuel cyan',(.02,.65,.9),.1,.25,.25)
floor_mat=mat('Studio floor',(.015,.025,.045),.1,.45)

def uv(name,loc,scale,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=loc); o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(material
); bpy.ops.object.shade_smooth(); return o
def bone(name,a,b,r,material):
    mid=(Vector(a)+Vector(b))/2; length=(Vector(b)-Vector(a)).length
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=length,location=mid); o=bpy.context.object; o.name=name; o.data.materials.append(material)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=(Vector(b)-Vector(a)).to_track_quat('Z','Y'); bpy.ops.object.shade_smooth(); return o

# Side-facing standing anatomical mannequin; major limbs are articulated segments.
# Animated torso/head and shoulder/hip pivots make a readable push-up cycle.
hip=uv('Pelvis',(0,0,2.25),(.42,.27,.32),skin)
torso=uv('Torso',(0,0,2.85),(.42,.28,.62),skin)
chest=uv('Pectoral highlight',(0,-.245,3.12),(.32,.075,.23),active)
head=uv('Head',(0,0,3.72),(.24,.22,.28),skin)
neck=bone('Neck',(0,0,3.42),(0,0,3.55),.12,joint)
# Arms, forearms, legs; visible side-profile
upperarm=bone('Upper arm',(0,-.25,3.15),(0,-.48,2.72),.13,skin)
triceps=uv('Triceps activation',(0,-.34,2.92),(.14,.12,.22),active)
forearm=bone('Forearm',(0,-.48,2.72),(0,-.48,2.28),.105,skin)
thigh=bone('Thigh',(0,.05,2.18),(0,.05,1.25),.19,skin)
quad=uv('Quadriceps activation',(0,-.14,1.72),(.17,.12,.34),active)
shin=bone('Shin',(0,.05,1.25),(0,-.12,.35),.12,skin)
foot=uv('Foot',(0,-.32,.22),(.18,.38,.1),skin)
# cyan joint markers
for n,p in [('Shoulder',(0,-.25,3.15)),('Elbow',(0,-.48,2.72)),('Hip',(0,.05,2.18)),('Knee',(0,.05,1.25))]: uv(n,p,(.075,.075,.075),cyan)

# Ground plane
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0)); bpy.context.object.data.materials.append(floor_mat)
# Camera and lighting
bpy.ops.object.camera_add(location=(6,-10,3.2)); cam=bpy.context.object; cam.data.type='ORTHO'; cam.data.ortho_scale=5.2
cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler(); scene.camera=cam
for loc,power,size in [((2,-4,6),900,5),((-4,-2,3),650,4),((1,3,5),1100,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.data.energy=power; l.data.shape='DISK'; l.data.size=size; l.rotation_euler=(Vector((0,0,2))-l.location).to_track_quat('-Z','Y').to_euler()
# Motion: smooth torso/head/chest bob and limb pulse. Keyframes are deliberately simple for prototype.
for frame,z in [(1,0),(24,-.22),(48,0),(72,-.22),(96,0)]:
    for o in (torso,chest,head,neck):
        o.location.z += z; o.keyframe_insert(data_path='location',frame=frame)
for frame,angle in [(1,0),(24,-.22),(48,0),(72,-.22),(96,0)]:
    upperarm.rotation_euler[1]=angle; upperarm.keyframe_insert(data_path='rotation_euler',frame=frame)
scene.frame_set(1)
scene.render.image_settings.file_format='FFMPEG'
scene.render.ffmpeg.format='MPEG4'; scene.render.ffmpeg.codec='H264'; scene.render.ffmpeg.constant_rate_factor='MEDIUM'
scene.render.filepath=os.getenv('ANIM_OUTPUT','output/3d_prototype.mp4')
os.makedirs(os.path.dirname(scene.render.filepath),exist_ok=True)
bpy.ops.render.render(animation=True)
print('3D prototype rendered:',scene.render.filepath)
