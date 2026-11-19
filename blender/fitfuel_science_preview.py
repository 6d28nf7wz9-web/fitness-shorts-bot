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


def add_muscle_belly(name, center, length, radius_x, radius_y, material, frames,
                      activation=1.0, taper=0.42):
    """Build an organic, tapered 3D muscle belly with a softly curved profile."""
    rings, sides = 12, 24
    verts, faces = [], []
    cx, cy, cz = center
    for ring in range(rings + 1):
        u = ring / rings
        z = (u - 0.5) * length
        profile = (math.sin(math.pi * (0.08 + 0.84 * u)) ** taper)
        profile = max(0.10, profile)
        curve = math.sin((u - 0.5) * math.pi) * radius_x * 0.10
        for side in range(sides):
            angle = 2 * math.pi * side / sides
            x = cx + curve + math.cos(angle) * radius_x * profile
            y = cy + math.sin(angle) * radius_y * profile
            verts.append((x, y, cz + z))
    for ring in range(rings):
        for side in range(sides):
            a = ring * sides + side
            b = ring * sides + (side + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces.append(tuple(range(sides - 1, -1, -1)))
    faces.append(tuple(rings * sides + i for i in range(sides)))
    mesh = bpy.data.meshes.new(name + " | anatomical surface")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    sub = obj.modifiers.new("Muscle surface refinement", "SUBSURF")
    sub.levels = 1
    # Gentle contraction is visible but never distorts the anatomical silhouette.
    for frame, factor in ((1, 1.0), (frames // 4, 1.0 + 0.045 * activation),
                          (frames // 2, 1.0), (3 * frames // 4, 1.0 + 0.045 * activation),
                          (frames, 1.0)):
        obj.scale = (factor, 1.0 - (factor - 1.0) * 0.35, 1.0)
        obj.keyframe_insert(data_path="scale", frame=frame)
    return obj


def add_body_core(name, location, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def build_scene(args):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    # Blender 4.x renamed Eevee; retain compatibility with older runners.
    engines = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 16
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
    camera.data.ortho_scale = 11.6
    scene.camera = camera

    # A complete stylized 3D anterior upper-body anatomy model. Muscle bellies
    # are independent meshes, so later scenes can highlight the exact target group.
    muscle_base = make_material("Anatomy | deep muscle", (0.30, 0.075, 0.085), 0.05, 0.42)
    muscle_light = make_material("Anatomy | muscle highlights", (0.62, 0.16, 0.18), 0.04, 0.36)
    muscle_target = make_material("Anatomy | active muscle teal", (0.035, 0.72, 0.62), 0.18, 0.25, 0.22)
    tendon = make_material("Anatomy | tendons", (0.72, 0.48, 0.39), 0.0, 0.48)
    bone = make_material("Anatomy | bone landmarks", (0.78, 0.72, 0.61), 0.0, 0.48)

    # Torso silhouette, neck, pelvis and head establish anatomical proportions.
    add_body_core("Thorax | 3D anatomical base", (0, 0.12, 0.25), (1.28, 0.48, 2.00), muscle_base)
    add_body_core("Abdominal wall | base", (0, -0.01, -1.55), (0.82, 0.39, 1.05), muscle_base)
    add_body_core("Pelvis | base", (0, 0.10, -2.55), (0.92, 0.43, 0.48), tendon)
    add_body_core("Neck", (0, 0.02, 2.38), (0.34, 0.34, 0.62), tendon)
    add_body_core("Head | silhouette", (0, 0.04, 3.28), (0.52, 0.48, 0.66), tendon)

    # Pectorals, individually modeled left and right.
    for side, label in ((-1, "L"), (1, "R")):
        add_muscle_belly(f"Pectoralis major {label}", (side * 0.62, -0.40, 1.12),
                         0.92, 0.58, 0.23, muscle_target, args.frames, 1.0, 0.58)
        add_muscle_belly(f"Deltoid {label}", (side * 1.20, -0.23, 1.62),
                         0.86, 0.38, 0.34, muscle_light, args.frames, 0.9, 0.62)
        add_muscle_belly(f"Biceps brachii {label}", (side * 1.48, -0.25, 0.55),
                         1.18, 0.30, 0.27, muscle_target, args.frames, 0.85, 0.52)
        add_muscle_belly(f"Forearm flexors {label}", (side * 1.62, -0.12, -0.43),
                         1.05, 0.25, 0.23, muscle_base, args.frames, 0.5, 0.48)
        add_muscle_belly(f"External oblique {label}", (side * 0.67, -0.34, -1.18),
                         1.05, 0.25, 0.18, muscle_light, args.frames, 0.7, 0.50)
        add_muscle_belly(f"Rectus abdominis {label}", (side * 0.22, -0.39, -1.45),
                         1.35, 0.19, 0.13, muscle_target, args.frames, 0.75, 0.40)
        add_muscle_belly(f"Quadriceps {label}", (side * 0.52, -0.17, -3.45),
                         1.55, 0.39, 0.32, muscle_light, args.frames, 0.8, 0.58)

    # Clavicles and sternum provide clear landmarks without cluttering the muscle map.
    add_bar("Sternum landmark", (0, -0.43, 1.12), (0.09, 0.08, 1.12), bone, 0.035)
    for side in (-1, 1):
        clavicle = add_bar(f"Clavicle landmark {side}", (side * 0.48, -0.42, 1.82),
                           (0.92, 0.075, 0.075), bone, 0.035)
        clavicle.rotation_euler[1] = side * -0.12

    # A moving activation pulse travels along the selected pectoral group.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, radius=0.13,
                                         location=(-0.55, -0.72, 0.75))
    pulse = bpy.context.object
    pulse.name = "Traveling activation signal"
    pulse.data.materials.append(signal)
    for frame, x in ((1, -0.55), (args.frames // 2, 0.55), (args.frames, -0.55)):
        pulse.location.x = x
        pulse.keyframe_insert(data_path="location", frame=frame)

    # Small labels frame the anatomy; the model remains the visual focal point.
    add_text("Brand label", "FITFUEL  /  3D ANATOMY", (0, -0.8, 5.00), 0.22, muted, camera)
    title = add_text("Main title", args.title, (0, -0.8, 4.48), 0.31, white, camera)
    title.data.space_character = 1.05
    add_text("Subtitle", "Layered muscle groups • animated contraction", (0, -0.8, 4.05), 0.17, muted, camera)
    add_bar("Callout rule left", (-2.12, -0.48, 1.35), (0.54, 0.05, 0.03), mint, 0.015)
    add_text("Callout label left", "PECTORAL", (-2.03, -0.82, 1.08), 0.14, white, camera)
    add_bar("Callout rule right", (2.08, -0.48, -1.38), (0.54, 0.05, 0.03), signal, 0.015)
    add_text("Callout label right", "ABDOMINAL", (1.98, -0.82, -1.65), 0.14, white, camera)
    add_bar("Bottom accent", (0, -0.4, -4.55), (2.8, 0.08, 0.035), mint, 0.015)
    add_text("Footer", "CONTRACT  •  RELEASE  •  REPEAT", (0, -0.8, -4.92), 0.18, white, camera)
    add_text("Scientific note", "Stylized 3D educational anatomy", (0, -0.8, -5.25), 0.12, muted, camera)

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
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "../fitfuel-science-preview.blend"))
    bpy.ops.render.render(animation=True)
    first_frame = output_dir / "frame_0001.png"
    last_frame = output_dir / f"frame_{scene.frame_end:04d}.png"
    if not first_frame.is_file() or not last_frame.is_file():
        raise SystemExit(f"Missing expected PNG frames in {output_dir}")
    print(f"FITFUEL_BLENDER_FRAMES={output_dir} frames={scene.frame_end}")


if __name__ == "__main__":
    main()
