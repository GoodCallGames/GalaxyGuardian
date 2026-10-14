"""Planets, moon, asteroids and space debris. Run: blender -b -P art/build_space.py

Planets follow the look of the game's 2D backdrop: dark bodies that rely on a bright
rim of light (added in Godot by the atmosphere shader). Rocky things carry per-vertex
colors; the debris pieces use ordinary materials so they can have lights and glints."""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bmesh
import bpy
from mathutils import Vector, noise
from blender_common import *  # noqa: F401,F403


def lerp3(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def ramp(stops, t):
    t = max(stops[0][0], min(stops[-1][0], t))
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            return lerp3(c0, c1, (t - p0) / max(p1 - p0, 1e-6))
    return stops[-1][1]


def fbm(p, octaves=6, offset=(0, 0, 0)):
    return noise.fractal(Vector(p) + Vector(offset), 0.55, 2.0, octaves)


def paint_mesh(mesh, color_fn):
    attr = mesh.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    for i, v in enumerate(mesh.vertices):
        attr.data[i].color = (*srgb_to_linear(color_fn(v.co)), 1.0)
    for p in mesh.polygons:
        p.use_smooth = True


def painted_sphere(name, radius, subdiv, color_fn, relief_fn=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    for v in bm.verts:
        n = v.co.normalized()
        v.co = n * (radius * (1.0 + (relief_fn(n) if relief_fn else 0.0)))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    paint_mesh(mesh, lambda co: color_fn(co.normalized()))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(vertex_color_material(name + "_mat"))
    return obj


# --------------------------------------------------------------------- planets

def build_planet_ice():
    reset_scene()
    ocean = [(0.0, hex_color("#020816")), (0.5, hex_color("#05143a")), (1.0, hex_color("#0b2a62"))]
    land = [(0.0, hex_color("#0a2c56")), (1.0, hex_color("#2a6a9c"))]

    def height(n):
        return fbm(n * 2.2, 6, (3.1, 1.7, 8.2))

    def color(n):
        h = height(n)
        c = ramp(land, (h - 0.02) * 3.0) if h > 0.02 else ramp(ocean, (h + 0.35) * 1.8)
        return lerp3(c, hex_color("#3d78a6"), max(0.0, (abs(n.z) - 0.78) / 0.15))

    planet = painted_sphere("PlanetIce", 60.0, 6, color, lambda n: max(height(n), 0.02) * 0.016)
    export_glb([planet], "planet_ice.glb")
    preview([planet], "planet_ice.png", distance=150)


def build_planet_gas():
    reset_scene()
    bands = [(0.0, hex_color("#080418")), (0.4, hex_color("#160c3c")),
             (0.7, hex_color("#2a1766")), (1.0, hex_color("#432792"))]

    def color(n):
        warp = fbm(n * 3.0, 5, (1.0, 5.0, 2.0)) * 0.35
        t = math.sin((n.z + warp) * 11.0) * 0.5 + 0.5
        t = t * 0.8 + fbm(n * 6.0, 4, (9, 9, 9)) * 0.18
        storm = Vector((n.x - 0.7, n.y + 0.3, n.z + 0.25)).length
        return lerp3(ramp(bands, t), hex_color("#7a52d8"), max(0.0, 1.0 - storm * 6.5))

    planet = painted_sphere("PlanetGas", 100.0, 6, color)
    export_glb([planet], "planet_gas.glb")
    preview([planet], "planet_gas.png", distance=250)


def build_planet_lava():
    reset_scene()
    rock = [(0.0, hex_color("#0f0305")), (0.5, hex_color("#240709")), (1.0, hex_color("#42110e"))]

    def color(n):
        base = ramp(rock, fbm(n * 3.0, 5, (2.2, 6.1, 1.3)) * 0.9 + 0.5)
        crack = abs(fbm(n * 4.0, 5, (7.7, 1.9, 4.4)))
        glow = max(0.0, 1.0 - crack / 0.06)
        return lerp3(base, hex_color("#ff7a1c"), glow)

    planet = painted_sphere("PlanetLava", 45.0, 6, color, lambda n: fbm(n * 5.0, 4) * 0.02)
    export_glb([planet], "planet_lava.glb")
    preview([planet], "planet_lava.png", distance=120)


def build_planet_green():
    reset_scene()
    forest = [(0.0, hex_color("#021611")), (0.5, hex_color("#053226")), (1.0, hex_color("#0d5e42"))]

    def color(n):
        c = ramp(forest, fbm(n * 2.6, 6, (5.0, 2.0, 9.0)) * 0.9 + 0.5)
        clouds = max(0.0, fbm(n * 5.0, 5, (1.0, 8.0, 3.0)) - 0.12) * 2.2
        return lerp3(c, hex_color("#6fc9a4"), min(clouds, 0.55))

    planet = painted_sphere("PlanetGreen", 35.0, 6, color)
    export_glb([planet], "planet_green.glb")
    preview([planet], "planet_green.png", distance=100)


def build_planet_ringed():
    reset_scene()
    bands = [(0.0, hex_color("#150f07")), (0.5, hex_color("#35260f")), (1.0, hex_color("#664a26"))]

    def color(n):
        t = math.sin((n.z + fbm(n * 2.5, 4, (3, 3, 3)) * 0.12) * 14.0) * 0.5 + 0.5
        return ramp(bands, t * 0.85 + 0.08)

    planet = painted_sphere("PlanetRinged", 70.0, 6, color)

    # Concentric ring bands with gaps between them.
    bm = bmesh.new()
    rng = random.Random(4)
    edges = [(1.35, 1.5), (1.55, 1.78), (1.83, 1.92), (1.97, 2.2), (2.28, 2.38)]
    ring_colors = ["#3a3f52", "#524a44", "#2a3040", "#5d5448", "#343a4a"]
    ring_objs = []
    for (a, b), col in zip(edges, ring_colors):
        bm = bmesh.new()
        annulus(bm, 70.0 * a, 70.0 * b, segments=96)
        mesh = bpy.data.meshes.new("ring")
        bm.to_mesh(mesh)
        bm.free()
        tint = hex_color(col)
        paint_mesh(mesh, lambda co, tint=tint: lerp3(tint, (0.8, 0.8, 0.85), rng.random() * 0.12))
        obj = bpy.data.objects.new("Ring", mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(vertex_color_material("ring_mat"))
        ring_objs.append(obj)
    # Tilt the planet and ring plane so the ring reads as an ellipse from the side.
    tilt = (math.radians(28), math.radians(-18), 0.0)
    for obj in [planet] + ring_objs:
        obj.rotation_euler = tilt
    export_glb([planet] + ring_objs, "planet_ringed.glb")
    preview([planet] + ring_objs, "planet_ringed.png", rotation_deg=(90, 0, 0), distance=420)


def build_moon():
    reset_scene()
    rock = [(0.0, hex_color("#161a26")), (1.0, hex_color("#5a6580"))]

    def craters(n):
        total = 0.0
        for c in ((0.6, 0.3, 0.5), (-0.5, 0.7, 0.2), (0.1, -0.8, 0.4), (-0.7, -0.2, -0.5)):
            d = (n - Vector(c).normalized()).length
            if d < 0.35:
                total -= (1 - d / 0.35) ** 0.5 * 0.6
            elif d < 0.42:
                total += (1 - (d - 0.35) / 0.07) * 0.2
        return total

    def color(n):
        return ramp(rock, 0.4 + fbm(n * 4.0, 5, (4, 4, 4)) * 0.5 + craters(n) * 0.25)

    moon = painted_sphere("Moon", 18.0, 5, color, lambda n: craters(n) * 0.04 + fbm(n * 5.0, 4) * 0.02)
    export_glb([moon], "moon.glb")
    preview([moon], "moon.png", distance=50)


# ------------------------------------------------------------------- asteroids

def build_asteroid(name, seed, radius, stretch):
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    off = Vector((rnd.uniform(0, 50), rnd.uniform(0, 50), rnd.uniform(0, 50)))
    for v in bm.verts:
        n = v.co.normalized()
        r = 1.0 + noise.fractal(n * 1.6 + off, 0.5, 2.0, 4) * 0.55 + rnd.uniform(-0.06, 0.06)
        v.co = Vector((n.x * r * stretch[0], n.y * r * stretch[1], n.z * r * stretch[2])) * radius
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    def color(co):
        shade = 0.5 + noise.fractal(co * 0.15 + off, 0.5, 2.0, 3) * 0.7
        return lerp3(hex_color("#14121c"), hex_color("#6b6470"), shade)

    paint_mesh(mesh, color)
    for p in mesh.polygons:
        p.use_smooth = False
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(vertex_color_material(name + "_mat", roughness=0.95))
    return obj


def build_asteroids():
    specs = [("asteroid_a", 11, 7.0, (1.0, 0.85, 0.8)),
             ("asteroid_b", 23, 6.0, (1.3, 0.8, 0.9)),
             ("asteroid_c", 37, 8.0, (0.9, 1.0, 0.75))]
    for name, seed, radius, stretch in specs:
        reset_scene()
        rock = build_asteroid(name, seed, radius, stretch)
        export_glb([rock], name + ".glb")
        preview([rock], name + ".png", distance=26)


# ---------------------------------------------------------------------- debris

def build_satellite():
    reset_scene()
    foil = make_material("foil_gold", hex_color("#b8902a"), metallic=0.8, roughness=0.35)
    panel = make_material("solar_blue", hex_color("#17306e"), metallic=0.5, roughness=0.25,
                          emission=hex_color("#1d4fb8"), emission_strength=0.35)
    steel = make_material("steel", hex_color("#8a8e9a"), metallic=0.7, roughness=0.4)
    blink = make_material("blink_red", hex_color("#ff3b3b"), roughness=0.3,
                          emission=hex_color("#ff3b3b"), emission_strength=6.0)
    objs = []
    bm = bmesh.new()
    box(bm, (7, 6, 6))
    box(bm, (7.6, 3.0, 0.5), loc=(0, 0, 3.0))
    objs.append(finish(bm, "Body", foil, smooth=False))
    bm = bmesh.new()
    for side in (1, -1):
        box(bm, (9, 12, 0.35), loc=(0, side * 12.0, 0))
        box(bm, (0.8, 6, 0.6), loc=(0, side * 6.0, 0))
    objs.append(finish(bm, "Panels", panel, smooth=False))
    bm = bmesh.new()
    cone(bm, 0.0, 3.2, 1.8, loc=(0, 0, 4.2), segs=14)
    cone(bm, 0.25, 0.25, 6.0, loc=(2.5, 0, 6.0), segs=6)
    box(bm, (0.5, 0.5, 2.5), loc=(0, 0, 3.4))
    objs.append(finish(bm, "Dish", steel, smooth=True))
    bm = bmesh.new()
    sphere(bm, 0.5, loc=(2.5, 0, 9.2), segs=8, rings=6)
    objs.append(finish(bm, "Beacon", blink, smooth=True))
    export_glb(objs, "debris_satellite.glb")
    preview(objs, "debris_satellite.png", rotation_deg=(70, 0, 30), distance=40)


def build_panel():
    reset_scene()
    panel = make_material("solar_blue", hex_color("#17306e"), metallic=0.5, roughness=0.25,
                          emission=hex_color("#1d4fb8"), emission_strength=0.3)
    frame = make_material("frame_grey", hex_color("#6a6e7a"), metallic=0.7, roughness=0.45)
    bm = bmesh.new()
    prism_xz(bm, [(-9, -3), (9, -3), (9, 1.5), (3.5, 3.8), (-1, 1.2), (-9, 3)], -0.2, 0.2)
    p = finish(bm, "BrokenPanel", panel, smooth=False)
    bm = bmesh.new()
    box(bm, (18.5, 0.5, 0.5), loc=(0, 0, -3.2))
    box(bm, (0.5, 0.5, 6.4), loc=(-9, 0, 0))
    box(bm, (0.4, 0.4, 5.0), loc=(0, 0, 0), rot_deg=(0, 25, 0))
    f = finish(bm, "Frame", frame, smooth=False)
    export_glb([p, f], "debris_panel.glb")
    preview([p, f], "debris_panel.png", rotation_deg=(90, 0, 0), distance=26)


def build_pod():
    reset_scene()
    hull = make_material("pod_white", hex_color("#d8dce6"), metallic=0.3, roughness=0.45)
    stripe = make_material("pod_orange", hex_color("#e8580c"), metallic=0.2, roughness=0.45)
    window = make_material("pod_window", hex_color("#4fc3ff"), roughness=0.1,
                           emission=hex_color("#4fc3ff"), emission_strength=2.5)
    dark = make_material("pod_dark", hex_color("#25262e"), metallic=0.6, roughness=0.5)
    bm = bmesh.new()
    loft(bm, [(-7, 2.4, 2.4, 2.4), (-4, 3.4, 3.4, 3.4), (2, 3.6, 3.6, 3.6), (6, 2.4, 2.4, 2.4), (8, 0, 0.5, 0.5)], sides=12)
    h = finish(bm, "Hull", hull, smooth=True)
    bm = bmesh.new()
    loft(bm, [(-5.2, 3.45, 3.45, 3.45), (-4.2, 3.5, 3.5, 3.5), (-3.4, 3.5, 3.5, 3.5), (-2.6, 3.45, 3.45, 3.45)], sides=12)
    s = finish(bm, "Stripe", stripe, smooth=True)
    bm = bmesh.new()
    sphere(bm, 1.0, loc=(3.2, 0, 2.6), scale=(1.8, 1.2, 1.1), segs=10, rings=6)
    w = finish(bm, "Window", window, smooth=True)
    bm = bmesh.new()
    cone(bm, 2.0, 1.6, 1.4, loc=(-7.6, 0, 0), rot_deg=along_x(), segs=10)
    d = finish(bm, "Nozzle", dark, smooth=True)
    export_glb([h, s, w, d], "debris_pod.glb")
    preview([h, s, w, d], "debris_pod.png", rotation_deg=(75, 0, 20), distance=26)


def build_crate():
    reset_scene()
    shell = make_material("crate_rust", hex_color("#7a3b22"), metallic=0.5, roughness=0.65)
    rib = make_material("crate_dark", hex_color("#2c2a30"), metallic=0.6, roughness=0.55)
    mark = make_material("crate_mark", hex_color("#ffb21a"), roughness=0.5,
                         emission=hex_color("#ffb21a"), emission_strength=0.8)
    bm = bmesh.new()
    box(bm, (14, 6, 6))
    c = finish(bm, "Container", shell, smooth=False)
    bm = bmesh.new()
    for x in range(-6, 7, 3):
        box(bm, (0.7, 6.4, 6.4), loc=(x, 0, 0))
    box(bm, (14.4, 6.4, 0.7), loc=(0, 0, 3.0))
    box(bm, (14.4, 6.4, 0.7), loc=(0, 0, -3.0))
    r = finish(bm, "Ribs", rib, smooth=False)
    bm = bmesh.new()
    box(bm, (3.0, 0.2, 1.2), loc=(2.5, -3.05, 0.5))
    m = finish(bm, "Marking", mark, smooth=False)
    export_glb([c, r, m], "debris_crate.glb")
    preview([c, r, m], "debris_crate.png", rotation_deg=(70, 0, 30), distance=30)


def build_hull_chunk():
    reset_scene()
    plate = make_material("gunmetal", hex_color("#3a3e4a"), metallic=0.75, roughness=0.45)
    edge = make_material("torn_edge", hex_color("#e0541a"), roughness=0.5,
                         emission=hex_color("#ff5a14"), emission_strength=1.2)
    rnd = random.Random(8)
    bm = bmesh.new()
    prism_xz(bm, [(-9, -4), (7, -5), (11, 0), (5, 5), (-2, 4), (-8, 6), (-12, 1)], -0.6, 0.6)
    box(bm, (16, 0.8, 0.8), loc=(0, 0.9, 1.5), rot_deg=(0, 8, 0))
    box(bm, (0.8, 0.8, 9), loc=(-4, 0.9, 0), rot_deg=(0, 0, 10))
    box(bm, (0.8, 0.8, 8), loc=(3, -0.9, -0.5), rot_deg=(0, 12, 0))
    p = finish(bm, "Plate", plate, smooth=False)
    bm = bmesh.new()
    prism_xz(bm, [(11, 0), (13, 1.5), (12, -2), (10.6, -1.2)], -0.4, 0.4)
    prism_xz(bm, [(-12, 1), (-13.6, 2.4), (-14, -0.4)], -0.4, 0.4)
    e = finish(bm, "TornEdge", edge, smooth=False)
    export_glb([p, e], "debris_hull.glb")
    preview([p, e], "debris_hull.png", rotation_deg=(80, 0, 20), distance=34)


def build_shards():
    reset_scene()
    crystal = make_material("crystal_cyan", hex_color("#35b8e8"), roughness=0.1,
                            emission=hex_color("#3fd0ff"), emission_strength=2.2)
    violet = make_material("crystal_violet", hex_color("#8a4fe0"), roughness=0.1,
                           emission=hex_color("#a066ff"), emission_strength=2.0)
    rock = make_material("crystal_rock", hex_color("#22222c"), metallic=0.3, roughness=0.8)
    bm = bmesh.new()
    icosphere(bm, 1.0, loc=(0, 0, -1.0), scale=(4.5, 4.0, 2.6), subdivisions=1)
    base = finish(bm, "Base", rock, smooth=False)
    specs = [((0, 0, 2.5), (8, 5, 0), 1.5, 8.0), ((2.5, 1, 1.6), (50, 20, 5), 1.1, 6.0),
             ((-2.4, -1, 1.4), (-45, 30, -10), 1.2, 6.5), ((0.6, 2.4, 1.2), (30, -50, 40), 0.9, 5.0),
             ((-0.8, -2.5, 1.0), (-30, -35, 30), 0.9, 4.6)]
    cyan_bm, vio_bm = bmesh.new(), bmesh.new()
    for i, (loc, rot, rad, length) in enumerate(specs):
        target = cyan_bm if i % 3 != 2 else vio_bm
        cone(target, rad, 0.0, length, loc=loc, rot_deg=rot, segs=5)
    c = finish(cyan_bm, "ShardsCyan", crystal, smooth=False)
    v = finish(vio_bm, "ShardsViolet", violet, smooth=False)
    export_glb([base, c, v], "debris_shards.glb")
    preview([base, c, v], "debris_shards.png", rotation_deg=(80, 0, 20), distance=24)


if __name__ == "__main__":
    for step in (build_planet_ice, build_planet_gas, build_planet_lava, build_planet_green,
                 build_planet_ringed, build_moon, build_asteroids, build_satellite, build_panel,
                 build_pod, build_crate, build_hull_chunk, build_shards):
        step()
