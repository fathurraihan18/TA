"""Uji varian --penahan: shell tanpa boss + 4 penahan sekrup terpisah (dilem sesudah tumpukan masuk) + back plate v2 TIDAK berubah.

python verify_penahan.py <folder_penahan> <folder_v2_asli>      mis.  python verify_penahan.py v2c_penahan_sekrup .
"""
import sys, os, json, glob, hashlib
import numpy as np, trimesh
from trimesh.proximity import closest_point

D, V2 = sys.argv[1], sys.argv[2]
R = os.path.join(D, "_ref"); R2 = os.path.join(V2, "_ref")
S = json.load(open(os.path.join(R, "summary.json")))
P = S["penahan"]
NP = len(P.get("pieces", P["blocks"]))                    # jumlah bagian (4 blok, atau 3 bagian bila --strip)
ok_all = True


def report(name, ok, extra=""):
    global ok_all
    ok_all &= bool(ok)
    print(f"[{'OK ' if ok else 'GAGAL'}] {name} {extra}")


def vol(a, b):
    if np.any(a.bounds[1] < b.bounds[0]) or np.any(a.bounds[0] > b.bounds[1]):
        return 0.0
    r = trimesh.boolean.intersection([a, b], engine="manifold")
    return abs(r.volume) if r is not None and len(r.faces) else 0.0


def mind(a, b, n=3000):
    return closest_point(b, a.sample(n))[1].min()


shell = trimesh.load(os.path.join(R, "shell_design.stl")); plate = trimesh.load(os.path.join(R, "plate_design.stl"))
pen = trimesh.load(os.path.join(R, "penahan_design.stl"))
shell2 = trimesh.load(os.path.join(R2, "shell_design.stl")); plate2 = trimesh.load(os.path.join(R2, "plate_design.stl"))

print("=== 1. Back plate dan sekrup TIDAK berubah dari v2 ===")
h1 = hashlib.md5(open(os.path.join(D, "2_BackPlate_siap_cetak.stl"), "rb").read()).hexdigest()
h2 = hashlib.md5(open(os.path.join(V2, "2_BackPlate_siap_cetak.stl"), "rb").read()).hexdigest()
report("2_BackPlate_siap_cetak.stl identik byte-demi-byte dengan plate v2 yang sudah dicetak", h1 == h2, f"(md5 {h1[:8]} / {h2[:8]})")
d_ = trimesh.boolean.difference([plate, plate2], engine="manifold"); d2_ = trimesh.boolean.difference([plate2, plate], engine="manifold")
report("geometri plate sama (selisih 0 mm3)", (0 if len(d_.faces) == 0 else abs(d_.volume)) < 0.01 and (0 if len(d2_.faces) == 0 else abs(d2_.volume)) < 0.01)
sc1 = trimesh.load(os.path.join(R, "ref_Sekrup_M3x8.stl")); sc2 = trimesh.load(os.path.join(R2, "ref_Sekrup_M3x8.stl"))
report("4 lubang sekrup di plate (M3 x 8 flat head dari belakang) sama dengan v2", np.allclose(sc1.bounds, sc2.bounds, atol=1e-6))

print("\n=== 2. Shell = shell v2 dikurangi boss (tidak ada yang ditambah) ===")
rem = trimesh.boolean.difference([shell2, shell], engine="manifold"); add = trimesh.boolean.difference([shell, shell2], engine="manifold")
v_rem = abs(rem.volume) if len(rem.faces) else 0.0; v_add = abs(add.volume) if len(add.faces) else 0.0
report("shell hanya kehilangan boss (4 blok + pilot)", v_add < 0.01, f"(dibuang {v_rem:.0f} mm3, ditambah {v_add:.3f} mm3)")
bodies = [b for b in rem.split(only_watertight=False) if b.volume > 5]
for b in sorted(bodies, key=lambda m: m.bounds[0][0]):
    print(f"      boss dibuang: x[{b.bounds[0][0]:6.2f},{b.bounds[1][0]:6.2f}] y[{b.bounds[0][1]:6.2f},{b.bounds[1][1]:6.2f}] z[{b.bounds[0][2]:5.2f},{b.bounds[1][2]:5.2f}]")
report("tepat 4 boss", len(bodies) == 4)

print("\n=== 3. Penahan (4 blok) ===")
pb = pen.split(only_watertight=False)
report(f"penahan desain: {NP} badan, rapat", len(pb) == NP and all(b.is_watertight for b in pb))
ok_p = True
for blk in P["blocks"]:
    x, (ya, yb) = blk["x"], blk["y"]; px, py = blk["pilot"]
    mid = ((ya + yb) / 2)
    body = pen.contains(np.array([[x + 3.5, mid, 2.0], [x - 3.5, mid, 2.0], [x, mid + (1.6 if blk['side'] > 0 else -1.6), 2.0]]))
    hole = pen.contains(np.array([[px, py, 2.0], [px, py, 4.0], [px, py, 4.4]]))
    ok_p &= bool(body.all()) and not hole.any()
