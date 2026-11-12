"""Controlled, anatomically plausible biceps-curl preview for FitFuel.

Preview-only Blender scene. The elbow stays fixed, the forearm rotates through a
controlled curl arc, and the dumbbell is parented to the gripping hand.
Run:
  blender -b -P blender_bicep_curl.py -- --duration 5 --output output/3d_preview/bicep_curl.mp4
"""
import argparse
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument("--duration", type=float, default=5.0)
parser.add_argument("--output", required=True)
parser.add_argument("--exercise", default="bicep curl")
args = parser.parse_args(argv)
if not 1.0 <= args.duration <= 10.0:
    raise SystemExit("--duration must be between 1 and 10 seconds")

FAST = os.getenv("FITFUEL_PREVIEW_FAST", "0") == "1"
WIDTH, HEIGHT = (320, 568) if FAST else (720, 1280)
FPS = 12 if FAST else 30
FRAMES = max(24, round(args.duration * FPS))

# Clean scene and render configuration.
bpy.ops.object.select_all(action="SELECT)
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT" if hasattr(bpy.types, "EEVEE_NEXT") else "BLENDER_EEVEE"
scene.render.resolution_x = WIDTH
scene.render.resolution_y = HEIGHT
scene.render.resolution_percentage = 100
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = FRAMES
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
scene.render.ffmpeg.video_bitrate = 9000
scene.render.image_settings.color_mode = "RGB"
scene.render.filepath = os.path.abspath(args.output)
scene.render.use_file_extension = True
scene.render.film_transparent = False
scene.render.image_settings.color_depth = "8"
scene.render.use_motion_blur = not FAST
scene.render.motion_blur_shutter = 0.25
scene.render.resolution_percentage = 100
scene.render.image_settings.color_mode = "RGB"
scene.view_settings.view_transform = "AgX"
scene.world.color = (0.012, 0.018, 0.03)
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items else "BLENDER_EEVEE"
if hasattr(scene, "eevee") and not FAST:
    scene.eevee.taa_render_samples = 32
if hasattr(scene, "eevee") and FAST:
    scene.eevee.taa_render_samples = 8

def mat(name, color, metallic=0.0, roughness=0.35, emission=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Metallic"].default_value = metallic
    bs.inputs["Roughness"].default_value = roughness
    if emission:
        if "Emission Color" in bs.inputs:
            bs.inputs["Emission Color"].default_value = (*color, 1)
        bs.inputs["Emission Strength"].default_value = emission
    return m

skin = mat("FitFuel warm anatomical skin", (0.64, 0.39, 0.27), 0.05, 0.3)
skin_light = mat("Muscle highlight", (0.82, 0.56, 0.40), 0.03, 0.32)
muscle = mat("Biceps highlighted red", (0.78, 0.055, 0.045), 0.02, 0.28, 0.12)
dark = mat("Training shorts", (0.018, 0.028, 0.045), 0.15, 0.3)
steel = mat("Dumbbell brushed steel", (0.30, 0.38, 0.48), 0.82, 0.22)
rubber = mat("Dumbbell rubber plates", (0.012, 0.018, 0.026), 0.1, 0.3)
white = mat("FitFuel typography", (0.88, 0.94, 1.0), 0.0, 0.4, 0.15)
accent = mat("FitFuel cyan", (0.02, 0.55, 0.95), 0.2, 0.22, 0.35)
floor_mat = mat("Dark studio floor", (0.009, 0.014, 0.024), 0.15, 0.4)

def uv(name, loc, scale, material, segments=40):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=24, radius=1, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    ob.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return ob

def segment(name, radius, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=radius, depth=1, location=(0, 0, 0))
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(material)
    bevel = ob.modifiers.new("Soft rounded edges", "BEVEL")
    bevel.width = radius * 0.35
    bevel.segments = 4
    ob.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return ob

def put_between(ob, a, b, radius_scale=1.0):
    va, vb = Vector(a), Vector(b)
    delta = vb - va
    ob.location = (va + vb) * 0.5
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = delta.to_track_quat("Z", "Y")
    ob.scale.z = delta.length
    ob.keyframe_insert(data_path="location")
    ob.keyframe_insert(data_path="rotation_quaternion")
    ob.keyframe_insert(data_path="scale")

def label(body, location, size, material):
    curve = bpy.data.curves.new(body, "FONT")
    curve.body = body
    curve.size = size
    curve.align_x = "CENTER"
    curve.extrude = 0.001
    ob = bpy.data.objects.new(body, curve)
    bpy.context.collection.objects.link(ob)
    ob.location = location
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.data.materials.append(material)
    return ob

# Upright athletic upper body, kept deliberately simple so the exercise mechanics
# remain the visual focus while the biceps and forearm are clearly readable.
uv("Torso", (0.0, 0.0, 1.55), (0.48, 0.27, 0.72), skin)
uv("Chest", (-0.08, -0.245, 1.83), (0.37, 0.075, 0.23), skin_light)
uv("Abdominal core", (0.05, -0.24, 1.42), (0.25, 0.055, 0.34), skin)
uv("Pelvis", (0.0, 0.0, 0.88), (0.38, 0.25, 0.24), skin)
uv("Shorts", (0.0, 0.0, 0.76), (0.40, 0.27, 0.20), dark)
uv("Head", (0.0, 0.0, 2.43), (0.22, 0.20, 0.27), skin)
uv("Neck", (0.0, 0.0, 2.15), (0.13, 0.13, 0.20), skin)
# Stable legs provide a grounded, upright exercise stance.
for side, x in (("L", -0.20), ("R", 0.20)):
    thigh = segment(side + " thigh", 0.14, skin)
    put_between(thigh, (x, 0, 0.72), (x * 1.08, 0, 0.12))
    uv(side + " shoe", (x * 1.08, -0.08, 0.07), (0.19, 0.27, 0.09), dark)

# Curling arm is on the camera-facing side. Shoulder and elbow centers are fixed.
shoulder = (-0.43, -0.02, 1.96)
elbow = (-0.53, -0.06, 1.22)
upper = segment("Upper arm", 0.115, skin)
put_between(upper, shoulder, elbow)
uv("Shoulder cap", shoulder, (0.19, 0.17, 0.19), skin)
biceps = uv("Biceps brachii highlighted", (-0.49, -0.205, 1.62), (0.105, 0.065, 0.28), muscle)
# Triceps mass on the back of the arm.
uv("Triceps mass", (-0.64, 0.04, 1.60), (0.09, 0.11, 0.27), skin_light)
uv("Fixed elbow joint", elbow, (0.105, 0.105, 0.105), skin)

forearm = segment("Moving forearm", 0.082, skin_light)
wrist_joint = uv("Wrist joint", (0, 0, 0), (0.075, 0.075, 0.075), skin)
palm = uv("Gripping palm", (0, 0, 0), (0.105, 0.085, 0.12), skin)
# A visible closed grip: fingers curl around the horizontal handle, not around a plate.
finger_objects = []
for i in range(4):
    finger_objects.append(uv("Grip finger " + str(i + 1), (0, 0, 0), (0.035, 0.045, 0.075), skin, 24))
thumb = uv("Opposing thumb", (0, 0, 0), (0.04, 0.05, 0.09), skin, 24)

# Dumbbell assembly: handle along the hand's grip axis, collars, and equal round plates.
dumbbell_root = bpy.data.objects.new("Dumbbell held in hand", None)
bpy.context.collection.objects.link(dumbbell_root)
def parent_to_root(ob, local):
    ob.parent = dumbbell_root
    ob.location = local
    return ob
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.027, depth=0.34)
handle = bpy.context.object
handle.name = "Dumbbell grip handle"
handle.rotation_euler[1] = math.radians(90)
handle.data.materials.append(steel)
parent_to_root(handle, (0, 0, 0))
for side in (-1, 1):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.145, depth=0.085)
    plate = bpy.context.object
    plate.name = "Rubber dumbbell plate"
    plate.rotation_euler[1] = math.radians(90)
    plate.data.materials.append(rubber)
    bevel = plate.modifiers.new("Plate rim bevel", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 3
    parent_to_root(plate, (side * 0.245, 0, 0))
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.055, depth=0.025)
    collar = bpy.context.object
    collar.name = "Steel dumbbell collar"
    collar.rotation_euler[1] = math.radians(90)
    collar.data.materials.append(steel)
    parent_to_root(collar, (side * 0.185, 0, 0))
