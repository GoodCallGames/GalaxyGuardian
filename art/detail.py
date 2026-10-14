"""Detail toolkit: bevelled hard-surface parts, procedural panel materials and
texture baking, so the glTF models carry real surface detail (panel seams, grime,
scratches, ambient occlusion) rather than flat colors."""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from blender_common import *  # noqa: F401,F403

CACHE_DIR = os.path.join(PROJECT_ROOT, "art", "bake_cache")


# ----------------------------------------------------------------- geometry

def mark_sharp(bm, angle_deg=35.0):
    """Hard edges where faces meet at a sharp angle; everything else stays smooth."""
    limit = math.radians(angle_deg)
    for edge in bm.edges:
        if len(edge.link_faces) == 2:
            edge.smooth = edge.calc_face_angle(0.0) < limit
        else:
            edge.smooth = True


def finish_hs(bm, name, material, bevel=0.1, angle=35.0, segments=2):
    """Like finish(), but marks sharp edges and adds a bevel so edges catch light."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mark_sharp(bm, angle)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    if material is not None:
        mesh.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(angle)
        mod.harden_normals = True
    return obj


def bake_mesh_modifiers(obj):
    """Replace the object's mesh with its evaluated (modifiers applied) version."""
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated)
    old = obj.data
    obj.modifiers.clear()
    obj.data = mesh
    bpy.data.meshes.remove(old)


# ---------------------------------------------------------------- materials

def _node(nt, kind, **inputs):
    node = nt.nodes.new(kind)
    for key, value in inputs.items():
        node.inputs[key].default_value = value
    return node


