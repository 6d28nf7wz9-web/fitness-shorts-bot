"""Generate a standalone FitFuel 3D muscle-fiber animation preview with Blender.

This is an opt-in prototype asset generator. It does not change the daily renderer
or upload path. Run:
  blender -b --factory-startup --python blender/fitfuel_science_preview.py -- \
    --output output/blender-science-preview.mp4 --frames 72 --width 540 --height 960
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
    parser.add_argument("--frames", type=int, default=72)
    parser.add_argument("--width", type=int, default=540)
    parser.add_argument("--height", type=int, default=960)
    return parser.parse_args(argv)


def material(name, color, metallic=0.15, roughness=0.3, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        emission_socket = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        strength_socket = bsdf.inputs.get("Emission Strength")
        if emission_socket:
            emission_socket.default_value = (*color, 1.0)
        if strength_socket:
            strength_socket.default_value = emission
    return mat


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_fiber(name, z, y, mat, parent):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 24
    curve.bevel_depth = 0.19
    curve.bevel_resolution = 5
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(4)
    for i, point in enumerate(spline.bezier_points):
        x = -3.45 + i * 1.725
        point.co = (x, y, z + math.sin(i * math.pi / 2) * 0.16)
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    return obj


def add_ring(name, x, z, y, mat, parent, scale=1.0):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=32, minor_segments=8, location=(x, y, z),
        major_radius=0.22 * scale, minor_radius=0.035 * scale,
        rotation=(0, math.pi / 2, 0),
    )
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.data.materials.append(mat)
    return obj


def add_particle(name, z, y, mat, parent, start, end, frames):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=0.105, location=(start, y, z))
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.data.materials.append(mat)
    obj.keyframe_insert(data_path="location", frame=1)
    obj.location.x = end
    obj.keyframe_insert(data_path="location", frame=frames)
    return obj


def build_scene(args):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 16
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = max(24, args.frames)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"

    world = bpy.data.worlds.new("FitFuel Midnight") if not bpy.data.worlds else bpy.data.worlds[0]
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.012, 0.026, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.28

    teal = material("FitFuel | living teal", (0.035, 0.72, 0.62), metallic=0.32, roughness=0.25, emission=0.22)
    mint = material("FitFuel | signal mint", (0.38, 1.0, 0.78), metallic=0.12, roughness=0.22, emission=1.6)
    blue = material("FitFuel | deep muscle blue", (0.055, 0.22, 0.42), metallic=0.38, roughness=0.28, emission=0.12)
    nucleus = material("FitFuel | nucleus", (0.22, 0.62, 1.0), metallic=0.18, roughness=0.2, emission=1.0)

    rig = bpy.data.objects.new("Muscle fiber contraction rig", None)
    bpy.context.collection.objects.link(rig)
    for idx, (z, y) in enumerate(((1.0, 0.0), (0.35, 0.08), (-0.35, -0.08), (-1.0, 0.0))):
        fiber_mat = teal if idx % 2 == 0 else blue
        add_fiber(f"Muscle fiber {idx + 1}", z, y, fiber_mat, rig)
        for ring_idx, x in enumerate((-2.65, -1.75, -0.85, 0.05, 0.95, 1.85, 2.75)):
            add_ring(f"Striation {idx + 1}-{ring_idx + 1}", x, z, y - 0.205, mint if ring_idx % 2 == 0 else blue, rig, 0.72 if idx % 2 else 1.0)
        add_particle(f"Signal particle {idx + 1}", z + 0.02, y - 0.28, nucleus, rig, -3.1, 3.1, scene.frame_end)

    # Gentle contraction / release loop; no abrupt first or last frame.
    rig.scale = (0.92, 1.0, 1.0)
    rig.keyframe_insert(data_path="scale", frame=1)
    rig.scale = (1.0, 1.0, 1.0)
    rig.keyframe_insert(data_path="scale", frame=scene.frame_end // 2)
    rig.scale = (0.92, 1.0, 1.0)
    rig.keyframe_insert(data_path="scale", frame=scene.frame_end)

    # Camera and soft studio lighting.
    bpy.ops.object.camera_add(location=(0, -15, 0.1))
    camera = bpy.context.object
    camera.name = "FitFuel science camera"
    aim(camera, (0, 0, 0))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 9.6
    scene.camera = camera
    camera.data.lens = 52

    for name, location, energy, size, color in (
        ("Key softbox", (-4, -7, 5), 1150, 6.0, (0.48, 1.0, 0.88)),
        ("Blue rim", (4, 1, 2), 1500, 5.0, (0.18, 0.42, 1.0)),
        ("Lower fill", (0, -5, -5), 650, 4.0, (0.12, 0.72, 0.62)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        aim(light, (0, 0, 0))

    # A restrained ground plane catches soft shadows without competing with overlays.
    floor_mat = material("Midnight backdrop", (0.006, 0.018, 0.034), metallic=0.05, roughness=0.48)
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0.9, -3.0))
    floor = bpy.context.object
    floor.name = "Midnight studio floor"
    floor.data.materials.append(floor_mat)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output_dir / "frame_")
    scene.frame_set(1)
    return scene


def main():
    args = arguments()
    if args.width < 270 or args.height < 480 or args.frames < 24:
        raise SystemExit("Preview must be at least 270x480 and 24 frames.")
    scene = build_scene(args)
    bpy.ops.render.render(animation=True)
    first_frame = output_dir / "frame_0001.png"
    last_frame = output_dir / f"frame_{scene.frame_end:04d}.png"
    if not first_frame.is_file() or not last_frame.is_file():
        raise SystemExit(f"Blender did not produce the expected PNG sequence in {output_dir}")
    print(f"FITFUEL_BLENDER_FRAMES={output_dir} frames={scene.frame_end}")


if __name__ == "__main__":
    main()