# Parent grip pieces to the same wrist root so the hand and weight travel together.
for ob in [palm, wrist_joint, thumb] + finger_objects:
    ob.parent = dumbbell_root
    ob.location = (0, 0, 0)

# Camera-facing side of the dumbbell and palm is y=-0.18.
dumbbell_root.location = (-0.53, -0.18, 0.60)
dumbbell_root.keyframe_insert(data_path="location", frame=1)

# Animate one smooth repetition: 0 degrees (arm extended) -> 125 degrees -> 0.
# Forearm endpoint is calculated around a stationary elbow pivot.
forearm_len = 0.59
for frame in range(1, FRAMES + 1):
    phase = (frame - 1) / max(1, FRAMES - 1)
    angle_deg = 125.0 * (0.5 - 0.5 * math.cos(2 * math.pi * phase))
    angle = math.radians(angle_deg)
    wrist = (
        elbow[0] - forearm_len * math.sin(angle),
        elbow[1],
        elbow[2] - forearm_len * math.cos(angle),
    )
    put_between(forearm, elbow, wrist)
    wrist_joint.location = wrist
    wrist_joint.keyframe_insert(data_path="location", frame=frame)
    # The hand stays aligned with the forearm; dumbbell axis remains horizontal.
    palm.location = (wrist[0] - 0.015, wrist[1] - 0.015, wrist[2] - 0.01)
    palm.keyframe_insert(data_path="location", frame=frame)
    dumbbell_root.location = (wrist[0], wrist[1] - 0.18, wrist[2] - 0.02)
    dumbbell_root.keyframe_insert(data_path="location", frame=frame)
    for i, finger in enumerate(finger_objects):
        finger.location = (wrist[0] + 0.035 * (i - 1.5), wrist[1] - 0.10, wrist[2] - 0.015)
        finger.keyframe_insert(data_path="location", frame=frame)
    thumb.location = (wrist[0] - 0.02, wrist[1] - 0.11, wrist[2] + 0.055)
    thumb.keyframe_insert(data_path="location", frame=frame)

