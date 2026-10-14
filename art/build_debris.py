"""Detailed space debris: satellite, broken solar panel, escape pod, cargo container,
hull chunk and crystal cluster. Run: blender -b -P art/build_debris.py"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bmesh
import bpy
from blender_common import *  # noqa: F401,F403
from detail import *  # noqa: F401,F403


class Kit:
    """Collects parts for one model and bakes/exports them together."""

    def __init__(self, name):
        reset_scene()
        self.name = name
        self.parts = []
        self.n = 0

    def panel(self, **kw):
        self.n += 1
        return panel_material(f"{self.name}_m{self.n}", **kw)

    def add(self, name, material, bm, bevel=0.06, res=256, angle=35.0):
        baked = "color_node" in material.keys()
        self.parts.append((finish_hs(bm, name, material, bevel=bevel, angle=angle), res if baked else None))

    def finish(self, preview_rot=(65, 0, 30), distance=34, export_name=None):
        for obj, res in self.parts:
            if res:
                bake_albedo(obj, res=res)
        objs = [o for o, _ in self.parts]
        render_preview(f"{self.name}.png", rotation_deg=preview_rot, distance=distance, samples=40)
        export_glb(objs, export_name or f"{self.name}.glb")


def solar_grid(bm, center, cols, rows, cell, gap, thickness=0.18, axis="y"):
    """Grid of thin solar cells; `cols` along the arm (y or x), `rows` across."""
    cw, ch = cell
    total_c = cols * cw + (cols - 1) * gap
    total_r = rows * ch + (rows - 1) * gap
    for i in range(cols):
        for j in range(rows):
            u = -total_c / 2 + cw / 2 + i * (cw + gap)
            v = -total_r / 2 + ch / 2 + j * (ch + gap)
            if axis == "y":
                box(bm, (ch, cw, thickness), loc=(center[0] + v, center[1] + u, center[2]))
            else:
                box(bm, (cw, ch, thickness), loc=(center[0] + u, center[1] + v, center[2]))


def build_satellite():
    k = Kit("debris_satellite")
    glow_red = make_material("beacon", hex_color("#ff3b3b"), roughness=0.3,
                             emission=hex_color("#ff3b3b"), emission_strength=7.0)
    dish_glow = make_material("dish_lamp", hex_color("#7fe0ff"), roughness=0.3,
                              emission=hex_color("#5fd0ff"), emission_strength=3.0)

    bm = bmesh.new()
    box(bm, (7.0, 6.0, 6.0))
    box(bm, (7.5, 3.2, 0.5), loc=(0, 0, 3.1))
    box(bm, (7.5, 3.2, 0.5), loc=(0, 0, -3.1))
    box(bm, (1.0, 6.3, 6.3), loc=(-3.0, 0, 0))
    k.add("Body", k.panel(base_hex="#b8902a", metallic=0.35, roughness=0.4, seam=0.65, dirt=0.35, scratch=0.4,
                          panel_scale=0.7), bm, bevel=0.1, res=512)

    bm = bmesh.new()
    for side in (1, -1):
        box(bm, (0.5, 5.0, 0.5), loc=(0, side * 5.0, 0))
        box(bm, (0.35, 13.0, 0.35), loc=(3.9, side * 11.5, 0), rot_deg=(0, 0, 0))
        box(bm, (0.35, 13.0, 0.35), loc=(-3.9, side * 11.5, 0))
        for y in (6.0, 9.5, 13.0, 16.5):
            box(bm, (7.8, 0.3, 0.3), loc=(0, side * y, 0))
    k.add("Truss", k.panel(base_hex="#8a8e9a", metallic=0.3, roughness=0.45, seam=0.5, dirt=0.3, scratch=0.4),
          bm, bevel=0.04, res=128)

    bm = bmesh.new()
    for side in (1, -1):
        solar_grid(bm, (0, side * 11.5, 0), cols=6, rows=3, cell=(1.8, 2.2), gap=0.18)
    k.add("SolarCells", k.panel(base_hex="#1b3f9a", metallic=0.3, roughness=0.2, seam=0.5, dirt=0.15, scratch=0.45,
                                panel_scale=0.25), bm, bevel=0.02, res=512)

    bm = bmesh.new()
    cone(bm, 0.2, 3.4, 1.9, loc=(0, 0, 4.6), segs=20)
    cone(bm, 0.18, 0.18, 4.5, loc=(0, 0, 3.6), segs=8)
    for a in range(0, 360, 45):
        r = math.radians(a)
        box(bm, (0.12, 3.0, 0.1), loc=(math.cos(r) * 1.7, math.sin(r) * 1.7, 4.65),
            rot_deg=(0, 0, a))
    cone(bm, 0.14, 0.14, 4.0, loc=(2.8, 0, 7.0), segs=6)
    for sx in (1, -1):
        for sy in (1, -1):
            cone(bm, 0.35, 0.28, 0.9, loc=(sx * 3.7, sy * 3.1, 2.2), rot_deg=(0, 90 if sx > 0 else -90, 0), segs=8)
    k.add("Dish", k.panel(base_hex="#c0c4d0", metallic=0.4, roughness=0.35, seam=0.45, dirt=0.25, scratch=0.35),
          bm, bevel=0.03, res=256)

    bm = bmesh.new()
    sphere(bm, 0.45, loc=(2.8, 0, 9.1), segs=8, rings=6)
    k.add("Beacon", glow_red, bm, bevel=0)
    bm = bmesh.new()
    for y in (-1.2, 0.0, 1.2):
        box(bm, (0.5, 0.45, 0.18), loc=(3.0, y, 3.45))
    k.add("StatusLights", dish_glow, bm, bevel=0)
    k.finish(preview_rot=(60, 0, 25), distance=44)


def build_panel():
    k = Kit("debris_panel")
    bm = bmesh.new()
    cells = []
    # A solar panel with a torn corner: cells missing where the tear is.
    for i in range(7):
        for j in range(3):
            x, y = -9.0 + i * 2.7, -3.4 + j * 2.35
            if i >= 5 and j == 2:
                continue
            box(bm, (2.4, 2.1, 0.16), loc=(x + 1.2, y, 0.0), rot_deg=(0, 0, 0))
    box(bm, (2.0, 1.4, 0.16), loc=(8.4, 1.0, 0.0), rot_deg=(0, 0, 18))
    k.add("Cells", k.panel(base_hex="#1b3f9a", metallic=0.3, roughness=0.2, seam=0.5, dirt=0.25, scratch=0.5,
                           panel_scale=0.25), bm, bevel=0.02, res=512)
    bm = bmesh.new()
    box(bm, (20.5, 0.4, 0.4), loc=(1.0, -4.9, 0.0))
    box(bm, (20.5, 0.4, 0.4), loc=(1.0, 3.1, 0.0))
    box(bm, (0.4, 8.4, 0.4), loc=(-10.2, -0.9, 0.0))
    for x in (-5.0, 0.0, 5.0):
        box(bm, (0.3, 8.0, 0.3), loc=(x, -0.9, -0.15))
    box(bm, (5.0, 0.35, 0.35), loc=(10.5, 3.1, 0.0), rot_deg=(0, 0, 30))
    cone(bm, 0.5, 0.5, 5.0, loc=(-10.2, -0.9, -2.0), rot_deg=(90, 0, 0), segs=8)
    k.add("Frame", k.panel(base_hex="#7d808c", metallic=0.4, roughness=0.5, seam=0.5, dirt=0.4, scratch=0.45),
          bm, bevel=0.04, res=256)
    k.finish(preview_rot=(60, 0, 20), distance=32)


def build_pod():
    k = Kit("debris_pod")
    window = make_material("pod_window", hex_color("#4fc3ff"), roughness=0.08,
                           emission=hex_color("#4fc3ff"), emission_strength=2.2)
    lamp = make_material("pod_lamp", hex_color("#ffb427"), roughness=0.4,
                         emission=hex_color("#ffa51a"), emission_strength=3.5)
    bm = bmesh.new()
    loft(bm, [(-7.0, 2.3, 2.3, 2.3), (-4.5, 3.3, 3.3, 3.3), (1.0, 3.7, 3.7, 3.7), (5.5, 2.8, 2.8, 2.8),
              (8.2, 1.2, 1.2, 1.2), (9.0, 0, 0.4, 0.4)], sides=16)
    k.add("Hull", k.panel(base_hex="#d9dce6", metallic=0.15, roughness=0.45, seam=0.5, dirt=0.3, scratch=0.35,
                          panel_scale=0.6), bm, bevel=0.06, res=512)
    bm = bmesh.new()
    loft(bm, [(-5.5, 3.45, 3.45, 3.45), (-4.6, 3.55, 3.55, 3.55), (-3.0, 3.6, 3.6, 3.6), (-2.1, 3.5, 3.5, 3.5)], sides=16)
    loft(bm, [(3.0, 3.45, 3.45, 3.45), (3.6, 3.5, 3.5, 3.5), (4.4, 3.35, 3.35, 3.35)], sides=16)
    k.add("Stripe", k.panel(base_hex="#e8580c", metallic=0.1, roughness=0.5, seam=0.4, dirt=0.3, scratch=0.3,
                            stripe=True, accent_hex="#ffb21a"), bm, bevel=0.04, res=256)
    bm = bmesh.new()
    cone(bm, 2.4, 1.7, 1.6, loc=(-7.8, 0, 0), rot_deg=along_x(), segs=14)
    torus(bm, 1.9, 0.25, loc=(-8.7, 0, 0), rot_deg=(0, 90, 0), major_segs=20, minor_segs=6)
    for a in range(0, 360, 90):
        r = math.radians(a)
        box(bm, (1.6, 0.45, 0.45), loc=(-5.6, math.cos(r) * 3.6, math.sin(r) * 3.6), rot_deg=(a, 0, 0))
    box(bm, (1.8, 1.6, 0.35), loc=(0.5, 0, 3.75))
    cone(bm, 0.12, 0.12, 3.0, loc=(-1.0, 0, 5.2), segs=6)
    k.add("Fittings", k.panel(base_hex="#383a4c", metallic=0.35, roughness=0.5, seam=0.55, dirt=0.35, scratch=0.4),
          bm, bevel=0.04, res=256)
    bm = bmesh.new()
    sphere(bm, 1.0, loc=(3.4, 0, 2.7), scale=(1.9, 1.3, 1.2), segs=12, rings=6)
    k.add("Window", window, bm, bevel=0)
    bm = bmesh.new()
    torus(bm, 1.55, 0.2, loc=(3.4, 0, 2.55), rot_deg=(0, 0, 0), major_segs=20, minor_segs=6)
    k.add("WindowRing", k.panel(base_hex="#383a4c", metallic=0.4, roughness=0.45), bm, bevel=0, res=128)
    bm = bmesh.new()
    for x in (-0.5, 0.2, 0.9):
        box(bm, (0.35, 0.2, 0.2), loc=(x, 0, 3.8))
    k.add("PodLamps", lamp, bm, bevel=0)
    k.finish(preview_rot=(65, 0, 20), distance=30)


def build_crate():
    k = Kit("debris_crate")
    marker = make_material("crate_light", hex_color("#ffb21a"), roughness=0.5,
                           emission=hex_color("#ffb21a"), emission_strength=2.2)
    bm = bmesh.new()
    box(bm, (14.0, 6.0, 6.0))
    k.add("Container", k.panel(base_hex="#8a4226", metallic=0.3, roughness=0.65, seam=0.55, dirt=0.5, scratch=0.5,
                               panel_scale=0.5), bm, bevel=0.1, res=512)
    bm = bmesh.new()
    for x in range(-6, 7, 2):
        box(bm, (0.5, 6.25, 6.25), loc=(x, 0, 0))   # corrugation ribs
    k.add("Ribs", k.panel(base_hex="#6e3520", metallic=0.3, roughness=0.7, seam=0.5, dirt=0.5, scratch=0.5),
          bm, bevel=0.05, res=256)
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                box(bm, (1.0, 1.0, 1.0), loc=(sx * 6.7, sy * 2.8, sz * 2.8))   # corner castings
    box(bm, (0.5, 0.5, 6.5), loc=(7.2, 0.8, 0.0))
    box(bm, (0.5, 0.5, 6.5), loc=(7.2, -0.8, 0.0))
    box(bm, (0.5, 1.9, 0.4), loc=(7.3, 0, 0.4))
    k.add("Fittings", k.panel(base_hex="#2c2a30", metallic=0.4, roughness=0.55, seam=0.5, dirt=0.4, scratch=0.5),
          bm, bevel=0.05, res=256)
    bm = bmesh.new()
    box(bm, (14.1, 6.1, 0.8), loc=(0, 0, 3.0))
    k.add("HazardBand", k.panel(base_hex="#26262e", metallic=0.2, roughness=0.6, stripe=True, accent_hex="#ffb21a",
                                dirt=0.3), bm, bevel=0.02, res=256)
    bm = bmesh.new()
    for y in (-2.0, 0.0, 2.0):
        box(bm, (0.4, 0.5, 0.18), loc=(7.2, y, -2.4))
    k.add("DoorLights", marker, bm, bevel=0)
    k.finish(preview_rot=(65, 0, 30), distance=30)


def build_hull_chunk():
    k = Kit("debris_hull")
    edge = make_material("torn_edge", hex_color("#e0541a"), roughness=0.5,
                         emission=hex_color("#ff5a14"), emission_strength=2.4)
    rnd = random.Random(8)
    bm = bmesh.new()
    prism_xz(bm, [(-9, -4), (7, -5), (11, 0), (5, 5), (-2, 4), (-8, 6), (-12, 1)], -0.6, 0.6)
    prism_xz(bm, [(-6, -2), (4, -3), (8, 0), (3, 3), (-5, 3)], 0.6, 1.2)
    k.add("Plating", k.panel(base_hex="#454a5a", metallic=0.35, roughness=0.5, seam=0.7, dirt=0.5, scratch=0.5,
                             panel_scale=0.7), bm, bevel=0.08, res=512)
    bm = bmesh.new()
    box(bm, (17, 0.8, 0.8), loc=(0, 1.6, 1.0), rot_deg=(0, 8, 0))
    box(bm, (0.8, 0.8, 10), loc=(-4, 1.6, 0), rot_deg=(0, 0, 10))
    box(bm, (0.8, 0.8, 9), loc=(3, -1.6, -0.5), rot_deg=(0, 12, 0))
    for i in range(6):
        box(bm, (rnd.uniform(1.5, 3.5), 0.6, 0.6), loc=(rnd.uniform(-8, 8), rnd.uniform(-1.8, 1.8), rnd.uniform(-3, 3)),
            rot_deg=(rnd.uniform(0, 90), rnd.uniform(0, 90), rnd.uniform(0, 90)))
    cone(bm, 0.5, 0.5, 6.0, loc=(8.0, 0, 1.2), rot_deg=(0, 70, 0), segs=8)
    k.add("Girders", k.panel(base_hex="#6a6e7c", metallic=0.4, roughness=0.55, seam=0.5, dirt=0.4, scratch=0.5),
          bm, bevel=0.04, res=256)
    bm = bmesh.new()
    prism_xz(bm, [(11, 0), (13.4, 1.8), (12.4, -2.2), (10.6, -1.2)], -0.4, 0.4)
    prism_xz(bm, [(-12, 1), (-14.0, 2.6), (-14.4, -0.6)], -0.4, 0.4)
    prism_xz(bm, [(-2, 4), (0.5, 6.4), (2.5, 4.4)], -0.4, 0.4)
    k.add("TornEdge", edge, bm, bevel=0)
    k.finish(preview_rot=(75, 0, 20), distance=36)


def build_shards():
    k = Kit("debris_shards")
    cyan = make_material("crystal_cyan", hex_color("#35b8e8"), roughness=0.08,
                         emission=hex_color("#3fd0ff"), emission_strength=2.6)
    violet = make_material("crystal_violet", hex_color("#8a4fe0"), roughness=0.08,
                           emission=hex_color("#a066ff"), emission_strength=2.4)
    bm = bmesh.new()
    icosphere(bm, 1.0, loc=(0, 0, -1.0), scale=(4.8, 4.2, 2.8), subdivisions=2)
    icosphere(bm, 1.0, loc=(2.6, 1.8, -1.2), scale=(2.4, 2.0, 1.8), subdivisions=1)
    icosphere(bm, 1.0, loc=(-2.8, -1.4, -1.0), scale=(2.2, 2.2, 1.6), subdivisions=1)
    k.add("Base", k.panel(base_hex="#2a2a36", metallic=0.2, roughness=0.85, seam=0.3, dirt=0.6, scratch=0.5),
          bm, bevel=0.05, res=256, angle=30.0)
    specs = [((0, 0, 2.5), (8, 5, 0), 1.6, 9.0), ((2.6, 1.0, 1.6), (50, 20, 5), 1.15, 6.5),
             ((-2.4, -1, 1.4), (-45, 30, -10), 1.25, 7.0), ((0.6, 2.4, 1.2), (30, -50, 40), 0.95, 5.5),
             ((-0.8, -2.5, 1.0), (-30, -35, 30), 0.95, 5.0), ((3.4, -1.8, 0.6), (70, 10, -20), 0.8, 4.2),
             ((-3.4, 1.6, 0.6), (-70, 20, 25), 0.7, 3.8)]
    cyan_bm, vio_bm = bmesh.new(), bmesh.new()
    for i, (loc, rot, rad, length) in enumerate(specs):
        cone(cyan_bm if i % 3 != 2 else vio_bm, rad, 0.0, length, loc=loc, rot_deg=rot, segs=6)
    k.add("ShardsCyan", cyan, cyan_bm, bevel=0.0)
    k.add("ShardsViolet", violet, vio_bm, bevel=0.0)
    k.finish(preview_rot=(78, 0, 20), distance=26)


if __name__ == "__main__":
    for step in (build_satellite, build_panel, build_pod, build_crate, build_hull_chunk, build_shards):
        step()
