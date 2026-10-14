"""Player ship, modelled after the pink/cyan top-down reference art.
Run: blender -b -P art/build_player.py

Built in design space: nose +X, wings spread along Y, dorsal side +Z (a top-down
view). On export the whole ship is turned 90 degrees about X so its dorsal side
faces the game camera, which is how the reference reads: nose pointing right,
wings up and down."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bmesh
import bpy
from blender_common import *  # noqa: F401,F403
from detail import *  # noqa: F401,F403

S = 0.0198  # reference pixels -> game units (ship is ~32 units long)


def P(xp, yp):
    """Reference-image pixel (nose pointing down in the image) -> design-space (x, y)."""
    return ((yp - 1050) * S, (xp - 730) * S)


def poly(points):
    return [P(x, y) for x, y in points]


def mirror(points):
    return [(x, -y) for x, y in reversed(points)]


def loft_at(bm, stations, y0=0.0, z0=0.0, sides=12):
    before = set(bm.verts)
    loft(bm, stations, sides=sides)
    moved = [v for v in bm.verts if v not in before]
    bmesh.ops.translate(bm, vec=(0.0, y0, z0), verts=moved)


def build():
    reset_scene()
    kinds = {
        "pink": dict(base_hex="#e468b4", metallic=0.1, roughness=0.42, seam=0.5, dirt=0.15, scratch=0.25),
        "pinkd": dict(base_hex="#b84a98", metallic=0.1, roughness=0.45, seam=0.5, dirt=0.2, scratch=0.25),
        "cyan": dict(base_hex="#34b4ec", metallic=0.12, roughness=0.38, seam=0.5, dirt=0.15, scratch=0.25),
        "slate": dict(base_hex="#7476a6", metallic=0.2, roughness=0.45, seam=0.55, dirt=0.2, scratch=0.3),
        "char": dict(base_hex="#383a52", metallic=0.35, roughness=0.5, seam=0.55, dirt=0.25, scratch=0.35),
    }
    counter = {"n": 0}

    def mat(kind):
        counter["n"] += 1
        return panel_material(f"{kind}_{counter['n']}", **kinds[kind])

    glass_mat = make_material("canopy_glass", hex_color("#1fb4c6"), metallic=0.0, roughness=0.04,
                              emission=hex_color("#28cfe0"), emission_strength=0.9)
    glow_mat = make_material("glow_cyan", hex_color("#8fe6ff"), roughness=0.3,
                             emission=hex_color("#4fd6ff"), emission_strength=7.0)
    lens_mat = make_material("lens_cyan", hex_color("#2fc4ff"), roughness=0.2,
                             emission=hex_color("#2fb8ff"), emission_strength=2.6)
    red_mat = make_material("accent_red", hex_color("#e5424d"), roughness=0.4,
                            emission=hex_color("#e5424d"), emission_strength=0.9)
    blue_mat = make_material("accent_blue", hex_color("#63bdf0"), roughness=0.4,
                             emission=hex_color("#63bdf0"), emission_strength=0.6)
    steel_mat = make_material("barrel_steel", hex_color("#3b3d50"), metallic=0.85, roughness=0.35)

    parts = []  # (object, bake_resolution or None)

    def add(name, material, bm, bevel=0.07, res=512, angle=35.0):
        parts.append((finish_hs(bm, name, material, bevel=bevel, angle=angle), res if "color_node" in material else None))

    # --- main hull (cyan) with the pink prow and side armour --------------------
    bm = bmesh.new()
    loft(bm, [(-11.5, 3.6, 2.2, 1.8), (-8, 4.3, 2.5, 2.0), (-3, 4.9, 2.7, 2.0), (2, 4.7, 2.7, 1.9),
              (7, 3.6, 2.3, 1.6), (11.5, 2.4, 1.9, 1.3), (14.5, 1.3, 1.5, 1.0), (16.0, 0.0, 0.9, 0.6)], sides=14)
    add("Hull", mat("cyan"), bm, bevel=0.1)

    bm = bmesh.new()
    loft(bm, [(10.6, 2.65, 2.05, 1.45), (13.0, 2.05, 1.85, 1.25), (15.0, 1.1, 1.45, 0.95), (16.2, 0.15, 0.95, 0.6)], sides=12)
    for side in (1, -1):
        loft_at(bm, [(9.0, 0.35, 3.0, 1.2), (6.0, 1.0, 3.2, 1.1), (1.0, 1.25, 3.3, 1.0),
                     (-4.0, 1.2, 3.2, 1.0), (-8.5, 0.5, 2.9, 1.2), (-9.5, 0.0, 2.6, 1.4)],
                y0=side * 3.7, sides=10)
    add("Armor", mat("pink"), bm, bevel=0.12)

    # --- canopy: dark frame, teal glass ------------------------------------------
    bm = bmesh.new()
    loft(bm, [(-5.4, 2.0, 2.85, 0.4), (-3.6, 2.8, 3.15, 0.4), (-1.4, 2.8, 3.25, 0.4),
              (0.8, 2.0, 2.95, 0.4), (2.3, 0.7, 2.25, 0.4)], sides=12)
    add("CanopyFrame", mat("char"), bm, bevel=0.06)
    bm = bmesh.new()
    loft(bm, [(-5.0, 1.6, 3.15, 2.0), (-3.5, 2.3, 3.6, 2.0), (-1.5, 2.35, 3.75, 2.0),
              (0.6, 1.5, 3.4, 2.0), (1.8, 0.4, 2.8, 2.0)], sides=14)
    add("Canopy", glass_mat, bm, bevel=0, res=None)

    # dark chevron shield ahead of the canopy, and spine vents
    bm = bmesh.new()
    prism(bm, [(2.4, -1.5), (3.8, -0.9), (4.1, 0.0), (3.8, 0.9), (2.4, 1.5)], 2.3, 3.0)
    for x in (4.9, 6.3, 10.3, 11.6):
        box(bm, (1.2, 2.2, 0.5), loc=(x, 0, 2.3))
    add("Vents", mat("char"), bm, bevel=0.05, res=256)
    bm = bmesh.new()
    for x in (4.9, 6.3, 10.3, 11.6):
        for dx in (-0.35, 0.0, 0.35):
            box(bm, (0.14, 1.9, 0.22), loc=(x + dx, 0, 2.62))
    add("VentSlats", mat("slate"), bm, bevel=0.02, res=128)

    # --- rear engine housing, nacelles and tall fins ------------------------------
    bm = bmesh.new()
    cone(bm, 3.5, 3.5, 6.2, loc=(-10.9, 0, 0.3), rot_deg=along_x(), segs=24)
    add("EngineBarrel", mat("slate"), bm, bevel=0.1)
    bm = bmesh.new()
    for x in (-13.2, -12.0, -10.8, -9.6, -8.4):
        cone(bm, 3.68, 3.68, 0.35, loc=(x, 0, 0.3), rot_deg=along_x(), segs=24)
    torus(bm, 2.7, 0.35, loc=(-14.1, 0, 0.3), rot_deg=(0, 90, 0), major_segs=28, minor_segs=8)
    box(bm, (1.8, 2.2, 0.6), loc=(-8.8, 0, 3.7))
    add("EngineRibs", mat("char"), bm, bevel=0.05, res=256)
    bm = bmesh.new()
    box(bm, (4.5, 3.4, 0.45), loc=(-11.2, 0, 3.6))
    box(bm, (1.6, 2.6, 0.45), loc=(-12.9, 0, 3.55))
    add("EnginePanels", mat("cyan"), bm, bevel=0.08, res=256)
    bm = bmesh.new()
    cone(bm, 2.45, 2.45, 0.3, loc=(-13.95, 0, 0.3), rot_deg=along_x(), segs=24)
    add("EngineGlow", glow_mat, bm, bevel=0, res=None)

    for side in (1, -1):
        bm = bmesh.new()
        cone(bm, 1.5, 1.4, 4.6, loc=(-9.6, side * 4.9, 0.0), rot_deg=along_x(), segs=14)
        add(f"Nacelle{side}", mat("pink"), bm, bevel=0.1, res=256)
        bm = bmesh.new()
        box(bm, (1.3, 2.0, 1.6), loc=(-12.1, side * 4.9, 0.0))
        cone(bm, 0.8, 0.8, 0.5, loc=(-12.8, side * 4.9, 0.0), rot_deg=along_x(), segs=10)
        add(f"NacelleMouth{side}", mat("char"), bm, bevel=0.05, res=128)
        bm = bmesh.new()
        prism_xz(bm, [(-9.8, 0.4), (-15.8, 0.9), (-15.8, 3.2), (-11.0, 2.9)], side * 4.45 - 0.45, side * 4.45 + 0.45)
        add(f"TailFin{side}", mat("cyan"), bm, bevel=0.06, res=256)
        bm = bmesh.new()
        box(bm, (1.8, 1.2, 0.9), loc=(-10.6, side * 4.45, 0.9))
        add(f"FinBase{side}", mat("pink"), bm, bevel=0.1, res=128)

    # --- wings -----------------------------------------------------------------------
    wing = poly([(960, 1300), (1150, 1130), (1285, 1045), (1310, 935), (1225, 790), (965, 660)])
    flap = poly([(1255, 890), (1215, 785), (1000, 660), (965, 690), (965, 830), (1130, 900)])
    stripes_blue = [poly([(1010, 985), (1060, 962), (1200, 952), (1150, 975)]),
                    poly([(1130, 1005), (1180, 990), (1260, 990), (1215, 1005)])]
    stripe_red = poly([(1065, 935), (1105, 918), (1180, 918), (1140, 938)])
    for side in (1, -1):
        sgn = (lambda pts: pts) if side > 0 else mirror
        bm = bmesh.new()
        prism(bm, sgn(wing), 0.3, 1.5)
        add(f"Wing{side}", mat("pink"), bm, bevel=0.1)
        bm = bmesh.new()
        prism(bm, sgn(flap), 1.5, 2.0)
        add(f"WingFlap{side}", mat("slate"), bm, bevel=0.08)
        bm = bmesh.new()
        for pts in stripes_blue:
            prism(bm, sgn(pts), 1.5, 1.58)
        add(f"WingStripeBlue{side}", blue_mat, bm, bevel=0, res=None)
        bm = bmesh.new()
        prism(bm, sgn(stripe_red), 1.5, 1.58)
        prism(bm, sgn(poly([(1060, 835), (1100, 800), (1160, 835), (1120, 865)])), 2.0, 2.08)
        add(f"WingStripeRed{side}", red_mat, bm, bevel=0, res=None)

        # leading-edge light housings with glowing lenses, wingtip caps, wing cannons
        bm = bmesh.new()
        cx, cy = P(1160, 1085)
        box(bm, (2.8, 5.0, 1.5), loc=(cx, side * cy, 0.9), rot_deg=(0, 0, -25 * side))
        add(f"LightHousing{side}", mat("pinkd"), bm, bevel=0.1, res=256)
        bm = bmesh.new()
        for xp, yp in ((1245, 1055), (1155, 1080), (1085, 1100)):
            lx, ly = P(xp, yp)
            sphere(bm, 1.0, loc=(lx, side * ly, 1.7), scale=(0.55, 0.95, 0.35), segs=10, rings=6)
        add(f"WingLights{side}", lens_mat, bm, bevel=0, res=None)
        bm = bmesh.new()
        cone(bm, 0.7, 0.7, 4.4, loc=(-1.6, side * 11.7, 0.9), rot_deg=along_x(), segs=12)
        sphere(bm, 0.7, loc=(-3.8, side * 11.7, 0.9), segs=10, rings=6)
        sphere(bm, 0.7, loc=(0.6, side * 11.7, 0.9), segs=10, rings=6)
        add(f"WingtipCap{side}", mat("char"), bm, bevel=0.05, res=128)
        bm = bmesh.new()
        box(bm, (1.5, 1.5, 1.1), loc=(3.8, side * 6.4, 0.4))
        add(f"CannonHousing{side}", mat("pinkd"), bm, bevel=0.1, res=128)
        bm = bmesh.new()
        cone(bm, 0.45, 0.45, 3.8, loc=(6.4, side * 6.4, 0.4), rot_deg=along_x(), segs=10)
        cone(bm, 0.6, 0.6, 0.35, loc=(8.2, side * 6.4, 0.4), rot_deg=along_x(), segs=10)
        add(f"WingCannon{side}", steel_mat, bm, bevel=0.03, res=None)

    # --- nose cannons and prow spikes -----------------------------------------------
    bm = bmesh.new()
    for side in (1, -1):
        cone(bm, 0.36, 0.36, 3.2, loc=(16.1, side * 0.95, 0.9), rot_deg=along_x(), segs=10)
        cone(bm, 0.5, 0.5, 0.35, loc=(17.6, side * 0.95, 0.9), rot_deg=along_x(), segs=10)
        prism(bm, [(14.4, side * 0.4), (13.5, side * 6.8), (13.1, side * 6.8), (13.9, side * 0.5)], 0.7, 1.0)
    add("NoseGuns", steel_mat, bm, bevel=0.03, res=None)

    # --- baking, parenting and export -------------------------------------------------
    for obj, res in parts:
        if res:
            bake_albedo(obj, res=res)

    objs = [o for o, _ in parts]
    render_preview("player_top.png", rotation_deg=(0, 0, 0), distance=38, samples=48)

    root = bpy.data.objects.new("ShipRoot", None)
    bpy.context.scene.collection.objects.link(root)
    root.rotation_euler = (math.radians(90), 0, 0)
    for obj in objs:
        obj.parent = root
    export_glb([root] + objs, "player_ship.glb")


if __name__ == "__main__":
    build()
