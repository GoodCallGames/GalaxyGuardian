"""Shared helpers for the Galaxy Guardian Blender asset scripts.

Conventions: 1 Blender unit = 1 game unit (the old sprites were ~26px, so ships
are ~26 units long). Models are built with +X as "forward" and +Z as up; the
glTF exporter turns that into Godot's +X forward / +Y up.
"""
import math
import os

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_DIR = os.path.join(PROJECT_ROOT, "assets", "models")


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def srgb_to_linear(c):
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)


def hex_color(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def make_material(name, color, metallic=0.0, roughness=0.5, emission=None, emission_strength=0.0):
    """`color`/`emission` are sRGB 0-1 triples."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*srgb_to_linear(color), 1.0)
    mat.diffuse_color = (*srgb_to_linear(color), 1.0)  # Workbench previews
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*srgb_to_linear(emission), 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def vertex_color_material(name, roughness=0.9):
    """White material whose base color comes from the mesh's active color attribute."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = roughness
    attr = nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    mat.node_tree.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def xf(loc=(0, 0, 0), rot_deg=(0, 0, 0), scale=(1, 1, 1)):
    rot = Euler([math.radians(a) for a in rot_deg], "XYZ").to_matrix().to_4x4()
    scl = Matrix.Diagonal((*scale, 1.0))
    return Matrix.Translation(loc) @ rot @ scl


def sphere(bm, radius=1.0, loc=(0, 0, 0), scale=(1, 1, 1), rot_deg=(0, 0, 0), segs=16, rings=10):
    verts = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=radius)["verts"]
    bmesh.ops.transform(bm, matrix=xf(loc, rot_deg, scale), verts=verts)
    return verts


def cone(bm, r1, r2, depth, loc=(0, 0, 0), rot_deg=(0, 0, 0), segs=12, scale=(1, 1, 1)):
    """Axis is local Z; r1 is the bottom radius, r2 the top."""
    verts = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                                  radius1=r1, radius2=r2, depth=depth)["verts"]
    bmesh.ops.transform(bm, matrix=xf(loc, rot_deg, scale), verts=verts)
    return verts


def along_x(rot_deg=(0, 0, 0)):
    """Rotation that turns a Z-axis primitive to point along +X, plus extra rotation."""
    return (rot_deg[0], 90 + rot_deg[1], rot_deg[2])


def torus(bm, major, minor, loc=(0, 0, 0), rot_deg=(0, 0, 0), major_segs=24, minor_segs=8):
    """Ring around local Z."""
    verts = []
    rings = []
    for i in range(major_segs):
        a = 2 * math.pi * i / major_segs
        ring = []
        for j in range(minor_segs):
            b = 2 * math.pi * j / minor_segs
            r = major + minor * math.cos(b)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b))))
        rings.append(ring)
        verts += ring
    for i in range(major_segs):
        for j in range(minor_segs):
            bm.faces.new((rings[i][j], rings[(i + 1) % major_segs][j],
                          rings[(i + 1) % major_segs][(j + 1) % minor_segs], rings[i][(j + 1) % minor_segs]))
    bmesh.ops.transform(bm, matrix=xf(loc, rot_deg), verts=verts)
    return verts


def prism(bm, points_xy, z0, z1, mirror_y=False):
    """Extrude a convex-ish XY polygon between z0 and z1 (flat plate)."""
    def build(pts):
        bottom = [bm.verts.new((x, y, z0)) for x, y in pts]
        top = [bm.verts.new((x, y, z1)) for x, y in pts]
        bm.faces.new(top)
        bm.faces.new(list(reversed(bottom)))
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    build(points_xy)
    if mirror_y:
        build([(x, -y) for x, y in reversed(points_xy)])


