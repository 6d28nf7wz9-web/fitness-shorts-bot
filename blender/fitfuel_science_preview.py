"""Portrait-first, reusable FitFuel scientific animation preview.

Safe standalone renderer: renders PNG frames only. The workflow encodes and validates
the MP4. No YouTube upload is performed by this script.
"""
import argparse
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def arguments():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output/blender-frames")
    parser.add_argument("--frames", type=int, default=96)
    parser.add_argument("--width", type=int, default=720)
    parser.add_argument("--height", type=int, default=1280)
    parser.add_argument("--title", default="HOW MUSCLE FIBERS CONTRACT")
    parser.add_argument("--subtitle", default="A closer look inside skeletal muscle")
    return parser.parse_args(argv)


def make_material(name, color, metallic=0.1, roughness=0.32, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        socket = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        strength = bsdf.inputs.get("Emission Strength")
        if socket:
            socket.default_value = (*color, 1.0)
        if strength:
            strength.default_value = emission
    return mat


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_text(name, body, location, size, mat, camera):
    curve = bpy.data.curves.new(name, "FONT")
    curve.body = body
    curve.size = size
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.extrude = 0.001
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = camera.rotation_euler
    obj.data.materials.append(mat)
    return obj


def add_bar(name, location, scale, mat, bevel=0.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Soft rounded edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def add_fiber(name, x, y, material, parent, frames):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 24
    curve.bevel_depth = 0.19
    curve.bevel_resolution = 5
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(4)
    for i, point in enumerate(spline.bezier_points):
        z = -2.55 + i * 1.275
        point.co = (x + math.sin(i * math.pi / 2) * 0.045, y, z)
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(material)
    # Small cyclic pulse keeps the movement continuous at the loop boundary.
    for frame, factor in ((1, 1.0), (frames // 4, 1.08), (frames // 2, 1.0),
                           (3 * frames // 4, 1.08), (frames, 1.0)):
        obj.scale = (factor, 1.0, 1.0)
        obj.keyframe_insert(data_path="scale", frame=frame)
    return obj


def build_scene(args):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 8
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = args.frames
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.compression = 20

    world = bpy.data.worlds.new("FitFuel deep navy") if not bpy.data.worlds else bpy.data.worlds[0]
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.003, 0.012, 0.026, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.42

    teal = make_material("Fiber | teal", (0.025, 0.52, 0.48), 0.28, 0.25, 0.16)
    mint = make_material("Bands | mint", (0.30, 0.95, 0.74), 0.08, 0.24, 0.8)
    blue = make_material("Fiber | blue", (0.035, 0.19, 0.34), 0.25, 0.28, 0.12)
    white = make_material("Type | white", (0.82, 0.94, 1.0), 0.0, 0.4, 1.2)
    muted = make_material("Type | muted", (0.30, 0.60, 0.70), 0.0, 0.4, 0.8)
    signal = make_material("Signal | cyan", (0.12, 0.65, 1.0), 0.1, 0.2, 1.8)

    bpy.ops.object.camera_add(location=(0, -18, 0))
    camera = bpy.context.object
    camera.name = "Portrait science camera"
    aim(camera, (0, 0, 0))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 10.8
    scene.camera = camera

    # A centered, vertical bundle is designed for the 9:16 frame, not a landscape crop.
    rig = bpy.data.objects.new("Muscle fiber bundle rig", None)
    bpy.context.collection.objects.link(rig)
    fiber_x = (-1.25, -0.62, 0.0, 0.62, 1.25)
    for index, x in enumerate(fiber_x):
        add_fiber(f"Muscle fiber {index + 1}", x, 0.0, teal if index % 2 == 0 else blue, rig, args.frames)

    # Repeating transverse bands communicate the sarcomere striation pattern.
    for row, z in enumerate((-2.05, -1.35, -0.65, 0.05, 0.75, 1.45, 2.15)):
        for col, x in enumerate(fiber_x):
            band = add_bar(f"Striation {row + 1}-{col + 1}", (x, -0.22, z),
                           (0.39, 0.11, 0.075), mint if row % 2 == 0 else signal, 0.025)
            band.parent = rig
            band.keyframe_insert(data_path="location", frame=1)
            band.location.z = z + 0.10
            band.keyframe_insert(data_path="location", frame=args.frames // 2)
            band.location.z = z
            band.keyframe_insert(data_path="location", frame=args.frames)

    # A traveling activation pulse moves through the bundle.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.16, location=(0, -0.48, -2.35))
    pulse = bpy.context.object
    pulse.name = "Traveling activation signal"
    pulse.data.materials.append(signal)
    for frame, z in ((1, -2.35), (args.frames // 2, 2.35), (args.frames, -2.35)):
        pulse.location.z = z
        pulse.keyframe_insert(data_path="location", frame=frame)

    # Labels, hierarchy and generous safe margins make the graphic legible on a phone.
    add_text("Brand label", "FITFUEL  /  SCIENCE", (0, -0.8, 4.65), 0.22, muted, camera)
    title = add_text("Main title", args.title, (0, -0.8, 4.05), 0.34, white, camera)
    title.data.space_character = 1.05
    add_text("Subtitle", args.subtitle, (0, -0.8, 3.55), 0.19, muted, camera)

    # Explanatory callouts are placed beside the anatomy without covering it.
    add_bar("Callout rule left", (-2.05, -0.35, 1.55), (0.62, 0.06, 0.035), mint, 0.015)
    add_text("Callout label left", "MUSCLE FIBERS", (-1.95, -0.82, 1.25), 0.16, white, camera)
    add_bar("Callout rule right", (2.05, -0.35, -1.45), (0.62, 0.06, 0.035), signal, 0.015)
    add_text("Callout label right", "ACTIVATION SIGNAL", (1.82, -0.82, -1.76), 0.14, white, camera)

    add_bar("Bottom accent", (0, -0.4, -3.55), (2.8, 0.08, 0.035), mint, 0.015)
    add_text("Footer", "CONTRACT  •  RELEASE  •  REPEAT", (0, -0.8, -4.05), 0.19, white, camera)
    add_text("Scientific note", "Illustrative anatomy — simplified for education", (0, -0.8, -4.48), 0.12, muted, camera)

    # Soft studio lighting; no detached floor strip or horizon line.
    for name, location, energy, size, color in (
        ("Key softbox", (-4, -7, 5), 1050, 6.0, (0.42, 1.0, 0.86)),
        ("Blue rim", (4, 1, 2), 1250, 5.0, (0.16, 0.40, 1.0)),
        ("Lower fill", (0, -5, -5), 500, 4.0, (0.12, 0.68, 0.62)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        aim(light, (0, 0, 0))

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output_dir / "frame_")
    scene.frame_set(1)
    return scene


def main():
    args = arguments()
    if args.width < 270 or args.height < 480 or args.frames < 24:
        raise SystemExit("Preview must be at least 270x480 and 24 frames.")
    if args.width / args.height > 0.75:
        raise SystemExit("Science preview must be portrait (width/height <= 0.75).")
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = build_scene(args)
    bpy.ops.render.render(animation=True)
    first_frame = output_dir / "frame_0001.png"
    last_frame = output_dir / f"frame_{scene.frame_end:04d}.png"
    if not first_frame.is_file() or not last_frame.is_file():
        raise SystemExit(f"Missing expected PNG frames in {output_dir}")
    print(f"FITFUEL_BLENDER_FRAMES={output_dir} frames={scene.frame_end}")


if __name__ == "__main__":
    main()