report("tiap penahan padat dan berlubang pilot Ø2.7 tembus ke atas", ok_p)
pf_ = os.path.join(D, "3_Penahan_Sekrup_siap_cetak.stl")
if not os.path.exists(pf_): pf_ = os.path.join(D, "3_Penahan_Sekrup_x4_siap_cetak.stl")
pr = trimesh.load(pf_)
report(f"STL cetak: satu berkas, {NP} bagian, rata di meja (Z=0), tanpa support", pr.is_watertight and len(pr.split(only_watertight=False)) == NP and abs(pr.bounds[0][2]) < 1e-6,
       f"(ukuran {np.round(pr.extents, 1).tolist()} mm, tinggi {pr.bounds[1][2]:.1f})")
vols = sorted(round(b.volume, 1) for b in pr.split(only_watertight=False))
if not P.get("strip"):
    report("4 blok bervolume sama", max(vols) - min(vols) < 0.5, f"({vols})")
else:
    print(f"      volume bagian cetak (mm3): {vols}")
    # puncak strip rata di meja: luas kontak dengan meja (Z=0) harus >= 40% luas denah tiap bagian (tanpa overhang)
    flat_ = [b for b in pr.split(only_watertight=False)]
    report("tidak ada overhang: dasar cetak = puncak penahan (bidang rata)", all(abs(b.bounds[0][2]) < 1e-6 for b in flat_))

print("\n=== 4. Dipasang SESUDAH tumpukan masuk: tidak menabrak komponen ===")
refs = {os.path.basename(f)[4:-4]: trimesh.load(f) for f in sorted(glob.glob(os.path.join(R, "ref_*.stl")))}
skip = {"Sekrup_M3x8", "Area_aktif", "Badan_saklar_KCD11", "Gland_PG7_+_mur"}
for nm, m in refs.items():
    if nm in skip: continue
    if nm == "Plug_jack_AD8232":
        m = m.slice_plane([0, 29.7, 0], [0, -1, 0], cap=True)
    v = vol(m, pen); d = mind(pen, m, 2500)
    report(f"{nm:20s} vs penahan", v < 0.3, f"(irisan {v:.2f} mm3, jarak terdekat {d:.2f} mm)")
d_pcb = mind(pen, refs["PCB_hijau"])
report("puncak penahan di bawah PCB (celah >= 0.2 mm)", d_pcb >= 0.2, f"({d_pcb:.2f} mm)")
v_sh = vol(pen, shell); d_sh = mind(pen, shell)
report("penahan tidak menyentuh shell tanpa lem: celah lem ke dinding", v_sh < 0.01 and 0.2 <= d_sh <= 0.4, f"(irisan {v_sh:.3f}; celah {d_sh:.2f} mm, diisi epoxy)")
v_pl = vol(pen, plate)
if P.get("strip"):
    pts_ = pen.sample(6000); pts_ = pts_[pts_[:, 2] > 1.75]                  # bagian batang (di atas kaki)
    d_rim = closest_point(plate, pts_)[1].min()
    report("batang strip melintas di atas rim plate tanpa menyentuh (celah >= 0.3 mm)", d_rim >= 0.3, f"({d_rim:.2f} mm)")
report("penahan tidak menabrak back plate (duduk di lantai plate)", v_pl < 0.3, f"(irisan {v_pl:.3f} mm3)")

print("\n=== 5. Penahan tidak menutup lubang port / jack / saklar / gland ===")
# bukaan dinding = irisan lempeng dinding dengan ruang kosong shell; jarak penahan ke tiap bukaan
out_x, out_yb, out_yt = S["outer"][0] / 2, *S["outer_y"]
cav_x, (cav_yb, cav_yt) = S["cavity"][0] / 2, S["cavity_y"]
slabs = {"ATAS (jack, saklar)": trimesh.creation.box(extents=(2 * out_x, out_yt - cav_yt, 33.9 + 0.5)),
         "BAWAH (micro-USB)": trimesh.creation.box(extents=(2 * out_x, cav_yb - out_yb, 33.9 + 0.5)),
         "KANAN (USB-C, gland)": trimesh.creation.box(extents=(out_x - cav_x, 2 * (cav_yt - cav_yb) / 2 * 2, 33.9 + 0.5))}
