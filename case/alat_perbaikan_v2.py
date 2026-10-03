"""Alat bantu memperbaiki shell v2 yang SUDAH tercetak (boss di dinding menghalangi tumpukan) tanpa mencetak ulang shell.

python alat_perbaikan_v2.py <folder_v2b>

Hasil di <folder_v2b>/perbaikan_v2_tercetak/:
  bagian_dibuang_dari_shell_v2.stl   volume yang harus dibuang dari shell v2 (selisih shell v2 - shell v2b; tidak ada yang ditambah)
  jig_bor_ATAS.stl, jig_bor_BAWAH.stl  penuntun bor Ø3.4 untuk 4 lubang sekrup samping (pelana di tepi belakang dinding)
Jig: flange rata di tepi belakang dinding (bidang belah Z = -0.5), pelat tegak menempel muka luar dinding dengan lubang di Z = 2.0,
dua tab masuk ke sudut rongga (menentukan posisi X). Cetak dengan flange di meja, tanpa support.
"""
import sys, os, json
import numpy as np, trimesh

D = sys.argv[1]
S = json.load(open(os.path.join(D, "_ref", "summary.json")))
R = S["rakit"]
out = os.path.join(D, "perbaikan_v2_tercetak"); os.makedirs(out, exist_ok=True)
CAV_HX = S["cavity"][0] / 2
cav_yb, cav_yt = S["cavity_y"]; out_yb, out_yt = S["outer_y"]
Z_SPLIT = S["z"]["split"]


def box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0)); b.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)); return b


def cyl_y(x, z, r, y0, y1):
    c = trimesh.creation.cylinder(radius=r, height=y1 - y0, sections=48)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    c.apply_translation((x, (y0 + y1) / 2, z)); return c


def union(ms): return trimesh.boolean.union(ms, engine="manifold")
def diff(a, bs): return trimesh.boolean.difference([a] + bs, engine="manifold")


def jig(side, xs):
    """side=+1 dinding Atas, -1 dinding Bawah; xs = posisi x lubang (sumbu simetris)."""
    wall_in, wall_out = (cav_yt, out_yt) if side > 0 else (cav_yb, out_yb)
    T = 3.0; GAP = 0.06
    def Y(a, b): return (min(a, b), max(a, b))
    y_plate = Y(wall_out + side * GAP, wall_out + side * (GAP + T))                    # pelat menempel muka luar dinding
    y_flange = Y(wall_in - side * 3.0, wall_out + side * (GAP + T))                    # flange: dari 3 mm di dalam rongga sampai pelat
    y_tab = Y(wall_in - side * 3.0, wall_in - side * 0.05)                              # tab di sudut rongga, menempel dinding dalam
    parts = [box(-CAV_HX + 0.3, CAV_HX - 0.3, *y_flange, Z_SPLIT - 3.0, Z_SPLIT),
             box(-45.0, 45.0, *y_plate, Z_SPLIT - 3.0, R["z"] + 4.5)]
    xe = CAV_HX - 0.3
    for xa, xb in ((xe - 3.0, xe), (-xe, -xe + 3.0)):                                   # tab di kedua ujung rongga
        parts.append(box(xa, xb, *y_tab, Z_SPLIT, Z_SPLIT + 8.0))
    j = union(parts)
    holes = [cyl_y(x, R["z"], 3.6 / 2, y_plate[0] - 0.5, y_plate[1] + 0.5) for x in xs]
    j = diff(j, holes)
    # tanda: celah bor Ø3.4 -> lubang jig Ø3.6 (bor 3.5 mm pas)
    return j


for nm, side, xs in (("ATAS", +1, [x for x, s in R["pos"] if s > 0]), ("BAWAH", -1, [x for x, s in R["pos"] if s < 0])):
    j = jig(side, xs)
    assert j.is_watertight, nm
    # orientasi cetak: flange di meja (Z = Z_SPLIT-3 -> 0)
    j.apply_translation((0, 0, -(Z_SPLIT - 3.0)))
    j.export(os.path.join(out, f"jig_bor_{nm}.stl"))
    print(f"jig {nm}: lubang di x = {xs} (mm dari tengah shell), tinggi lubang {R['z'] - Z_SPLIT:.1f} mm di atas tepi belakang; ukuran {np.round(j.extents, 1)}")