def panel_material(name, base_hex, metallic=0.5, roughness=0.45, panel_scale=0.45,
                   seam=0.45, dirt=0.4, scratch=0.35, accent_hex=None, stripe=False,
                   emission=None, emission_strength=0.0):
    """Principled material whose color comes from a procedural network (panel seams,
    tonal variation, grime, scratches). The final color node is named 'ColorOut' so
    bake_albedo() can find it."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*srgb_to_linear(emission), 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    base = (*srgb_to_linear(hex_color(base_hex)), 1.0)
    dark = tuple(c * 0.25 for c in base[:3]) + (1.0,)
    light = tuple(min(c * 1.35 + 0.02, 1.0) for c in base[:3]) + (1.0,)

    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])

    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 1.0 / max(panel_scale, 0.01) * 0.5
    brick.inputs["Mortar Size"].default_value = 0.018
    brick.inputs["Mortar Smooth"].default_value = 0.1
    brick.inputs["Brick Width"].default_value = 1.6
    brick.inputs["Row Height"].default_value = 0.8
    brick.inputs["Color1"].default_value = base
    brick.inputs["Color2"].default_value = tuple(c * 0.86 for c in base[:3]) + (1.0,)
    brick.inputs["Mortar"].default_value = tuple(c * (1.0 - seam) for c in base[:3]) + (1.0,)
    nt.links.new(mapping.outputs["Vector"], brick.inputs["Vector"])

    # Large soft grime blotches.
    grime = nt.nodes.new("ShaderNodeTexNoise")
    grime.inputs["Scale"].default_value = 0.5
    grime.inputs["Detail"].default_value = 10.0
    nt.links.new(mapping.outputs["Vector"], grime.inputs["Vector"])
    grime_ramp = nt.nodes.new("ShaderNodeValToRGB")
    grime_ramp.color_ramp.elements[0].position = 0.42
    grime_ramp.color_ramp.elements[1].position = 0.78
    nt.links.new(grime.outputs["Fac"], grime_ramp.inputs["Fac"])
    grime_mix = nt.nodes.new("ShaderNodeMix")
    grime_mix.data_type = "RGBA"
    grime_mix.blend_type = "MIX"
    grime_mix.inputs["Factor"].default_value = dirt
    grime_mix.inputs[7].default_value = dark
    # factor = dirt * ramp
    grime_fac = nt.nodes.new("ShaderNodeMath")
    grime_fac.operation = "MULTIPLY"
    grime_fac.inputs[1].default_value = dirt
    nt.links.new(grime_ramp.outputs["Color"], grime_fac.inputs[0])
    nt.links.new(brick.outputs["Color"], grime_mix.inputs[6])
    nt.links.new(grime_fac.outputs["Value"], grime_mix.inputs["Factor"])

    # Fine scratches: thin lines from Voronoi cell edges.
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 2.2
    nt.links.new(mapping.outputs["Vector"], vor.inputs["Vector"])
    warp = nt.nodes.new("ShaderNodeTexNoise")
    warp.inputs["Scale"].default_value = 1.4
    warp.inputs["Detail"].default_value = 4.0
    nt.links.new(mapping.outputs["Vector"], warp.inputs["Vector"])
    scratch_ramp = nt.nodes.new("ShaderNodeValToRGB")
    scratch_ramp.color_ramp.elements[0].position = 0.0
    scratch_ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    scratch_ramp.color_ramp.elements[1].position = 0.045
    scratch_ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    nt.links.new(vor.outputs["Distance"], scratch_ramp.inputs["Fac"])
    scratch_gate = nt.nodes.new("ShaderNodeMath")
    scratch_gate.operation = "MULTIPLY"
    nt.links.new(scratch_ramp.outputs["Color"], scratch_gate.inputs[0])
    gate_ramp = nt.nodes.new("ShaderNodeValToRGB")
    gate_ramp.color_ramp.elements[0].position = 0.55
    gate_ramp.color_ramp.elements[1].position = 0.7
    nt.links.new(warp.outputs["Fac"], gate_ramp.inputs["Fac"])
    nt.links.new(gate_ramp.outputs["Color"], scratch_gate.inputs[1])
    scratch_fac = nt.nodes.new("ShaderNodeMath")
    scratch_fac.operation = "MULTIPLY"
    scratch_fac.inputs[1].default_value = scratch
    nt.links.new(scratch_gate.outputs["Value"], scratch_fac.inputs[0])
    final = nt.nodes.new("ShaderNodeMix")
    final.data_type = "RGBA"
    final.label = "ColorOut"
    final.name = "ColorOut"
    final.inputs[7].default_value = light
    nt.links.new(grime_mix.outputs[2], final.inputs[6])
    nt.links.new(scratch_fac.outputs["Value"], final.inputs["Factor"])
    color_socket = final.outputs[2]

    if stripe and accent_hex:
        # Diagonal hazard stripes.
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.inputs["Scale"].default_value = 1.2
        wave.inputs["Distortion"].default_value = 0.0
        wave.wave_type = "BANDS"
        wave.bands_direction = "DIAGONAL"
        nt.links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
        step = nt.nodes.new("ShaderNodeMath")
        step.operation = "GREATER_THAN"
        step.inputs[1].default_value = 0.55
        nt.links.new(wave.outputs["Fac"], step.inputs[0])
        stripe_mix = nt.nodes.new("ShaderNodeMix")
        stripe_mix.data_type = "RGBA"
        stripe_mix.inputs[7].default_value = (*srgb_to_linear(hex_color(accent_hex)), 1.0)
        nt.links.new(color_socket, stripe_mix.inputs[6])
        nt.links.new(step.outputs["Value"], stripe_mix.inputs["Factor"])
        color_socket = stripe_mix.outputs[2]
        stripe_mix.name = "ColorOut"

    nt.links.new(color_socket, bsdf.inputs["Base Color"])
    mat["color_node"] = color_socket.node.name
    return mat


# ------------------------------------------------------------------- baking

def _setup_cycles(samples=16):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False


def bake_albedo(obj, res=512, ao_strength=0.5, margin=6):
    """Unwrap `obj`, bake its procedural color (+ ambient occlusion) to a PNG, and
    rewire its material to use that image, so glTF export carries a real texture."""
    scene = bpy.context.scene
    _setup_cycles()
    bake_mesh_modifiers(obj)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.012)
    bpy.ops.object.mode_set(mode="OBJECT")

    mat = obj.active_material
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    bsdf = nt.nodes["Principled BSDF"]
    color_node = nt.nodes[mat["color_node"]]

    # Bake pure color through an Emission shader (immune to metallic darkening).
    emit = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(color_node.outputs[2], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])

    color_img = bpy.data.images.new(obj.name + "_color", res, res, alpha=False)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = color_img
    nt.nodes.active = tex
    bpy.ops.object.bake(type="EMIT", margin=margin, use_clear=True)

    ao_img = bpy.data.images.new(obj.name + "_ao", res, res, alpha=False)
    ao_img.colorspace_settings.name = "Non-Color"
    tex.image = ao_img
    scene.cycles.samples = 32
    bpy.ops.object.bake(type="AO", margin=margin, use_clear=True)

    color = np.array(color_img.pixels[:], dtype=np.float32).reshape(-1, 4)
    ao = np.array(ao_img.pixels[:], dtype=np.float32).reshape(-1, 4)
    shade = 1.0 - ao_strength + ao_strength * ao[:, :3]
    color[:, :3] *= shade
    color[:, 3] = 1.0
    color_img.pixels = color.ravel()

    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, obj.name + ".png")
    color_img.filepath_raw = path
    color_img.file_format = "PNG"
    color_img.save()
    final_img = bpy.data.images.load(path)
    final_img.name = obj.name + "_baked"

    # Restore the shader and feed it the baked image.
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tex.image = final_img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.nodes.remove(emit)
    bpy.data.images.remove(color_img)
    bpy.data.images.remove(ao_img)


# ------------------------------------------------------------------ preview

def render_preview(filename, rotation_deg=(90, 0, 0), size=720, distance=40, samples=40, target=(0, 0, 0)):
    """Cycles preview with a key light, so baked textures and emission are visible."""
    scene = bpy.context.scene
    _setup_cycles(samples)
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.view_settings.view_transform = "Standard"
    scene.world = bpy.data.worlds.new("pv")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.012, 0.02, 0.05, 1.0)
    bg.inputs["Strength"].default_value = 1.0

    sun = bpy.data.lights.new("key", "SUN")
    sun.energy = 3.0
    sun_obj = bpy.data.objects.new("key", sun)
    scene.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(55), math.radians(15), math.radians(-35))
    fill = bpy.data.lights.new("fill", "SUN")
    fill.energy = 0.8
    fill_obj = bpy.data.objects.new("fill", fill)
    scene.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = (math.radians(100), 0, math.radians(140))

    cam_data = bpy.data.cameras.new("pvcam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = distance
    cam = bpy.data.objects.new("pvcam", cam_data)
    scene.collection.objects.link(cam)
    cam.rotation_euler = [math.radians(a) for a in rotation_deg]
    direction = cam.rotation_euler.to_matrix() @ Vector((0, 0, 1))
    cam.location = Vector(target) + direction * 120
    scene.camera = cam
    out = os.path.join(PROJECT_ROOT, "art", "previews")
    os.makedirs(out, exist_ok=True)
    scene.render.filepath = os.path.join(out, filename)
    bpy.ops.render.render(write_still=True)
    for ob in (cam, sun_obj, fill_obj):
        bpy.data.objects.remove(ob)
