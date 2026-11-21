"""Build a procedural 3D asset pack and animated Blender preview.
Run: blender -b --python blender_asset_preview.py
"""
import bpy, json, math, os
from asset_pipeline import build_render_manifest
from pathlib import Path
from mathutils import Vector
OUT=Path(os.getenv("FITFUEL_3D_OUT","output/3d_preview")); ASSET_DIR=Path("assets_3d/generated")
FPS=24; FRAMES=96; W,H=720,1280
def mat(name,color,metallic=0,roughness=.42):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 b=m.node_tree.nodes.get("Principled BSDF");b.inputs["Base Color"].default_value=(*color,1);b.inputs["Metallic"].default_value=metallic;b.inputs["Roughness"].default_value=roughness;return m
def cube(name,loc,scale,m,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:
  x=o.modifiers.new("Soft edges","BEVEL");x.width=bevel;x.segments=3;o.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
 return o
def label(body,loc,size,m):
 bpy.ops.object.text_add(location=loc,rotation=(math.radians(90),0,0));o=bpy.context.object;o.name="Label_"+body.replace(" ","_");o.data.body=body;o.data.size=size;o.data.extrude=.002;o.data.materials.append(m);return o
def point(cam,target):cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
def export(objects,path):
 try: bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
 except Exception: pass
 bpy.ops.object.select_all(action="DESELECT")
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.export_scene.gltf(filepath=str(path),export_format="GLB",use_selection=True)
def main():
 OUT.mkdir(parents=True,exist_ok=True);ASSET_DIR.mkdir(parents=True,exist_ok=True)
 bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
 navy=mat("Midnight Navy",(.018,.045,.075),roughness=.65);floor_m=mat("Gym Floor",(.055,.085,.11),roughness=.78)
 steel=mat("Brushed Steel",(.36,.48,.58),.82);rubber=mat("Rubber Grip",(.025,.035,.045),roughness=.8)
 red=mat("Muscle Fiber Red",(.55,.07,.12),roughness=.32);pink=mat("Fiber Highlight",(.92,.25,.29),roughness=.3)
 cyan=mat("FitFuel Cyan",(.08,.72,.82),.25);white=mat("Label White",(.88,.94,.98))
 cube("Gym_Floor",(0,0,-.28),(12,12,.45),floor_m,.12);cube("Gym_Back_Wall",(0,4.8,2.5),(12,.25,5),navy,.1)
 for x in (-4.5,-2.5,2.5,4.5):cube("Wall_Light_Panel",(x,4.62,2.6),(.045,.025,3.2),cyan,.015)
 fibers=[]
 for row in range(3):
  for col in range(5):
   x=(col-2)*.34;z=1.25+(row-1)*.28
   bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.105,depth=2.2,location=(x,0,z),rotation=(0,math.radians(90),0))
   o=bpy.context.object;o.name=f"Muscle_Fiber_{row}_{col}";o.data.materials.append(red if (row+col)%2 else pink)
   b=o.modifiers.new("Rounded ends","BEVEL");b.width=.09;b.segments=4;o.modifiers.new("Weighted normals","WEIGHTED_NORMAL");fibers.append(o)
 root=bpy.data.objects.new("Muscle_Bundle_Animated",None);bpy.context.collection.objects.link(root)
 for o in fibers:o.parent=root
 root.location=(-1.15,0,0)
 for f,s in ((1,1),(24,1),(48,1.08),(72,1),(96,1.04)):
  root.scale=(s,1,1+(s-1)*.5);root.keyframe_insert(data_path="scale",frame=f)
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.18,depth=1.25,location=(1.3,0,.75),rotation=(0,math.radians(90),0))
 grip=bpy.context.object;grip.name="Dumbbell_Grip";grip.data.materials.append(rubber);weights=[grip]
 for x in (.48,2.12):
  bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.48,depth=.28,location=(x,0,.75),rotation=(0,math.radians(90),0))
  p=bpy.context.object;p.name="Dumbbell_Weight";p.data.materials.append(steel);b=p.modifiers.new("Plate bevel","BEVEL");b.width=.045;b.segments=4;p.modifiers.new("Weighted normals","WEIGHTED_NORMAL");weights.append(p)
 label("MUSCLE FIBER MODEL",(-2.4,1.1,3.25),.28,white);label("REUSABLE 3D PROP",(.55,1.1,2.3),.23,cyan)
 export(fibers,ASSET_DIR/"muscle_fiber_bundle_preview.glb");export(weights,ASSET_DIR/"dumbbell_prop.glb")
 bpy.ops.object.camera_add(location=(0,-8.8,3.3));cam=bpy.context.object;cam.name="Preview_Camera";bpy.context.scene.camera=cam;cam.data.lens=48
 for f,a in ((1,-.45),(48,0),(96,.45)):
  cam.location=(9.5*math.sin(a),-8.8*math.cos(a),3.1+.25*math.sin(a*2));point(cam,(0,.3,1.25));cam.keyframe_insert(data_path="location",frame=f);cam.keyframe_insert(data_path="rotation_euler",frame=f)
 for typ,loc,power,size in (("AREA",(-3.5,-4.5,7),1250,6),("AREA",(4,2,5),950,5),("AREA",(0,-1,2.8),320,4)):
  bpy.ops.object.light_add(type=typ,location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape="DISK";l.data.size=size
 scene=bpy.context.scene;try: scene.render.engine="BLENDER_EEVEE_NEXT"
 except Exception: scene.render.engine="BLENDER_EEVEE"
 if hasattr(scene,"eevee"): scene.eevee.taa_render_samples=24
 scene.render.resolution_x=W;scene.render.resolution_y=H;scene.render.resolution_percentage=100;scene.render.fps=FPS;scene.frame_start=1;scene.frame_end=FRAMES;scene.world.color=(.025,.035,.055)
 scene.view_settings.view_transform="Standard";scene.render.image_settings.file_format="FFMPEG";scene.render.ffmpeg.format="MPEG4";scene.render.ffmpeg.codec="H264";scene.render.ffmpeg.constant_rate_factor="MEDIUM";scene.render.ffmpeg.ffmpeg_preset="GOOD";scene.render.filepath=str(OUT/"preview.mp4")
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"preview.blend"));bpy.ops.render.render(animation=True)
 catalog={"catalog_version":1,"assets":[
 {"asset_id":"muscle-fiber-bundle-preview","category":"scientific","file":"generated/muscle_fiber_bundle_preview.glb","source":"procedural-preview","license":"project-generated","review_status":"pending","scientific_accuracy_required":True,"notes":"Stylized teaching schematic; not validated anatomy."},
 {"asset_id":"dumbbell-prop","category":"prop","file":"generated/dumbbell_prop.glb","source":"procedural-preview","license":"project-generated","review_status":"pending","scientific_accuracy_required":False,"notes":"Generic exercise prop; pending visual review."}]}
 Path("assets_3d/catalog.json").write_text(json.dumps(catalog,indent=2)+"\n",encoding="utf-8")
 print("3D preview rendered:",OUT/"preview.mp4")
if __name__=="__main__":main()
