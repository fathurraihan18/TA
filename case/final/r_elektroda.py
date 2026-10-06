"""Render komponen ELEKTRODA EKG: set kabel 3-lead (merah RA, kuning LA, hijau RL) + plug 3,5 mm, tampak atas dan samping satu elektroda.
python r_elektroda.py -- <out_dir> [samples]
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import numpy as np

A = sys.argv[sys.argv.index("--") + 1:]
OUT = A[0]; SAMP = int(A[1]) if len(A) > 1 else 64
os.makedirs(OUT, exist_ok=True)
VIEWS = os.environ.get("VIEWS", "set,top,side,plug").split(",")
info = {}


def scene(transparent=True, res=(1800, 1100)):
    reset()
    sc = setup_cycles(res, SAMP, transparent=transparent, world_strength=0.85)
    studio_lights(0.4)
    return sc


# ---------------------------------------------------------------- set lengkap (rebah di meja)
if "set" in VIEWS:
    scene(True, (1800, 1000))
    zt = 0.0
    plug, pobj, pend = trs_plug(loc=(-120.0, 0.0, 3.25 + 0.0), tag="plug")
    # plug sepanjang +Y; putar agar searah +X (kabel menuju elektroda di kanan)
    plug.rotation_euler = (0, 0, math.radians(-90))
    plug.location = (-150.0, 0.0, 3.25)
    cable = mat_wire()
    # kabel utama: dari ujung relief (x=-150+ (14+10.3+11)=-114.7) ke sambungan J
    p0 = (-150.0 + 35.3, 0.0, 3.25)
    J = (-20.0, 0.0, 1.9)
    main = tube("kabel_utama", [p0, (-95.0, 6.0, 2.6), (-65.0, -8.0, 1.9), (-40.0, 4.0, 1.9), J], 1.9, cable, 14)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=2.6, radius2=2.6, depth=16.0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    sleeve = mesh_obj("sambungan", bm, mat("selongsong", (0.15, 0.15, 0.17), 0.5)); smooth(sleeve); sleeve.location = (J[0] + 6, J[1], J[2])
    P = {"RA": (95.0, 82.0), "RL": (130.0, 0.0), "LA": (95.0, -82.0)}
    for lb in ("RA", "RL", "LA"):
        px, py = P[lb]
        to_j = math.degrees(math.atan2(J[1] - py, J[0] - px))
        rot = to_j - 35.0
        em, objs, out = electrode(lb, loc=(px, py, 0.0), rot_z=rot, tail_deg=35.0, tag=lb.lower())
        R = Matrix.Rotation(math.radians(rot), 3, "Z")
        ow = Vector(R @ Vector(out)) + Vector((px, py, 0.0))
        d = Vector((J[0] - ow.x, J[1] - ow.y, 0)); n = Vector((-d.y, d.x, 0)).normalized() * (9.0 if lb == "RA" else -9.0 if lb == "LA" else 4.0)
        pw = [tuple(ow), (ow.x + d.x * 0.3 + n.x * 0.7, ow.y + d.y * 0.3 + n.y * 0.7, 1.9), (ow.x + d.x * 0.62 + n.x, ow.y + d.y * 0.62 + n.y, 1.9), (J[0] + 12.0, J[1] + (ow.y - J[1]) * 0.12, 1.9), (J[0] + 6.0, J[1], 1.9)]
        tube(f"kawat_{lb}", pw, 0.85, cable, 14)
    objs_all = [o for o in bpy.data.objects if o.type == "MESH"]
    allv = np.array([(o.matrix_world @ v.co)[:] for o in objs_all for v in o.data.vertices])
    lo, hi = allv.min(0), allv.max(0); cen = (lo + hi) / 2
    add_floor(lo[2] - 0.02, catcher=True)
    camera((cen[0] + 30, cen[1] - 330, 330), (cen[0] + 10, cen[1] + 4, 0), lens=45, up=(0, 1, 0))
    render(os.path.join(OUT, "elektroda_set.png"))
    info["set"] = dict(bbox_min=lo.tolist(), bbox_max=hi.tolist())

# ---------------------------------------------------------------- tampak atas satu elektroda (RA)
if "top" in VIEWS:
    scene(True, (1400, 1400))
    em, objs, out = electrode("RA", loc=(0, 0, 0), rot_z=0.0, tail_deg=35.0, tag="ra")
    camera((0, 0, 800), (0, 0, 0), ortho=64.0, up=(0, 1, 0))
    render(os.path.join(OUT, "elektroda_top.png"))
    info["top"] = dict(ortho=64.0, px=1400, center=[0, 0])
# ---------------------------------------------------------------- tampak samping (kamera di -Y, X ke kanan, Z ke atas)
if "side" in VIEWS:
    scene(True, (1800, 700))
    em, objs, out = electrode("RA", loc=(0, 0, 0), rot_z=0.0, tail_deg=0.0, tag="ra")
    ortho = 64.0
    camera((0, -800, 4.5), (6.0, 0, 4.5), ortho=ortho, up=(0, 0, 1))
    render(os.path.join(OUT, "elektroda_side.png"))
    info["side"] = dict(ortho=ortho, px=[1800, 700], center_x=6.0, center_z=4.5, snap_x=SNAP_XY[0])
# ---------------------------------------------------------------- plug 3,5 mm
if "plug" in VIEWS:
    scene(True, (1800, 700))
    plug, pobj, pend = trs_plug(loc=(0, 0, 0), tag="plug")
    plug.rotation_euler = (0, 0, math.radians(-90))
    ortho = 56.0
    camera((18.0, -800, 0), (18.0, 0, 0), ortho=ortho, up=(0, 0, 1))
    render(os.path.join(OUT, "plug_side.png"))
    info["plug"] = dict(ortho=ortho, px=[1800, 700], center_x=18.0, length=pend[1], barrel=14.0, body=10.3, boot=11.0)
json.dump(info, open(os.path.join(OUT, "elektroda_info.json"), "w"), indent=1)
