"""Render realistis (Cycles) klip sensor PPG: eksplode (+ jangkar balon), klip terpasang di jari, tampak bawah tanpa tutup.
Bagian cetak berwarna kode (A abu, B krem, C biru, D oranye) agar sesuai nomor pada gambar teknik; modul HW-605 memakai model nyata
(komponen/hw605, dipasang lewat file asm) dan kabel 4 inti + 4 kawat berwarna.
python r_klip.py -- <mode> <berkas_keluaran.png> [sampel] [lebar_px]     mode: meledak | pakai | bawah
Pada mode meledak juga ditulis anchors_meledak.json (koordinat normal 0..1, asal kiri-bawah) di folder yang sama dengan berkas keluaran.
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from lib import *
from bpy_extras.object_utils import world_to_camera_view
import sistem                                                       # hanya untuk konstanta/jalur dan hw_color (tidak membangun scene)

A_ = sys.argv[sys.argv.index("--") + 1:]
MODE, OUTP = A_[0], A_[1]
SAMP = int(A_[2]) if len(A_) > 2 else 64
RW = int(A_[3]) if len(A_) > 3 else 1500
R = os.path.join(sistem.CASE, "sensor_ppg", "klip_v2", "_ref")
S = sistem.KS
ASM = sistem.ASM
XP, XS, ZL, BT = S["XP"], S["XS"], S["Z_L"], S["board"]["t"]

# asm (klip menggantung di sistem) -> bingkai desain klip: p_klip = R^T (p_asm - t),  R = Rz(+90), t = (-100, -99.195, 28.15)
M_INV = Matrix(((0, 1, 0, 99.195), (-1, 0, 0, -100.0), (0, 0, 1, -28.15), (0, 0, 0, 1)))

reset()
transparent = True
sc = setup_cycles((RW, int(RW * (0.92 if MODE == "meledak" else 0.66))), SAMP, transparent=transparent, world_strength=0.8)
studio_lights(0.45)


def pm(name, col, rg=0.45, mt=0.0, **kw):
    return mat(name, col, rg, mt, **kw)


MA = {"A": pm("kA", (0.66, 0.68, 0.72), 0.45, 0.0, **{"Coat Weight": 0.1}), "B": pm("kB", (0.74, 0.70, 0.60), 0.45, 0.0, **{"Coat Weight": 0.1}),
      "C": pm("kC", (0.12, 0.30, 0.72), 0.45, 0.0, **{"Coat Weight": 0.1}), "D": pm("kD", (0.90, 0.38, 0.05), 0.45, 0.0, **{"Coat Weight": 0.1})}
WHITE = pm("kabel_putih", (0.92, 0.92, 0.90), 0.5)
G = {}
G["A"] = [load_stl(os.path.join(R, "A_desain.stl"), MA["A"], name="A", flat=False)]
G["B"] = [load_stl(os.path.join(R, "B_desain.stl"), MA["B"], name="B", flat=False)]
G["C"] = [load_stl(os.path.join(R, "C_desain.stl"), MA["C"], name="C", flat=False)]
G["D"] = [load_stl(os.path.join(R, "D_desain.stl"), MA["D"], name="D", flat=False)]
G["D"][0].location = (XP + S["seats_ls"][0] + 9.0, 14.0, S["BLK"][0] + 6.0)
board = []
for k_ in ("pcb", "pad", "sensor", "jendela", "ic", "smd"):
    col, rg, mt, ex = sistem.hw_color(k_)
    board.append(load_stl(os.path.join(ASM, f"ppg__clip_hw605_{k_}.stl"), mat("hw_" + k_, col, rg, mt, **ex), xform=M_INV, name="hw_" + k_))
G["board"] = board
G["spring"] = [load_stl(os.path.join(ASM, "ppg__clip_pegas.stl"), mat("pegas", (0.72, 0.74, 0.77), 0.25, 1.0), xform=M_INV, name="pegas", flat=False)]
G["screw"] = [load_stl(os.path.join(ASM, "ppg__clip_sekrup.stl"), mat("sekrup_klip", (0.06, 0.06, 0.07), 0.35, 0.6), xform=M_INV, name="sekrup", flat=False)]
G["finger"] = [load_stl(os.path.join(R, "ref_Jari_telunjuk.stl"), mat("jari", (0.90, 0.62, 0.50), 0.62, 0.0, **{"Subsurface Weight": 0.15}), name="jari", flat=False)]

cab_z = S["z_ax"]
G["cable"] = [tube("kabel", [(52.0, -8.4, cab_z), (59.0, 0.0, cab_z), (S["XL"] + 14.0, 0.0, cab_z)], S["cable_d"] / 2, WHITE, 14)]
pad_x = XS + S["board"]["l"] / 2 - 1.5
zw = ZL + BT + 0.9
wires = []
WC = {"w1": (0.95, 0.80, 0.10), "w2": (0.95, 0.95, 0.95), "w3": (0.85, 0.10, 0.10), "w4": (0.05, 0.05, 0.05)}
for i, (m_, off) in enumerate((("w1", -3.81), ("w2", -1.27), ("w3", 1.27), ("w4", 3.81))):
    k = (i - 1.5) * 0.9
    pts = [(pad_x, off, zw), (33.0, off * 0.35 + k * 0.6, zw), (37.5, -8.4 + k, zw + 0.2), (52.0, -8.4 + k, cab_z)]
    wires.append(tube(f"wire{i}", pts, 0.5, pm("w_" + m_, WC[m_], 0.45), 12))
G["wires"] = wires

# busa 1 mm pada rahang B (lekuk)
bm = bmesh.new()
n = 18
ys = [-8.0 + 16.0 * i / n for i in range(n + 1)]
R_C = S["cradle"]["R"]
top, bot = [], []
for x in (10.0, 33.0):
    for y in ys:
        zb = S["ZP"] + (R_C - math.sqrt(R_C ** 2 - y * y))
        top.append((x, y, zb + 0.05)); bot.append((x, y, zb - 1.0))
vt = [bm.verts.new(p) for p in top]; vb = [bm.verts.new(p) for p in bot]
m_ = n + 1
for i in range(n):
    bm.faces.new([vt[i], vt[i + 1], vt[m_ + i + 1], vt[m_ + i]])
    bm.faces.new([vb[m_ + i], vb[m_ + i + 1], vb[i + 1], vb[i]])
    bm.faces.new([vt[i], vb[i], vb[i + 1], vt[i + 1]])
    bm.faces.new([vt[m_ + i + 1], vb[m_ + i + 1], vb[m_ + i], vt[m_ + i]])
bm.faces.new([vt[0], vt[m_], vb[m_], vb[0]]); bm.faces.new([vt[n], vb[n], vb[m_ + n], vt[m_ + n]])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
G["foam"] = [mesh_obj("busa", bm, pm("busa", (0.15, 0.15, 0.17), 0.9))]

PAR = {}
for k, obs in G.items():
    e = bpy.data.objects.new("G_" + k, None); link(e)
    for o in obs: o.parent = e
    PAR[k] = e


def set_pose(offsets, show):
    for k, e in PAR.items():
        e.location = Vector(offsets.get(k, (0, 0, 0)))
        for o in G[k]: o.hide_render = k not in show


def proj(p):
    co = world_to_camera_view(sc, sc.camera, Vector(p))
    return (co.x, co.y)


def cam_dir(direction, target, ortho):
    d = Vector(direction).normalized()
    return camera(tuple(Vector(target) + d * 800), tuple(target), ortho=ortho, up=(0, 0, 1))


if MODE == "meledak":
    off = {"B": (0, 0, 46), "foam": (0, 0, 30), "spring": (0, 0, 24), "screw": (0, 40, 0), "D": (0, 0, 14), "C": (0, 0, -34), "board": (0, 0, -17), "cable": (0, 0, 0), "wires": (0, 0, -17)}
    set_pose(off, ("A", "B", "C", "D", "board", "cable", "wires", "spring", "screw", "foam"))
    cam_dir((-0.75, -0.95, 0.6), (33, 8, 8), 150.0)
    bpy.context.view_layer.update()
    render(OUTP)
    anchors = {
        "A": (3.0, -13.0, -8.0), "B": (20.0, -13.0, 4.0 + off["B"][2]), "C": (50.0, -10.6, S["Z_O"] + off["C"][2]),
        "D": (XP + S["seats_ls"][0] + 9.0, 14.0, S["BLK"][0] + 6.5 + 14.0), "board": (S["XS"] - 6.0, 6.0, S["Z_L"] + S["board"]["t"] + off["board"][2]),
        "cable": (S["XL"] + 10.0, 0.0, cab_z), "spring": (XP + S["seats_ls"][0], 0.0, S["BLK"][0] + 3.0 + off["spring"][2]),
        "screw": (XP, 40.0 + 6.0, 0.0), "foam": (20.0, 6.0, S["ZP"] - 1.0 + off["foam"][2]), "wires": (40.0, -8.4, S["Z_L"] + 3.0 + off["wires"][2]),
    }
    json.dump({k: proj(v) for k, v in anchors.items()}, open(os.path.join(os.path.dirname(OUTP), "anchors_meledak.json"), "w"), indent=1)
elif MODE == "pakai":
    set_pose({}, ("A", "B", "C", "board", "cable", "screw", "spring", "foam", "finger"))
    add_floor(S["Z_O"] - 0.5, catcher=True)
    cam_dir((-0.75, -0.9, 0.55), (28, 0, -1), 100.0)
    render(OUTP)
elif MODE == "bawah":
    set_pose({}, ("A", "board", "cable", "wires", "spring"))
    cam_dir((0.5, -0.7, -0.9), (35, -2, -9), 100.0)
    render(OUTP)
print("OK")