# Use linear timing between densely sampled points; motion is already eased analytically.
for ob in bpy.data.objects:
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for key in fc.keyframe_points:
                key.interpolation = "LINEAR"

label("BICEPS CURL  /  CONTROLLED REP", (0.0, -0.48, 2.92), 0.105, white)
label("ELBOW STAYS FIXED", (0.0, -0.48, 2.76), 0.065, accent)

# Dark studio, camera, and three-point lighting.
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.035))
bpy.context.object.data.materials.append(floor_mat)
bpy.ops.object.camera_add(location=(0.0, -8.5, 1.70))
camera = bpy.context.object
camera.data.type = "ORTHO"
camera.data.ortho_scale = 3.55
camera.rotation_euler = (Vector((0, 0, 1.52)) - camera.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = camera
for location, power, size in [
    ((-3.5, -4.0, 5.0), 1150, 4.0),
    ((3.0, -2.0, 2.8), 800, 3.0),
    ((0.5, 3.0, 4.5), 1400, 3.0),
]:
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = power
    light.data.shape = "DISK"
    light.data.size = size
    light.rotation_euler = (Vector((0, 0, 1.45)) - light.location).to_track_quat("-Z", "Y").to_euler()

# Camera-safe framing, render, and basic output validation.
scene.frame_set(1)
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.render.render(animation=True)
print("FITFUEL_BICEPS_CURL_RENDER_OK", args.output, FRAMES, FPS)