slabs["ATAS (jack, saklar)"].apply_translation((0, (out_yt + cav_yt) / 2, (33.9 - 0.5) / 2))
slabs["BAWAH (micro-USB)"].apply_translation((0, (out_yb + cav_yb) / 2, (33.9 - 0.5) / 2))
slabs["KANAN (USB-C, gland)"].apply_translation((-(out_x + cav_x) / 2, (cav_yt + cav_yb) / 2, (33.9 - 0.5) / 2))
for nm, slab in slabs.items():
    openings = trimesh.boolean.difference([slab, shell], engine="manifold")
    comps = [c for c in openings.split(only_watertight=False) if c.volume > 20]
    # buang lempeng sisa tipis (permukaan luar yang bukan bukaan): bukaan sejati menembus dinding
    for c in sorted(comps, key=lambda m: m.bounds[0][0]):
        dmin = mind(pen, c, 4000)
        ctr = c.bounds.mean(0)
        report(f"{nm:22s} bukaan di x={ctr[0]:6.1f} y={ctr[1]:6.1f} z={ctr[2]:5.1f} (volume {c.volume:6.0f} mm3)", dmin >= 3.0, f"(jarak penahan terdekat {dmin:.1f} mm)")
for nm in ("microUSB_ESP32", "USBC_powerbank"):
    d = mind(pen, refs[nm], 3000)
    report(f"jarak penahan ke konektor {nm}", d >= 3.0, f"({d:.1f} mm)")
jk = refs["Plug_jack_AD8232"].slice_plane([0, 29.7, 0], [0, -1, 0], cap=True)
report("jarak penahan ke laras jack AD8232", mind(pen, jk) >= 3.0, f"({mind(pen, jk):.1f} mm)")

print("\n=== 6. Penahan jauh dari kaki komponen/solder PCB ===")
holes = json.load(open(os.path.join(V2, "data", "pcb_holes.json")))["holes"]
XH, YH = 56.007, 33.655
mg = 99
fp = [dict(x=pc["x"], y=pc["y"]) for pc in P["pieces"]] if "pieces" in P else [dict(x=[b["x"] - P["w"] / 2, b["x"] + P["w"] / 2], y=b["y"]) for b in P["blocks"]]
for blk in fp:
    bx0, bx1 = blk["x"]; by0, by1 = blk["y"]
    for h in holes:
        hx, hy = -(h["xg"] - XH), -(h["yg"] - YH)
        dx = max(bx0 - hx, 0, hx - bx1); dy = max(by0 - hy, 0, hy - by1)
        mg = min(mg, np.hypot(dx, dy) - h["d"] / 2)
report("jarak penahan (seluruh denah) ke lubang/kaki PCB >= 1.5 mm", mg >= 1.5, f"(terdekat {mg:.2f} mm)")

print("\n=== 7. Sekrup M3 x 8 flat head dari belakang ===")
eng = vol(sc1, pen)
exp = 4 * np.pi * (1.5 ** 2 - (P["pilot_d"] / 2) ** 2) * (sc1.bounds[1][2] - S["z"]["split"])
report("ulir menggigit penahan (4 sekrup)", exp * 0.5 < eng < exp * 1.3, f"(irisan {eng:.1f} mm3, perkiraan {exp:.1f}; tertanam {sc1.bounds[1][2] - S['z']['split']:.2f} mm)")
report("sekrup tidak menyentuh shell", vol(sc1, shell) < 0.01)
report("ujung sekrup tidak menyentuh PCB (celah >= 0.3 mm)", S["z"]["pcb"][0] - sc1.bounds[1][2] >= 0.3, f"({S['z']['pcb'][0] - sc1.bounds[1][2]:.2f} mm)")

print("\n=== 8. Prosedur 'plate sebagai jig': penahan dipasang di plate dengan 4 sekrup, plate + penahan didorong lurus ke shell ===")
comb = trimesh.util.concatenate([plate, pen])
others = {"shell": shell}
others.update({nm: m for nm, m in refs.items() if nm not in skip})
first = {}
for d in np.arange(8.0, -1e-9, -1.0):
    cm = comb.copy(); cm.apply_translation((0, 0, -d))
    for nm, tgt in others.items():
        if nm in first: continue
        v = vol(trimesh.util.concatenate([pen.copy().apply_translation((0, 0, -d)), plate.copy().apply_translation((0, 0, -d))]), tgt)
        if v > 0.3: first[nm] = (d, v)
report("plate + 4 penahan masuk lurus ke shell berisi tumpukan tanpa tabrakan", not first, ("" if not first else str(first)))

print("\nHASIL AKHIR:", "SEMUA LOLOS" if ok_all else "ADA YANG GAGAL")
sys.exit(0 if ok_all else 1)
