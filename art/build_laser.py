"""Plasma lance projectile: white-hot core, blue halo, three energy rings (spun in
Godot via the object named "Rings") and trailing wisps.
Run: blender -b -P art/build_laser.py"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bmesh
import bpy
from blender_common import *  # noqa: F401,F403
from detail import render_preview


def build():
    reset_scene()
    core_mat = make_material("lance_core", hex_color("#ffffff"), roughness=0.3,
                             emission=hex_color("#ffffff"), emission_strength=10.0)
    halo_mat = make_material("lance_halo", hex_color("#4aa8ec"), roughness=0.3,
                             emission=hex_color("#3fa6ff"), emission_strength=3.5)
    ring_mat = make_material("lance_rings", hex_color("#9be4ff"), roughness=0.3,
                             emission=hex_color("#6fd8ff"), emission_strength=6.0)
    wisp_mat = make_material("lance_wisps", hex_color("#3d8ee0"), roughness=0.3,
                             emission=hex_color("#3d8ee0"), emission_strength=3.0)

    objs = []
    bm = bmesh.new()
    loft(bm, [(-7.5, 0, 0.1, 0.1), (-5.5, 0.5, 0.5, 0.5), (-1, 0.95, 0.95, 0.95), (5, 1.0, 1.0, 1.0),
              (8.5, 0.6, 0.6, 0.6), (10.5, 0, 0.1, 0.1)], sides=10)
    objs.append(finish(bm, "Core", core_mat, smooth=True))

    bm = bmesh.new()
    loft(bm, [(-9.0, 0, 0.1, 0.1), (-6.5, 1.0, 1.0, 1.0), (-1, 1.8, 1.8, 1.8), (5, 1.9, 1.9, 1.9),
              (9, 1.2, 1.2, 1.2), (11.0, 0, 0.1, 0.1)], sides=12)
    objs.append(finish(bm, "Halo", halo_mat, smooth=True))

    bm = bmesh.new()
    for x, major in ((1.0, 2.9), (4.5, 2.5), (7.8, 2.0)):
        torus(bm, major, 0.2, loc=(x, 0, 0), rot_deg=(0, 90, 0), major_segs=28, minor_segs=6)
    objs.append(finish(bm, "Rings", ring_mat, smooth=True))

    bm = bmesh.new()
    for a in (0, 120, 240):
        r = math.radians(a)
        cone(bm, 0.5, 0.0, 10.0, loc=(-9.5, math.cos(r) * 1.1, math.sin(r) * 1.1), rot_deg=(0, -90, 0), segs=6)
    objs.append(finish(bm, "Wisps", wisp_mat, smooth=True))

    export_glb(objs, "laser.glb")
    render_preview("laser.png", rotation_deg=(90, 0, 0), distance=30, samples=32)


if __name__ == "__main__":
    build()
