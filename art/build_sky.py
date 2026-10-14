"""Seamless equirectangular nebula panorama for Godot's PanoramaSkyMaterial.
Run: blender -b -P art/build_sky.py   (Cycles, CPU; emission-only so it is fast)"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bpy
from blender_common import PROJECT_ROOT, hex_color, srgb_to_linear, reset_scene

OUT = os.path.join(PROJECT_ROOT, "assets", "textures", "sky", "nebula.jpg")


def lin(h):
    return (*srgb_to_linear(hex_color(h)), 1.0)


def build():
    reset_scene()
    scene = bpy.context.scene
    world = bpy.data.worlds.new("Nebula")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    coord = nt.nodes.new("ShaderNodeTexCoord")

    def noise_node(scale, detail, distortion, w_offset, roughness=0.55):
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Location"].default_value = (w_offset, w_offset * 0.7, -w_offset * 0.4)
        nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.noise_dimensions = "3D"
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = roughness
        n.inputs["Distortion"].default_value = distortion
        nt.links.new(mapping.outputs["Vector"], n.inputs["Vector"])
        return n

    def ramp_node(stops, source):
        r = nt.nodes.new("ShaderNodeValToRGB")
        elements = r.color_ramp.elements
        while len(elements) > 1:
            elements.remove(elements[-1])
        for i, (pos, color) in enumerate(stops):
            e = elements[0] if i == 0 else elements.new(pos)
            e.position = pos
            e.color = color
        nt.links.new(source, r.inputs["Fac"])
        return r

    # Big soft cloud structure, carved by a second noise so there are dark voids.
    body = noise_node(1.5, 12.0, 1.1, 0.0)
    carve = noise_node(2.6, 8.0, 0.4, 7.3)
    carve_ramp = ramp_node([(0.38, (0, 0, 0, 1)), (0.68, (1, 1, 1, 1))], carve.outputs["Fac"])

    density = nt.nodes.new("ShaderNodeMath")
    density.operation = "MULTIPLY"
    nt.links.new(body.outputs["Fac"], density.inputs[0])
    nt.links.new(carve_ramp.outputs["Color"], density.inputs[1])
    # Density is mostly small, so stretch it before coloring.
    boost = nt.nodes.new("ShaderNodeMath")
    boost.operation = "MULTIPLY"
    boost.inputs[1].default_value = 1.55
    nt.links.new(density.outputs["Value"], boost.inputs[0])

    color = ramp_node([
        (0.00, lin("#010208")),
        (0.28, lin("#02071c")),
        (0.46, lin("#051a4a")),
        (0.64, lin("#0a4a82")),
        (0.80, lin("#2c2f8c")),
        (0.92, lin("#6a3496")),
        (1.00, lin("#a4489e")),
    ], boost.outputs["Value"])

    # A second, finer layer of wispy detail in a different hue.
    wisp = noise_node(5.5, 10.0, 0.8, 21.0, roughness=0.62)
    wisp_ramp = ramp_node([(0.55, (0, 0, 0, 1)), (0.85, lin("#0e3f80"))], wisp.outputs["Fac"])
    wisp_mask = nt.nodes.new("ShaderNodeMix")
    wisp_mask.data_type = "RGBA"
    wisp_mask.blend_type = "ADD"
    wisp_mask.inputs["Factor"].default_value = 0.4
    nt.links.new(color.outputs["Color"], wisp_mask.inputs["A"])
    nt.links.new(wisp_ramp.outputs["Color"], wisp_mask.inputs["B"])
    nt.links.new(wisp_mask.outputs["Result"], bg.inputs["Color"])

    cam_data = bpy.data.cameras.new("pano")
    cam_data.type = "PANO"
    cam_data.panorama_type = "EQUIRECTANGULAR"
    cam = bpy.data.objects.new("pano", cam_data)
    scene.collection.objects.link(cam)
    cam.rotation_euler = (math.radians(90), 0, 0)
    scene.camera = cam

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 8
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 4096
    scene.render.resolution_y = 2048
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.dither_intensity = 1.0
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 95
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    scene.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("sky written", OUT)


if __name__ == "__main__":
    build()
