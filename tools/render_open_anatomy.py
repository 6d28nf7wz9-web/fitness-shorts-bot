import bpy, math, os, sys
from mathutils import Vector
from pathlib import Path

model=Path(os.environ["ANATOMY_GLB"])
out=Path(os.environ.get("CGI_OUT","out"))
out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(model))
# Discover the imported anatomical hierarchy and mesh inventory.
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
if not meshes: raise RuntimeError("GLB imported but contains no mesh objects")
systems={}
for o in bpy.context.scene.objects:
    if o.type=="EMPTY":
        systems[o.name]=[x.name for x in o.children if x.type=="MESH"]
(out/"model_inventory.txt").write_text(
    "MESH_COUNT="+str(len(meshes))+"\n"+
    "MESHES="+", ".join(o.name for o in meshes[:220])+"\n"+
    "GROUPS="+repr(systems),encoding="utf-8")
# Show the muscular system only; retain separate named meshes for close-up storytelling.
for o in meshes:
    parent=o.parent.name.lower() if o.parent else ""
    name=o.name.lower()
    o.hide_render=not ("muscle" in parent or "muscle" in name)
visible=[o for o in meshes if not o.hide_render]
if not visible:
    # Fallback: render the full anatomy rather than a blank frame, but report it explicitly.
    for o in meshes: o.hide_render=False
    mode="full anatomy fallback"
else: mode="muscle meshes only"
(out/"render_mode.txt").write_text(mode,encoding="utf-8")
# Build cinematic materials, retaining anatomical mesh shapes.
for obj in meshes:
    if obj.hide_render: continue
    mat=bpy.data.materials.new("FitFuel | anatomical tissue")
    mat.diffuse_color=(0.48,0.075,0.09,1)
    mat.use_nodes=True
    bs=mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(0.34,0.035,0.055,1)
    bs.inputs["Metallic"].default_value=0.12
    bs.inputs["Roughness"].default_value=0.34
    obj.data.materials.clear(); obj.data.materials.append(mat)
# Bounds and camera
deps=bpy.context.evaluated_depsgraph_get()
pts=[]
for obj in meshes:
    if obj.hide_render: continue
    for corner in obj.bound_box: pts.append(obj.matrix_world @ Vector(corner))
if not pts: raise RuntimeError("No renderable anatomical geometry")
mn=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
mx=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
center=(mn+mx)/2
size=mx-mn
bpy.ops.object.camera_add(location=(center.x+size.x*1.9,center.y-size.y*2.8,center.z+size.z*0.15))
cam=bpy.context.object
direction=center-cam.location
cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
cam.data.lens=52
bpy.context.scene.camera=cam
# Dark studio world and three-point lighting
world=bpy.data.worlds.new("FitFuel dark studio")
world.use_nodes=True
world.node_tree.nodes["Background"].inputs[0].default_value=(0.006,0.009,0.018,1)
world.node_tree.nodes["Background"].inputs[1].default_value=0.35
bpy.context.scene.world=world
def area(name,loc,power,color,size):
    bpy.ops.object.light_add(type="AREA",location=loc)
    l=bpy.context.object; l.name=name; l.data.energy=power; l.data.color=color; l.data.shape="DISK"; l.data.size=size
    l.rotation_euler=(center-l.location).to_track_quat('-Z','Y').to_euler()
area("Key softbox",(center.x+size.x*1.4,center.y-size.y*1.6,center.z+size.z*1.4),1700,(1.0,0.72,0.66),size.x*1.8)
area("Cool rim",(center.x-size.x*1.5,center.y+size.y*0.8,center.z+size.z*0.7),2100,(0.22,0.48,1.0),size.x*1.6)
area("Top strip",(center.x,center.y,size.z+mx.z+1),1200,(1.0,0.2,0.18),size.x*1.2)
scene=bpy.context.scene
scene.render.engine="CYCLES" if os.environ.get("USE_CYCLES")=="1" else "BLENDER_EEVEE"
scene.render.resolution_x=720; scene.render.resolution_y=1280; scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="AgX"
scene.render.filepath=str(out/"anatomy-muscle-hero.png")
bpy.ops.render.render(write_still=True)
# Short subtle camera move for motion proof; same scene, no fake muscle deformation.
scene.render.image_settings.file_format="FFMPEG"
scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"; scene.render.ffmpeg.constant_rate_factor="MEDIUM"
scene.render.fps=24; scene.frame_start=1; scene.frame_end=72
base=cam.location.copy()
for frame,scale in [(1,1.0),(72,0.93)]:
    cam.location=center+(base-center)*scale
    cam.keyframe_insert(data_path="location",frame=frame)
scene.render.filepath=str(out/"anatomy-muscle-cinematic.mp4")
bpy.ops.render.render(animation=True)
print("CGI_RENDER_OK",len(meshes),len(visible),mode)
