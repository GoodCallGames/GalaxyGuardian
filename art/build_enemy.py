"""Enemy fighter, modelled after the indigo stealth-fighter turnaround sheet.
Run: blender -b -P art/build_enemy.py

Design space: nose -X (enemies fly toward -X), wings spread along Y, dorsal side +Z.
On export the ship is turned 90 degrees about X so its dorsal side faces the camera."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bmesh
import bpy
from blender_common import *  # noqa: F401,F403
from detail import *  # noqa: F401,F403


def loft_at(bm, stations, y0=0.0, z0=0.0, sides=10):
    before = set(bm.verts)
    loft(bm, stations, sides=sides)
    moved = [v for v in bm.verts if v not in before]
    bmesh.ops.translate(bm, vec=(0.0, y0, z0), verts=moved)


def build():
    reset_scene()
    kinds = {
        "indigo": dict(base_hex="#454989", metallic=0.15, roughness=0.45, seam=0.55, dirt=0.25, scratch=0.3),
        "light": dict(base_hex="#6468b0", metallic=0.15, roughness=0.4, seam=0.5, dirt=0.15, scratch=0.3),
        "navy": dict(base_hex="#24284c", metallic=0.3, roughness=0.5, seam=0.55, dirt=0.3, scratch=0.3),
        "purple": dict(base_hex="#563f98", metallic=0.15, roughness=0.4, seam=0.5, dirt=0.2, scratch=0.25),
        "deep": dict(base_hex="#16182e", metallic=0.4, roughness=0.5, seam=0.6, dirt=0.3, scratch=0.3),
    }
    counter = {"n": 0}

    def mat(kind):
        counter["n"] += 1
        return panel_material(f"{kind}_{counter['n']}", **kinds[kind])

    amber = make_material("amber_glow", hex_color("#ffb427"), roughness=0.4,
                          emission=hex_color("#ffa51a"), emission_strength=3.6)
    thruster = make_material("thruster_orange", hex_color("#ff9a2a"), roughness=0.3,
                             emission=hex_color("#ff7a14"), emission_strength=6.5)
    canopy = make_material("canopy_maroon", hex_color("#8a1048"), roughness=0.05,
                           emission=hex_color("#c8206e"), emission_strength=0.9)

    parts = []

    def add(name, material, bm, bevel=0.07, res=512, angle=35.0):
        parts.append((finish_hs(bm, name, material, bevel=bevel, angle=angle),
                      res if "color_node" in material else None))

    # --- fuselage: long needle nose, blended into a broad rear -------------------
    bm = bmesh.new()
    loft(bm, [(-14.0, 0.0, 0.2, 0.2), (-11.4, 0.5, 0.45, 0.35), (-8.0, 1.0, 0.8, 0.7), (-4.6, 1.7, 1.2, 1.0),
              (-1.2, 2.6, 1.5, 1.3), (2.2, 3.3, 1.7, 1.5), (5.6, 3.6, 1.8, 1.6), (9.0, 3.4, 1.8, 1.6),
              (11.8, 2.6, 1.6, 1.4), (13.2, 1.4, 1.2, 1.0)], sides=14)
    add("Fuselage", mat("indigo"), bm, bevel=0.1)

    # lighter dorsal ridge running down the spine
    bm = bmesh.new()
    loft(bm, [(-12.5, 0.0, 0.5, 0.2), (-9.0, 0.45, 1.0, 0.5), (-5.0, 0.8, 1.55, 0.7),
              (-1.5, 1.0, 1.85, 0.8), (3.0, 1.05, 2.0, 0.9), (5.6, 0.6, 1.95, 1.0), (6.6, 0.0, 1.8, 1.2)], sides=10)
    add("SpineRidge", mat("light"), bm, bevel=0.06, res=256)

    # --- canopy: maroon gem in a navy frame -----------------------------------------
    bm = bmesh.new()
    loft(bm, [(-6.2, 0.0, 1.55, 0.6), (-5.2, 0.85, 1.95, 0.6), (-3.5, 1.15, 2.3, 0.6),
              (-1.8, 1.1, 2.3, 0.6), (-0.3, 0.7, 2.0, 0.6)], sides=10)
    add("CanopyFrame", mat("deep"), bm, bevel=0.05, res=256)
    bm = bmesh.new()
    loft(bm, [(-6.0, 0.0, 1.7, 1.2), (-5.0, 0.6, 2.05, 1.2), (-3.5, 0.85, 2.4, 1.2),
              (-1.8, 0.8, 2.4, 1.2), (-0.5, 0.4, 2.1, 1.2)], sides=12)
    add("Canopy", canopy, bm, bevel=0, res=None)

    # purple cockpit rear bulge
    bm = bmesh.new()
    loft(bm, [(-0.3, 0.8, 2.0, 1.2), (1.2, 1.5, 2.3, 1.0), (3.5, 1.5, 2.2, 1.0), (4.3, 0.9, 1.9, 1.1)], sides=10)
    add("CockpitBulge", mat("purple"), bm, bevel=0.07, res=256)

    # --- rear spires: purple central dorsal fin + two thin spires ----------------------
    bm = bmesh.new()
    prism_xz(bm, [(2.2, 1.7), (5.5, 3.1), (9.5, 4.0), (13.6, 3.0), (14.4, 1.7)], -0.55, 0.55)
    prism(bm, [(3.9, -1.0), (13.8, -0.9), (14.4, 0.0), (13.8, 0.9), (3.9, 1.0)], 1.2, 1.9)
    add("DorsalFin", mat("purple"), bm, bevel=0.06)
    for side in (1, -1):
        bm = bmesh.new()
        prism_xz(bm, [(5.0, 1.7), (8.5, 2.9), (14.8, 3.4), (13.6, 1.7)], side * 2.05 - 0.28, side * 2.05 + 0.28)
        add(f"Spire{side}", mat("navy"), bm, bevel=0.04, res=256)
        bm = bmesh.new()
        for x, z in ((7.6, 2.95), (9.8, 3.1), (12.0, 3.28)):
            box(bm, (0.5, 0.42, 0.14), loc=(x, side * 2.05, z))
        add(f"SpireSlits{side}", amber, bm, bevel=0, res=None)

    # --- outboard pylons ("wings"), vents, tips -----------------------------------------
    for side in (1, -1):
        sgn = (lambda pts: pts) if side > 0 else (lambda pts: [(x, -y) for x, y in reversed(pts)])
        bm = bmesh.new()
        prism(bm, sgn([(-4.6, 5.0), (-2.0, 6.3), (1.0, 6.4), (9.5, 6.2), (12.8, 5.4), (9.5, 3.8), (1.0, 3.8), (-2.4, 4.0)]),
              -2.0, 0.4)
        add(f"Pylon{side}", mat("indigo"), bm, bevel=0.12)
        bm = bmesh.new()
        prism(bm, sgn([(-2.0, 5.0), (1.0, 5.7), (9.0, 5.5), (11.0, 5.1), (9.0, 4.4), (1.0, 4.4)]), 0.4, 0.75)
        add(f"PylonRidge{side}", mat("light"), bm, bevel=0.06, res=256)
        bm = bmesh.new()
        prism(bm, sgn([(9.6, 6.2), (14.6, 5.5), (12.0, 4.0), (9.6, 3.9)]), -1.4, 0.2)
        add(f"PylonTip{side}", mat("deep"), bm, bevel=0.06, res=256)
        bm = bmesh.new()
        box(bm, (10.0, 1.2, 0.9), loc=(4.5, side * 4.0, -0.5))
        add(f"WingStub{side}", mat("navy"), bm, bevel=0.06, res=256)
        bm = bmesh.new()
        for x in (4.6, 5.4, 6.2):
            box(bm, (0.5, 2.1, 0.2), loc=(x, side * 5.05, 0.85))
        add(f"PylonVents{side}", amber, bm, bevel=0, res=None)

        # engine nacelles under the rear fuselage, with orange vents and thrusters
        bm = bmesh.new()
        box(bm, (8.6, 1.8, 2.9), loc=(2.4, side * 2.75, -0.7))
        add(f"Nacelle{side}", mat("navy"), bm, bevel=0.1, res=256)
        bm = bmesh.new()
        cone(bm, 0.85, 0.85, 0.9, loc=(7.1, side * 2.75, -0.7), rot_deg=along_x(), segs=14)
        add(f"Nozzle{side}", mat("deep"), bm, bevel=0.04, res=128)
        bm = bmesh.new()
        cone(bm, 0.7, 0.7, 0.25, loc=(7.65, side * 2.75, -0.7), rot_deg=along_x(), segs=14)
        for x in (3.0, 4.0, 5.0):
            box(bm, (0.4, 1.2, 0.12), loc=(x, side * 2.75, 0.8))
        add(f"NacelleGlow{side}", thruster, bm, bevel=0, res=None)

    # --- belly gun pod, side light dashes ----------------------------------------------------
    bm = bmesh.new()
    box(bm, (3.4, 2.0, 1.3), loc=(-3.2, 0, -1.9))
    add("GunPod", mat("navy"), bm, bevel=0.1, res=256)
    bm = bmesh.new()
    for x in (-4.2, -3.2, -2.2):
        box(bm, (0.35, 0.5, 0.12), loc=(x, 0, -2.6))
    for side in (1, -1):
        for i in range(5):
            box(bm, (0.35, 0.12, 0.12), loc=(-2.0 - i * 0.8, side * 1.55, 1.1 - i * 0.12))
    add("AmberDashes", amber, bm, bevel=0, res=None)

    # --- bake, parent, export -------------------------------------------------------------------
    for obj, res in parts:
        if res:
            bake_albedo(obj, res=res)

    objs = [o for o, _ in parts]
    render_preview("enemy_top.png", rotation_deg=(0, 0, 0), distance=36, samples=48)

    root = bpy.data.objects.new("ShipRoot", None)
    bpy.context.scene.collection.objects.link(root)
    root.rotation_euler = (math.radians(90), 0, 0)
    for obj in objs:
        obj.parent = root
    export_glb([root] + objs, "enemy.glb")


if __name__ == "__main__":
    build()