def loft(bm, stations, sides=10):
    """Body of revolution-ish hull. stations: (x, half_width, z_top, z_bottom).
    A station with half_width 0 collapses to a single point (nose or tail tip)."""
    rings = []
    for x, hw, zt, zb in stations:
        if hw <= 1e-6:
            rings.append([bm.verts.new((x, 0, (zt + zb) * 0.5))])
            continue
        ring = []
        for k in range(sides):
            t = 2 * math.pi * k / sides
            s = math.sin(t)
            z = zt * s if s >= 0 else zb * s
            ring.append(bm.verts.new((x, hw * math.cos(t), z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for k in range(sides):
                bm.faces.new((a[0], b[(k + 1) % sides], b[k]))
        elif len(b) == 1:
            for k in range(sides):
                bm.faces.new((a[k], a[(k + 1) % sides], b[0]))
        else:
            for k in range(sides):
                k2 = (k + 1) % sides
                bm.faces.new((a[k], a[k2], b[k2], b[k]))
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        bm.faces.new(rings[-1])


def finish(bm, name, material, smooth=True, loc=(0, 0, 0)):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    if material is not None:
        mesh.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth = smooth
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    return obj


def export_glb(objects, filename):
    os.makedirs(MODEL_DIR, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    path = os.path.join(MODEL_DIR, filename)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_cameras=False,
        export_lights=False,
        export_vertex_color="ACTIVE",
    )
    print("exported", path)
    return path


def preview(objects, filename, rotation_deg=(65, 0, 125), size=640, distance=60):
    """Quick Workbench render so models can be eyeballed without opening Godot."""
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.world = bpy.data.worlds.new("pv")
    scene.world.color = (0.02, 0.03, 0.06)
    cam_data = bpy.data.cameras.new("pvcam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = distance
    cam = bpy.data.objects.new("pvcam", cam_data)
    scene.collection.objects.link(cam)
    cam.rotation_euler = [math.radians(a) for a in rotation_deg]
    direction = cam.rotation_euler.to_matrix() @ Vector((0, 0, 1))
    cam.location = direction * 100
    scene.camera = cam
    out = os.path.join(PROJECT_ROOT, "art", "previews")
    os.makedirs(out, exist_ok=True)
    scene.render.filepath = os.path.join(out, filename)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)


def prism_xz(bm, points_xz, y0, y1):
    """Extrude a polygon drawn in the XZ (side-view) plane between y0 and y1."""
    n = len(points_xz)
    near = [bm.verts.new((x, y0, z)) for x, z in points_xz]
    far = [bm.verts.new((x, y1, z)) for x, z in points_xz]
    bm.faces.new(near)
    bm.faces.new(list(reversed(far)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((near[i], near[j], far[j], far[i]))


def arc_blade(bm, center_xz, radius, a0_deg, a1_deg, max_width, thickness_y,
              steps=16, sides=6, start_width=0.5):
    """Curved, tapering blade (a crescent claw) lying in the XZ plane.
    Starts `start_width` * max_width thick and tapers to a point at the end."""
    rings = []
    for i in range(steps + 1):
        t = i / steps
        ang = math.radians(a0_deg + (a1_deg - a0_deg) * t)
        radial = Vector((math.cos(ang), 0.0, math.sin(ang)))
        centre = Vector((center_xz[0], 0.0, center_xz[1])) + radial * radius
        bulge = start_width + (1.0 - start_width) * math.sin(math.pi * min(t * 1.25, 1.0) * 0.5)
        width = max_width * bulge * (1.0 - t ** 2.6)
        if width < 1e-3:
            rings.append([bm.verts.new(centre)])
            continue
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            off_r = (width * 0.5) * math.cos(a)
            off_y = (thickness_y * 0.5) * math.sin(a) * (0.35 + 0.65 * (width / max_width))
            ring.append(bm.verts.new(centre + radial * off_r + Vector((0.0, off_y, 0.0))))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(b) == 1:
            for k in range(sides):
                bm.faces.new((a[k], a[(k + 1) % sides], b[0]))
        else:
            for k in range(sides):
                k2 = (k + 1) % sides
                bm.faces.new((a[k], a[k2], b[k2], b[k]))
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))


def icosphere(bm, radius=1.0, loc=(0, 0, 0), scale=(1, 1, 1), rot_deg=(0, 0, 0), subdivisions=2):
    verts = bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=radius)["verts"]
    bmesh.ops.transform(bm, matrix=xf(loc, rot_deg, scale), verts=verts)
    return verts


def box(bm, size=(1, 1, 1), loc=(0, 0, 0), rot_deg=(0, 0, 0)):
    verts = bmesh.ops.create_cube(bm, size=1.0)["verts"]
    bmesh.ops.transform(bm, matrix=xf(loc, rot_deg, size), verts=verts)
    return verts


def annulus(bm, r_in, r_out, segments=64, z=0.0):
    """Flat ring in the XY plane (double-sided via two faces per segment)."""
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        pts = [(r_in * math.cos(a0), r_in * math.sin(a0)), (r_out * math.cos(a0), r_out * math.sin(a0)),
               (r_out * math.cos(a1), r_out * math.sin(a1)), (r_in * math.cos(a1), r_in * math.sin(a1))]
        verts = [bm.verts.new((x, y, z)) for x, y in pts]
        bm.faces.new(verts)
        bm.faces.new(list(reversed([bm.verts.new((x, y, z)) for x, y in pts])))
