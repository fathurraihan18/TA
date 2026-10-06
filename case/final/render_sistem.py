"""Render sistem lengkap (Cycles). python render_sistem.py -- <mode> <out_png> [samples] [lebar] [tinggi]
mode: hero | depan | belakang | eksplode_a | eksplode_b
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sistem import *
import sistem
from bpy_extras.object_utils import world_to_camera_view

A = sys.argv[sys.argv.index("--") + 1:]
MODE, OUTP = A[0], A[1]
SAMP = int(A[2]) if len(A) > 2 else 64
RW = int(A[3]) if len(A) > 3 else 1800
RH = int(A[4]) if len(A) > 4 else 1100

import random

ALL_KEYS = ["shell", "plate", "penahan", "sekrup", "tft", "standoff", "pcb", "esp32", "ad8232", "boost", "baterai", "saklar", "gland",
            "kabel_ppg_dalam", "klip", "kabel_ppg_luar", "plug", "elektroda"]
reset()
transparent = MODE != "hero"
sc = setup_cycles((RW, RH), SAMP, transparent=transparent, world_strength=0.8)
studio_lights(0.55)
table = MODE in ("hero", "cover_depan")
build(table=table, tilt=0.0, elektroda=True)


def only(keys):
    hide([k for k in ALL_KEYS if k not in keys], True)


def anchor_pts(keys, cam, n_try=500):
    """titik permukaan yang terlihat dari kamera untuk tiap grup (ray cast), dikembalikan sebagai koordinat piksel."""
    out = {}
    deps = bpy.context.evaluated_depsgraph_get()
    rnd = random.Random(3)
    for k in keys:
        g = sistem.G[k]
        objs = [o for o in g["objs"] if not o.hide_render and o.type == "MESH"]
        if not objs: continue
        cands = []
        for o in objs:
            mw = o.matrix_world
            vs = [mw @ v.co for v in o.data.vertices]
            if len(vs) > 400: vs = rnd.sample(vs, 400)
            cands += [(p, o) for p in vs]
        allp = [c[0] for c in cands]
        cen = sum(allp, Vector()) / len(allp)
        cands.sort(key=lambda t: (t[0] - cen).length)
        best = None
        for p, o in cands[:n_try]:
            co = world_to_camera_view(sc, cam, p)
            if not (0.02 < co.x < 0.98 and 0.02 < co.y < 0.98): continue
            if cam.data.type == "ORTHO":
                d_ = -(cam.matrix_world.to_quaternion() @ Vector((0, 0, -1)))
                d_ = (cam.matrix_world.to_quaternion() @ Vector((0, 0, -1)))
                origin = p - d_ * 3000
            else:
                origin = cam.location; d_ = (p - origin).normalized()
            ok, loc, nrm, idx, hit, _m = sc.ray_cast(deps, origin, d_)
            if ok and hit is not None and hit.name in {x.name for x in objs} and (loc - p).length < 0.8:
                best = [co.x * RW, (1 - co.y) * RH]; break
        if best is None:
            c = world_to_camera_view(sc, cam, cen); best = [c.x * RW, (1 - c.y) * RH]
        out[k] = best
    return out


EXPL_A = {"plate": (0, 0, -78), "sekrup": (0, 0, -108), "penahan": (0, 0, -34), "tft": (0, 0, 72), "shell": (0, 0, 140), "saklar": (0, 0, 140), "gland": (0, 0, 140)}
EXPL_B = {"esp32": (46, 8, 44), "ad8232": (4, 50, 40), "boost": (-54, 44, 40), "baterai": (-6, -54, 36), "kabel_ppg_dalam": (-6, -10, 30)}
DIR_EXP = Vector((-0.42, 0.74, 0.55)).normalized()
info = {}

if MODE == "hero":
    add_floor(TABLE_Z - 0.02, color=(0.86, 0.86, 0.85))
    set_offsets({})
    lo, hi = bbox(); c = (lo + hi) / 2
    camera((c[0] + 10, c[1] - 380, 470), (c[0], c[1] + 5, 0), lens=42, up=(0, 1, 0))
elif MODE in ("cover_depan", "cover_belakang"):
    only(["shell", "plate", "sekrup", "saklar", "gland"] + (["penahan"] if MODE == "cover_belakang" and False else []))
    set_offsets({})
    if MODE == "cover_depan":
        add_floor(TABLE_Z - 0.02, catcher=True)
        camera((-190, 260, 230), (-5, -3, 12), lens=62, up=(0, 0, 1))
    else:
        camera((-210, 200, -290), (-3, -3, 8), lens=62, up=(0, 1, 0))
elif MODE == "eksplode_a":
    only(["shell", "plate", "penahan", "sekrup", "tft", "standoff", "pcb", "esp32", "ad8232", "boost", "baterai", "saklar", "gland", "kabel_ppg_dalam"])
    set_offsets(EXPL_A)
    c = Vector((-6, 0, 28)); cam = camera(tuple(c + DIR_EXP * 1500), tuple(c), ortho=float(os.environ.get("SCA", "360")), up=(0, 0, 1))
elif MODE == "eksplode_b":
    only(["pcb", "esp32", "ad8232", "boost", "baterai", "kabel_ppg_dalam"])
    set_offsets(EXPL_B)
    c = Vector((-6, 4, 22)); cam = camera(tuple(c + DIR_EXP * 1500), tuple(c), ortho=float(os.environ.get("SCB", "250")), up=(0, 0, 1))
bpy.context.view_layer.update()
render(OUTP)
if MODE.startswith("eksplode") or MODE == "hero":
    cam = sc.camera
    keys = [k for k in ALL_KEYS if k in sistem.G and any((not o.hide_render) for o in sistem.G[k]["objs"])]
    info = anchor_pts(keys, cam)
    info["_size"] = [RW, RH]
    json.dump(info, open(OUTP + ".json", "w"), indent=1)
    print(json.dumps(info))
