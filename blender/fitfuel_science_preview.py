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
    parser.add_argument("--title", default="HUMAN MUSCLE ANATOMY")
    parser.add_argument("--blend-file", default="output/fitfuel-science-preview.blend")
    parser.add_argument("--subtitle", default="Layered 3D muscle groups in motion")
    parser.add_argument("--view", choices=("anterior", "posterior"), default="anterior")
    parser.add_argument("--topic", choices=("anatomy", "muscle", "protein", "heart", "fat_loss", "hydration", "exercise", "nutrition", "hormones", "creatine", "supplements", "tracking", "recovery", "general"), default="anatomy")
    parser.add_argument("--clean", action="store_true", help="Render a clean visual plate for the production timeline")
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
        # Avoid Weighted Normal: it has caused instability on headless runners.
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
            x = curve + math.cos(angle) * radius_x * profile
            y = math.sin(angle) * radius_y * profile
            verts.append((x, y, z))
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
    obj.location = center
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


def add_cylinder(name, location, radius, depth, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("Rounded edges", "BEVEL")
    bevel.width = min(radius * 0.18, 0.08)
    bevel.segments = 3
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def add_tube(name, points, material, thickness=0.08):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 20
    curve.bevel_depth = thickness
    curve.bevel_resolution = 4
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def add_science_topic(topic, args, teal, mint, blue, white, muted, signal):
    """Build a distinct 3D science metaphor for each supported scene category."""
    center_y = -0.15
    label = topic.upper().replace("_", " ")
    if topic == "muscle":
        for index, x in enumerate((-1.15, -0.38, 0.38, 1.15)):
            add_muscle_belly(f"Muscle fiber bundle {index + 1}", (x, 0, 0),
                             4.7, 0.34, 0.28, teal if index % 2 else mint,
                             args.frames, 1.0, 0.45)
            for row in range(7):
                band = add_bar(f"Fiber striation {index}-{row}",
                               (x, -0.31, -2.0 + row * 0.66),
                               (0.48, 0.08, 0.07), signal, 0.025)
                band.keyframe_insert(data_path="location", frame=1)
                band.location.z += 0.12
                band.keyframe_insert(data_path="location", frame=args.frames // 2)
                band.location.z -= 0.12
                band.keyframe_insert(data_path="location", frame=args.frames)
        view_label = "3D MUSCLE FIBERS  /  CONTRACTION"
    elif topic == "protein":
        coords = [(-2.2, 0, 1.4), (-1.45, 0, 0.6), (-0.7, 0, 1.2),
                  (0.05, 0, 0.25), (0.8, 0, 0.9), (1.55, 0, -0.1), (2.2, 0, 0.55)]
        for i, point in enumerate(coords):
            node = add_body_core(f"Amino acid {i + 1}", point, (0.34, 0.34, 0.34),
                                 mint if i % 2 else blue)
            node.keyframe_insert(data_path="location", frame=1)
            node.location.z += 0.22
            node.keyframe_insert(data_path="location", frame=args.frames // 2)
            node.location.z -= 0.22
            node.keyframe_insert(data_path="location", frame=args.frames)
        add_tube("Peptide backbone", coords, teal, 0.095)
        add_muscle_belly("New protein strand", (0, 0.15, -1.5), 2.7, 0.22, 0.22,
                         signal, args.frames, 0.8, 0.4)
        view_label = "AMINO ACIDS  /  PROTEIN SYNTHESIS"
    elif topic == "heart":
        heart = add_body_core("Heart | left ventricle", (-0.42, 0, 0), (0.72, 0.38, 1.15), signal)
        heart2 = add_body_core("Heart | right ventricle", (0.42, 0, 0), (0.72, 0.38, 1.15), teal)
        for obj in (heart, heart2):
            for frame, scale in ((1, 1.0), (args.frames // 4, 1.09), (args.frames // 2, 1.0),
                                 (3 * args.frames // 4, 1.09), (args.frames, 1.0)):
                obj.scale = (scale, scale, scale)
                obj.keyframe_insert(data_path="scale", frame=frame)
        add_tube("Aorta", [(0, 0, 0.7), (0, 0, 1.65), (0.5, 0, 2.15)], mint, 0.22)
        add_tube("Pulmonary artery", [(-0.25, 0, 0.55), (-0.9, 0, 1.25), (-1.3, 0, 1.75)], blue, 0.17)
        view_label = "CARDIAC CYCLE  /  BLOOD FLOW"
    elif topic == "hydration":
        drop = add_body_core("Water droplet", (0, 0, 0), (1.05, 0.42, 1.65), blue)
        drop.rotation_euler[1] = 0.12
        for i, (x, z) in enumerate(((-1.6, 1.4), (1.55, 1.1), (-1.5, -1.2), (1.5, -1.45))):
            ion = add_body_core(f"Electrolyte ion {i + 1}", (x, -0.1, z), (0.23, 0.23, 0.23),
                                mint if i % 2 else signal)
            for frame, offset in ((1, 0), (args.frames // 2, 0.35), (args.frames, 0)):
                ion.location.x = x + offset
                ion.keyframe_insert(data_path="location", frame=frame)
        view_label = "WATER  /  ELECTROLYTE BALANCE"
    elif topic == "exercise":
        # A 3D hinge joint with bone segments and a moving lever arm.
        joint = add_body_core("Joint articulation", (0, 0, 0), (0.55, 0.42, 0.55), signal)
        upper = add_cylinder("Upper bone", (-0.15, 0, 1.55), 0.24, 2.7, white,
                             (0, 0.12, 0))
        lower = add_cylinder("Lower bone", (1.1, 0, -1.15), 0.22, 2.7, white,
                             (0, 0, -0.42))
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
        hinge = bpy.context.object
        hinge.name = "Biomechanical hinge pivot"
        lower.parent = hinge
        lower.matrix_parent_inverse = hinge.matrix_world.inverted()
        for frame, angle in ((1, -0.1), (args.frames // 2, 0.48), (args.frames, -0.1)):
            hinge.rotation_euler[1] = angle
            hinge.keyframe_insert(data_path="rotation_euler", frame=frame)
        add_body_core("Joint head", (-0.12, -0.3, 0.02), (0.32, 0.22, 0.32), mint)
        view_label = "JOINT MECHANICS  /  RANGE OF MOTION"
    elif topic == "nutrition":
        add_cylinder("Nutrition plate", (0, 0.1, 0), 2.05, 0.18, blue, (math.pi / 2, 0, 0))
        for i, (x, z, mat) in enumerate(((-0.9, 0.4, mint), (0.7, 0.55, signal),
                                         (0.65, -0.75, teal), (-0.85, -0.75, white))):
            food = add_body_core(f"Food group {i + 1}", (x, -0.12, z), (0.58, 0.24, 0.52), mat)
            food.rotation_euler[1] = i * 0.2
            for frame, offset in ((1, 0), (args.frames // 2, 0.12), (args.frames, 0)):
                food.location.z = z + offset
                food.keyframe_insert(data_path="location", frame=frame)
        view_label = "3D NUTRIENT PLATE  /  FUEL"
    elif topic == "fat_loss":
        beam = add_bar("Energy balance beam", (0, 0, 0.8), (3.7, 0.22, 0.18), mint, 0.08)
        for frame, angle in ((1, -0.08), (args.frames // 2, 0.08), (args.frames, -0.08)):
            beam.rotation_euler[1] = angle
            beam.keyframe_insert(data_path="rotation_euler", frame=frame)
        add_cylinder("Energy balance pivot", (0, 0, 0.15), 0.28, 1.15, white)
        for side in (-1, 1):
            x = side * 1.55
            add_tube(f"Balance cable {side}", [(x, 0, 0.75), (x, 0, -0.6)], signal, 0.045)
            add_bar(f"Balance pan {side}", (x, 0, -0.72), (1.0, 0.16, 0.12), blue, 0.05)
            for i in range(3):
                add_body_core(f"Energy token {side}-{i}", (x + (i - 1) * 0.22, -0.15, -0.42),
                              (0.13, 0.13, 0.13), mint if side < 0 else signal)
        view_label = "ENERGY IN  /  ENERGY OUT"
    elif topic == "hormones":
        cell = add_body_core("Cell membrane", (0, 0.2, 0), (1.55, 0.45, 1.55), blue)
        receptor = add_cylinder("Cell receptor", (0, -0.52, 1.25), 0.18, 1.1, mint)
        ligand = add_body_core("Hormone signal", (-1.8, -0.2, 1.8), (0.28, 0.28, 0.28), signal)
        for frame, x in ((1, -1.8), (args.frames // 2, -0.35), (args.frames, -1.8)):
            ligand.location.x = x
            ligand.keyframe_insert(data_path="location", frame=frame)
        view_label = "HORMONE SIGNAL  /  CELL RECEPTOR"
    elif topic == "creatine":
        atp = add_body_core("ATP molecule", (-1.1, 0, 0.3), (0.75, 0.42, 0.75), mint)
        adp = add_body_core("ADP molecule", (1.1, 0, 0.3), (0.68, 0.42, 0.68), blue)
        phosphate = add_body_core("Phosphate group", (0, -0.2, 1.65), (0.3, 0.3, 0.3), signal)
        for frame, x in ((1, 0), (args.frames // 2, 0.9), (args.frames, 0)):
            phosphate.location.x = x
            phosphate.keyframe_insert(data_path="location", frame=frame)
        add_tube("ATP ADP reaction path", [(-0.25, -0.2, 0.3), (0, -0.2, 0.3), (0.25, -0.2, 0.3)], white, 0.08)
        view_label = "ATP  /  ADP  /  PHOSPHOCREATINE"
    elif topic == "supplements":
        add_cylinder("Supplement container", (0, 0, 0), 0.85, 2.7, blue)
        add_cylinder("Bottle cap", (0, 0, 1.48), 0.88, 0.35, mint)
        add_bar("Bottle label", (0, -0.88, 0), (1.1, 0.08, 0.95), white, 0.06)
        for i in range(3):
            capsule = add_body_core(f"Supplement capsule {i + 1}", (1.35, -0.15, 0.8 - i * 0.8),
                                    (0.18, 0.18, 0.42), signal if i % 2 else mint)
            capsule.rotation_euler[1] = 0.55
            for frame, offset in ((1, 0), (args.frames // 2, 0.16), (args.frames, 0)):
                capsule.location.z = 0.8 - i * 0.8 + offset
                capsule.keyframe_insert(data_path="location", frame=frame)
        view_label = "SUPPLEMENT FORM  /  DOSE"
    elif topic == "tracking":
        for i, height in enumerate((0.8, 1.35, 2.0, 2.8, 3.5)):
            bar = add_bar(f"Progress bar {i + 1}", (-1.8 + i * 0.9, 0, -0.5 + height / 2),
                          (0.5, 0.28, height), mint if i % 2 else blue, 0.06)
            bar.keyframe_insert(data_path="scale", frame=1)
            bar.scale.z *= 1.12
            bar.keyframe_insert(data_path="scale", frame=args.frames)
        view_label = "PROGRESSIVE OVERLOAD  /  TRACKING"
    elif topic == "recovery":
        add_cylinder("Recovery clock face", (0, 0.1, 0), 1.6, 0.18, blue, (math.pi / 2, 0, 0))
        minute = add_bar("Clock hand minute", (0, -0.18, 0.55), (0.09, 0.08, 1.1), mint, 0.03)
        add_bar("Clock hand hour", (0.42, -0.2, 0), (0.85, 0.08, 0.09), signal, 0.03)
        for frame, angle in ((1, 0), (args.frames // 2, 0.8), (args.frames, 0)):
            minute.rotation_euler[1] = angle
            minute.keyframe_insert(data_path="rotation_euler", frame=frame)
        add_body_core("Recovery moon", (1.8, 0.1, 1.6), (0.45, 0.25, 0.45), mint)
        view_label = "REST  /  RECOVERY  /  ADAPTATION"
    else:  # general 3D science process
        nodes = [(-1.65, 0, 0), (0, 0, 0), (1.65, 0, 0)]
        for index, point in enumerate(nodes):
            node = add_body_core(f"Science process node {index + 1}", point,
                                 (0.58, 0.38, 0.58), (blue, mint, signal)[index])
            for frame, offset in ((1, 0), (args.frames // 2, 0.22), (args.frames, 0)):
                node.location.z = offset
                node.keyframe_insert(data_path="location", frame=frame)
        add_tube("Science process connector 1", [nodes[0], (-0.8, 0, 0), nodes[1]], white, 0.08)
        add_tube("Science process connector 2", [nodes[1], (0.8, 0, 0), nodes[2]], white, 0.08)
        view_label = "INPUT  /  PROCESS  /  RESULT"
    activation_name = f"{label} 3D motion signal"
    activation_y = -0.7
    return view_label, activation_name, activation_y


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

    bpy.ops.object.camera_add(location=(0, 18 if args.view == "posterior" else -18, 0))
    camera = bpy.context.object
    camera.name = "Portrait science camera"
    aim(camera, (0, 0, 0))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 11.6 if args.topic == "anatomy" else 7.2
    scene.camera = camera

    muscle_base = make_material("Anatomy | deep muscle", (0.30, 0.075, 0.085), 0.05, 0.42)
    muscle_light = make_material("Anatomy | muscle highlights", (0.62, 0.16, 0.18), 0.04, 0.36)
    muscle_target = make_material("Anatomy | active muscle teal", (0.035, 0.72, 0.62), 0.18, 0.25, 0.22)
    tendon = make_material("Anatomy | tendons", (0.72, 0.48, 0.39), 0.0, 0.48)
    bone = make_material("Anatomy | bone landmarks", (0.78, 0.72, 0.61), 0.0, 0.48)

    if args.topic == "anatomy":
        # A complete stylized 3D anterior upper-body anatomy model. Muscle bellies
        # are independent meshes, so later scenes can highlight the exact target group.
        # Torso silhouette, neck, pelvis and head establish anatomical proportions.
        add_body_core("Thorax | 3D anatomical base", (0, 0.12, 0.25), (1.28, 0.48, 2.00), muscle_base)
        add_body_core("Abdominal wall | base", (0, -0.01, -1.55), (0.82, 0.39, 1.05), muscle_base)
        add_body_core("Pelvis | base", (0, 0.10, -2.55), (0.92, 0.43, 0.48), tendon)
        add_body_core("Neck", (0, 0.02, 2.38), (0.34, 0.34, 0.62), tendon)
        add_body_core("Head | silhouette", (0, 0.04, 3.28), (0.52, 0.48, 0.66), tendon)
        # Limb masses sit behind the independently modeled muscle bellies.
        for side in (-1, 1):
            add_body_core(f"Upper arm | core {side}", (side * 1.40, 0.12, 0.58),
                          (0.29, 0.30, 1.03), tendon)
            add_body_core(f"Forearm | core {side}", (side * 1.62, 0.14, -0.48),
                          (0.23, 0.25, 0.83), tendon)
            add_body_core(f"Thigh | core {side}", (side * 0.52, 0.16, -3.48),
                          (0.43, 0.42, 1.18), muscle_base)
            add_body_core(f"Lower leg | core {side}", (side * 0.54, 0.17, -4.76),
                          (0.29, 0.30, 0.91), tendon)

        if args.view == "anterior":
            # Pectorals, individually modeled left and right.
            for side, label in ((-1, "L"), (1, "R")):
                add_muscle_belly(f"Pectoralis major upper head {label}", (side * 0.60, -0.40, 1.43),
                                 0.56, 0.52, 0.21, muscle_target, args.frames, 1.0, 0.58)
                add_muscle_belly(f"Pectoralis major lower head {label}", (side * 0.64, -0.42, 0.88),
                                 0.56, 0.50, 0.21, muscle_target, args.frames, 1.0, 0.58)
                add_muscle_belly(f"Deltoid anterior head {label}", (side * 1.20, -0.26, 1.82),
                                 0.58, 0.31, 0.27, muscle_light, args.frames, 0.9, 0.62)
                add_muscle_belly(f"Deltoid lateral head {label}", (side * 1.32, -0.22, 1.48),
                                 0.68, 0.29, 0.30, muscle_target, args.frames, 0.9, 0.62)
                add_muscle_belly(f"Deltoid posterior head {label}", (side * 1.18, -0.06, 1.25),
                                 0.56, 0.25, 0.26, muscle_light, args.frames, 0.7, 0.62)
                add_muscle_belly(f"Biceps brachii long head {label}", (side * 1.46, -0.27, 0.73),
                                 0.88, 0.22, 0.20, muscle_target, args.frames, 0.85, 0.52)
                add_muscle_belly(f"Biceps brachii short head {label}", (side * 1.51, -0.30, 0.45),
                                 0.78, 0.21, 0.19, muscle_light, args.frames, 0.8, 0.52)
                add_muscle_belly(f"Brachialis {label}", (side * 1.52, -0.28, 0.10),
                                 0.58, 0.18, 0.16, muscle_base, args.frames, 0.65, 0.5)
                add_muscle_belly(f"Forearm flexors {label}", (side * 1.62, -0.12, -0.43),
                                 1.05, 0.25, 0.23, muscle_base, args.frames, 0.5, 0.48)
                add_muscle_belly(f"External oblique {label}", (side * 0.67, -0.34, -1.18),
                                 1.05, 0.25, 0.18, muscle_light, args.frames, 0.7, 0.50)
                add_muscle_belly(f"Internal oblique {label}", (side * 0.54, -0.38, -1.48),
                                 0.78, 0.20, 0.14, muscle_base, args.frames, 0.6, 0.48)
                for segment, z in enumerate((-0.95, -1.43, -1.91), 1):
                    add_muscle_belly(f"Rectus abdominis segment {segment} {label}",
                                     (side * 0.20, -0.42, z), 0.39, 0.18, 0.12,
                                     muscle_target, args.frames, 0.75, 0.42)
                add_muscle_belly(f"Quadriceps rectus femoris {label}", (side * 0.48, -0.20, -3.42),
                                 1.40, 0.24, 0.22, muscle_target, args.frames, 0.8, 0.58)
                add_muscle_belly(f"Quadriceps vastus lateralis {label}", (side * 0.78, -0.17, -3.48),
                                 1.46, 0.25, 0.24, muscle_light, args.frames, 0.8, 0.58)
                add_muscle_belly(f"Quadriceps vastus medialis {label}", (side * 0.30, -0.18, -3.95),
                                 0.72, 0.22, 0.21, muscle_light, args.frames, 0.75, 0.58)
            add_bar("Sternum landmark", (0, -0.43, 1.12), (0.09, 0.08, 1.12), bone, 0.035)
            for side in (-1, 1):
                clavicle = add_bar(f"Clavicle landmark {side}", (side * 0.48, -0.42, 1.82),
                                   (0.92, 0.075, 0.075), bone, 0.035)
                clavicle.rotation_euler[1] = side * -0.12
            view_label = "ANTERIOR VIEW  /  FRONT MUSCLE GROUPS"
            activation_name = "Pectoral activation signal"
            activation_y = -0.72
        else:
            # Posterior muscle map: trapezius, latissimus, triceps, gluteals,
            # hamstrings and calves are separate animated 3D muscle meshes.
            add_muscle_belly("Trapezius upper", (0, 0.43, 1.78), 1.18, 0.62, 0.22,
                             muscle_target, args.frames, 0.9, 0.50)
            add_muscle_belly("Trapezius middle", (0, 0.44, 0.92), 0.82, 0.48, 0.19,
                             muscle_light, args.frames, 0.75, 0.50)
            add_muscle_belly("Trapezius lower", (0, 0.40, 0.25), 0.95, 0.34, 0.18,
                             muscle_base, args.frames, 0.65, 0.50)
            for side, label in ((-1, "L"), (1, "R")):
                add_muscle_belly(f"Latissimus dorsi {label}", (side * 0.68, 0.40, 0.25),
                                 1.95, 0.48, 0.22, muscle_target, args.frames, 1.0, 0.58)
                add_muscle_belly(f"Rhomboid {label}", (side * 0.38, 0.46, 1.05),
                                 0.78, 0.25, 0.16, muscle_light, args.frames, 0.7, 0.52)
                add_muscle_belly(f"Triceps brachii long head {label}", (side * 1.45, 0.28, 0.75),
                                 0.92, 0.23, 0.21, muscle_target, args.frames, 0.85, 0.52)
                add_muscle_belly(f"Triceps brachii lateral head {label}", (side * 1.50, 0.30, 0.38),
                                 0.80, 0.22, 0.20, muscle_light, args.frames, 0.8, 0.52)
                add_muscle_belly(f"Triceps brachii medial head {label}", (side * 1.43, 0.28, 0.05),
                                 0.68, 0.19, 0.17, muscle_base, args.frames, 0.7, 0.5)
                add_muscle_belly(f"Gluteus maximus {label}", (side * 0.48, 0.36, -2.55),
                                 0.95, 0.46, 0.24, muscle_target, args.frames, 0.9, 0.60)
                add_muscle_belly(f"Gluteus medius {label}", (side * 0.78, 0.38, -2.25),
                                 0.58, 0.30, 0.19, muscle_light, args.frames, 0.7, 0.55)
                add_muscle_belly(f"Biceps femoris {label}", (side * 0.70, 0.22, -3.55),
                                 1.45, 0.23, 0.21, muscle_target, args.frames, 0.8, 0.56)
                add_muscle_belly(f"Semitendinosus {label}", (side * 0.38, 0.22, -3.55),
                                 1.45, 0.21, 0.18, muscle_light, args.frames, 0.7, 0.56)
                add_muscle_belly(f"Gastrocnemius {label}", (side * 0.55, 0.12, -4.75),
                                 0.95, 0.28, 0.25, muscle_target, args.frames, 0.7, 0.52)
                add_muscle_belly(f"Soleus {label}", (side * 0.55, 0.15, -5.15),
                                 0.68, 0.23, 0.18, muscle_light, args.frames, 0.65, 0.52)
            view_label = "POSTERIOR VIEW  /  BACK MUSCLE GROUPS"
            activation_name = "Latissimus activation signal"
            activation_y = 0.70

    else:
        view_label, activation_name, activation_y = add_science_topic(
            args.topic, args, teal, mint, blue, white, muted, signal
        )

    # A subtle moving signal reinforces the selected 3D science mechanism.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, radius=0.13,
                                         location=(-0.55, activation_y, 0.75))
    pulse = bpy.context.object
    pulse.name = activation_name
    pulse.data.materials.append(signal)
    for frame, x in ((1, -0.55), (args.frames // 2, 0.55), (args.frames, -0.55)):
        pulse.location.x = x
        pulse.keyframe_insert(data_path="location", frame=frame)

    # Standalone previews include typography. Production plates stay clean so
    # HyperFrames can own the title, subtitles and word-timed kinetic type.
    if not args.clean:
        text_y = 0.8 if args.view == "posterior" else -0.8
        rule_y = 0.48 if args.view == "posterior" else -0.48
        add_text("Brand label", "FITFUEL  /  3D ANATOMY", (0, text_y, 5.00), 0.22, muted, camera)
        title = add_text("Main title", args.title, (0, text_y, 4.48), 0.31, white, camera)
        title.data.space_character = 1.05
        add_text("Subtitle", view_label, (0, text_y, 4.05), 0.16, muted, camera)
        add_bar("Callout rule left", (-2.12, rule_y, 1.35), (0.54, 0.05, 0.03), mint, 0.015)
        add_text("Callout label left", "MUSCLE GROUP", (-2.03, text_y, 1.08), 0.12, white, camera)
        add_bar("Callout rule right", (2.08, rule_y, -1.38), (0.54, 0.05, 0.03), signal, 0.015)
        add_text("Callout label right", "3D ACTIVATION", (1.98, text_y, -1.65), 0.12, white, camera)
        add_bar("Bottom accent", (0, rule_y, -4.55), (2.8, 0.08, 0.035), mint, 0.015)
        add_text("Footer", "CONTRACT  •  RELEASE  •  REPEAT", (0, text_y, -4.92), 0.18, white, camera)
        add_text("Scientific note", "Stylized 3D educational anatomy", (0, text_y, -5.25), 0.12, muted, camera)

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
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.blend_file).resolve()))
    bpy.ops.render.render(animation=True)
    first_frame = output_dir / "frame_0001.png"
    last_frame = output_dir / f"frame_{scene.frame_end:04d}.png"
    if not first_frame.is_file() or not last_frame.is_file():
        raise SystemExit(f"Missing expected PNG frames in {output_dir}")
    print(f"FITFUEL_BLENDER_FRAMES={output_dir} frames={scene.frame_end}")


if __name__ == "__main__":
    main()
