"""Verifikasi otomatis klip sensor PPG: integritas mesh, kecocokan komponen, gerak engsel (tabrakan tiap sudut),
gaya jepit pegas, kecocokan jari, fitur tipis, dan analisis overhang (orientasi cetak).
python verify_clip.py <folder_output_make_clip> [k_pegas_N_per_mm] [L0_mm]
"""
import sys, os, json
import numpy as np
import trimesh
from shapely.ops import unary_union

D = sys.argv[1] if len(sys.argv) > 1 else "."
R = os.path.join(D, "_ref")
S = json.load(open(os.path.join(R, "summary.json")))
K = float(sys.argv[2]) if len(sys.argv) > 2 else S["k_est"]
L0 = float(sys.argv[3]) if len(sys.argv) > 3 else S["spring"]["L0"]
M = {k: trimesh.load(os.path.join(R, f"{k}_desain.stl")) for k in "ABCD"}
G = {k: trimesh.load(os.path.join(R, f"ref_{k}.stl")) for k in ("Modul_HW605", "Kabel_4_inti", "Kawat_bundel", "Pegas", "Sekrup_engsel", "Jari_telunjuk")}
XP = S["XP"]
ok_all = True


def report(name, ok, extra=""):
    global ok_all
    ok_all &= bool(ok)
    print(f"[{'OK ' if ok else 'GAGAL'}] {name} {extra}")


def vol(a, b):
    try:
        r = trimesh.boolean.intersection([a, b], engine="manifold")
        return abs(r.volume) if r is not None and len(r.faces) else 0.0
    except Exception:
        return float("nan")


def rot_b(theta_deg):
    T = trimesh.transformations.rotation_matrix(np.radians(theta_deg), [0, 1, 0], [XP, 0, 0])
    b = M["B"].copy(); b.apply_transform(T)
    return b, T


print("=== 1. Integritas mesh ===")
for k in "ABCD":
    m = M[k]
    report(f"{k} watertight", m.is_watertight, f"| volume {m.volume:.0f} mm3 | bbox {np.ptp(m.bounds, axis=0).round(1).tolist()} | badan {len(m.split(only_watertight=False))}")
for k in "ABCD":
    report(f"{k} satu badan utuh", len(M[k].split(only_watertight=False)) == 1)

print("\n=== 2. Kecocokan pada posisi nominal (jari terpasang) ===")
v_ab = vol(M["A"], M["B"])
report("rahang A dan B tidak saling menembus", v_ab < 0.5, f"({v_ab:.3f} mm3)")
v_ac = vol(M["A"], M["C"])
exp_crush = 8 * 6.0 * 0.15 * (S["Z_L"] - 0.4 - (S["Z_O"] + 0.5))          # 8 rusuk gesek, interferensi 0,15 mm
report("tutup C: hanya 8 rusuk gesek yang menekan alur A (tahan tutup, bisa dicungkil)", 0.5 * exp_crush < v_ac < 1.6 * exp_crush, f"(irisan {v_ac:.1f} mm3, perkiraan {exp_crush:.1f} mm3)")
v_bc = vol(M["B"], M["C"])
report("tutup C tidak menyentuh B", v_bc < 0.5, f"({v_bc:.3f} mm3)")
for nm in ("Modul_HW605", "Kawat_bundel"):
    va, vc, vb = vol(G[nm], M["A"]), vol(G[nm], M["C"]), vol(G[nm], M["B"])
    report(f"{nm} muat di rongga A (irisan A/B/C = 0)", va < 0.5 and vc < 0.5 and vb < 0.5, f"(A {va:.3f}, C {vc:.3f}, B {vb:.3f} mm3)")
cab = G["Kabel_4_inti"]
va, vb, vc = vol(cab, M["A"]), vol(cab, M["B"]), vol(cab, M["C"])
report("kabel 4 inti lewat terowongan dan leher A tanpa tabrakan", va < 0.5 and vb < 0.5, f"(A {va:.3f}, B {vb:.3f} mm3)")
print(f"      rib penjepit di tutup menekan jaket kabel: irisan {vc:.2f} mm3 (sengaja, kabel empuk)")
va = vol(G["Sekrup_engsel"], M["A"]); vb = vol(G["Sekrup_engsel"], M["B"])
print(f"      sekrup engsel: irisan dengan A {va:.1f} mm3 (ulir mengulir sendiri di lug pilot), dengan B {vb:.3f} mm3")
report("sekrup lewat lug +Y dan tab B tanpa tabrakan (lubang 3,2 mm)", vb < 0.5)
# jarak bebas modul ke dinding rongga
from trimesh.proximity import closest_point
pts = G["Modul_HW605"].sample(4000)
d_a = closest_point(M["A"], pts)[1].min()
print(f"      jarak min modul HW-605 ke dinding A = {d_a:.2f} mm (tutup C menopang dari bawah)")
# sensor rata dengan permukaan bantalan
zs_top = G["Modul_HW605"].bounds[1][2]
print(f"      puncak sensor Z={zs_top:.2f}; permukaan bantalan Z={-S['ZP']:.2f} -> sensor masuk {(-S['ZP'] - zs_top):.2f} mm")

print("\n=== 3. Gerak engsel: B diputar terhadap A (theta<0 = menutup, theta>0 = membuka) ===")
res = {}
thetas = np.arange(-14.0, 21.0, 1.0)
first_close = first_open = None
for th in thetas:
    b, _ = rot_b(th)
    res[th] = vol(M["A"], b)
for th in sorted(thetas):
    if th <= 0 and res[th] > 0.5:
        first_close = th if first_close is None else max(first_close, th)
for th in sorted(thetas):
    if th >= 0 and res[th] > 0.5 and first_open is None:
        first_open = th
print("      theta:volume irisan A/B (mm3) -> " + " ".join(f"{int(t)}:{res[t]:.0f}" for t in thetas if res[t] > 0.5 or t in (-8, -6, -4, -2, 0, 4, 8, 12, 16)))
close_lim = None
for th in sorted([t for t in thetas if t <= 0], reverse=True):
    if res[th] > 0.5:
        close_lim = th; break
open_lim = None
for th in sorted([t for t in thetas if t >= 0]):
    if res[th] > 0.5:
        open_lim = th; break
# sudut bebas sebenarnya (kontak pertama)
free_close = max([t for t in thetas if t < 0 and res[t] > 0.5] + [-99.0])
free_open = min([t for t in thetas if t > 0 and res[t] > 0.5] + [99.0])
print(f"      kontak penutupan pertama pada theta = {free_close:.0f} derajat (bibir B menyentuh bibir A); kontak pembukaan pada theta = {free_open:.0f} derajat")
report("rentang gerak bebas tabrakan -(5) ... +(10) derajat", all(res[t] < 0.5 for t in thetas if -4 <= t <= 10))
lf = S["lf"]
gap_close = S["G0"] + 2 * 0  # dummy
print(f"      theta=0 : jarak bantalan di sensor = {S['G0']:.1f} mm")
for th in (-3, 0, 5, 10):
    print(f"      theta={th:+d} : jarak bantalan di pusat sensor ~ {S['G0'] + lf * np.tan(np.radians(th)) * 1.0:.1f} mm")

print("\n=== 4. Pegas dan gaya jepit pada jari ===")
print(f"      pegas: OD {S['spring']['od']} mm, kawat {S['spring']['wire']} mm, L0 {L0} mm, k = {K:.2f} N/mm (perkiraan, ukur pegas Anda)")
pivot = np.array([XP, 0, 0.0])


def clamp_force(seat_i, th, k=K, L0_=L0, shim=0.0):
    xs = S["seats_x"][seat_i]
    p_low = np.array([xs, 0, S["BLK"][0] + shim])
    p_up = np.array([xs, 0, S["BLK"][1] + S["pocket_depth"][seat_i]])
    a = np.radians(th)
    r = p_up - pivot
    # rotasi sekitar +Y: (x,z) -> (x cos a + z sin a, -x sin a + z cos a)
    p_up_r = pivot + np.array([r[0] * np.cos(a) + r[2] * np.sin(a), 0, -r[0] * np.sin(a) + r[2] * np.cos(a)])
    d = p_up_r - p_low
    Ls = np.linalg.norm(d)
    delta = L0_ - Ls
    if delta <= 0:
        return 0.0, delta, Ls
    u = d / Ls
    F = k * delta * u
    rr = p_up_r - pivot
    My = rr[2] * F[0] - rr[0] * F[2]
    Fc = -My / (S["XP"] - S["XS"]) * -1.0
    return abs(My) / (S["XP"] - S["XS"]), delta, Ls


for i, ls in enumerate(S["seats_ls"]):
    row = []
    for shim in (0.0, 1.0, 2.0):
        F, dlt, Ls_ = clamp_force(i, 0.0, shim=shim)
        row.append(f"{shim:.0f} shim: {F:.1f} N (tekan {dlt:.1f} mm)")
    print(f"      dudukan {i + 1} (Ls={ls:g} mm, kantong {S['pocket_depth'][i]:.1f} mm): " + " | ".join(row))
tab = {}
for k_ in (0.4, 0.7, 1.0, 1.3, 1.6, 2.0):
    tab[k_] = []
    for i in range(2):
        tab[k_].append([clamp_force(i, 0.0, k=k_, shim=sh)[0] for sh in (0.0, 1.0, 2.0)])
print("      tabel gaya jepit nominal (N), L0 = " + f"{L0:g}" + " mm:  k(N/mm) : dudukan1 [0,1,2 shim] | dudukan2 [0,1,2 shim]")
for k_, v in tab.items():
    print(f"        k={k_:.1f}: " + " ".join(f"{x:.1f}" for x in v[0]) + "   |   " + " ".join(f"{x:.1f}" for x in v[1]))
f1 = clamp_force(0, 0.0)[0]; f2 = clamp_force(1, 0.0)[0]
report("pegas selalu tertekan pada seluruh rentang gerak (jari 12-20 mm)", all(clamp_force(i, th)[1] > 0 for i in range(2) for th in (-3, 0, 5, 10)))
report("gaya jepit nominal 1-5 N pada kedua dudukan (pegas perkiraan)", 1.0 <= f1 <= 5.0 and 1.0 <= f2 <= 5.0, f"({f1:.1f} N / {f2:.1f} N)")
json.dump(dict(k=K, L0=L0, force_table={str(k_): v for k_, v in tab.items()}, thetas=[int(t) for t in thetas], overlap={str(int(t)): res[t] for t in thetas},
               free_close=float(free_close), free_open=float(free_open)), open(os.path.join(R, "kinematika.json"), "w"), indent=1)

print("\n=== 5. Jari telunjuk (17 x 14 mm) di dalam rahang (informasi) ===")
fj = G["Jari_telunjuk"]
va, vb = vol(fj, M["A"]), vol(fj, M["B"])
print(f"      irisan jari-A {va:.0f} mm3 (ujung jari membulat bertumpu pada bahu), jari-B {vb:.0f} mm3 (nol = ada celah ke busa/bibir)")
pts = fj.sample(6000)
print(f"      jarak min jari ke B {closest_point(M['B'], pts)[1].min():.2f} mm; ke A {closest_point(M['A'], pts)[1].min():.2f} mm")

print("\n=== 6. Fitur tipis dan overhang pada orientasi cetak ===")
Tpr = {"A": trimesh.transformations.translation_matrix([0, 0, -S["Z_O"]]),
       "B": trimesh.transformations.translation_matrix([0, 0, S["Z_T"]]) @ trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0]),
       "C": trimesh.transformations.translation_matrix([0, 0, -S["Z_O"]]), "D": np.eye(4)}
for k in "ABC":
    m = M[k].copy(); m.apply_transform(Tpr[k])
    zmax = m.bounds[1][2]
    found = []
    for z in np.arange(0.12, zmax, 0.25):
        sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if sec is None: continue
        p, T = sec.to_planar()
        U = unary_union(p.polygons_full)
        lost = U.difference(U.buffer(-0.45, join_style=2).buffer(0.45, join_style=2))
        for gm in (lost.geoms if hasattr(lost, "geoms") else [lost]):
            if gm.area > 0.3:
                c = gm.centroid.coords[0]
                found.append((round(z, 2), round(gm.area, 2), np.round(trimesh.transform_points([[c[0], c[1], 0]], T)[0][:2], 1).tolist()))
    report(f"{k}: tidak ada fitur tipis (< 0,9 mm)", len(found) == 0, f"({len(found)} potongan)" + (f" contoh {found[:3]}" if found else ""))
    # overhang
    nz = m.face_normals[:, 2]
    cz = m.triangles_center[:, 2]
    sel = np.where((nz < -0.70) & (cz > 0.25))[0]
    if len(sel):
        sub = trimesh.graph.connected_components(m.face_adjacency[np.isin(m.face_adjacency, sel).all(axis=1)], nodes=sel, min_len=1)
        items = []
        for comp in sub:
            area = m.area_faces[comp].sum()
            if area < 3.0: continue
            b = m.triangles[comp].reshape(-1, 3)
            ext = np.ptp(b, axis=0)
            flat = bool(np.all(nz[comp] < -0.98))
            items.append((round(area, 1), flat, np.round(b.min(0), 1).tolist(), np.round(ext, 1).tolist()))
        items.sort(reverse=True)
        print(f"      {k}: {len(items)} area overhang > 45 derajat (luas mm2, datar=jembatan, bbox-min, ukuran):")
        for it in items[:8]:
            print("         ", it)
    else:
        print(f"      {k}: tanpa overhang > 45 derajat")

print("\n=== 7. Estimasi massa (PLA 1,24 g/cm3, perimeter 3 + infill 25 % ~ 60 % volume) ===")
tot = 0
for k in "ABCD":
    w = M[k].volume / 1000 * 1.24 * 0.6 * (4 if k == "D" else 1)
    tot += w
    print(f"      {k}: {M[k].volume / 1000:.2f} cm3 -> sekitar {w:.1f} g" + (" (x4)" if k == "D" else ""))
print(f"      total klip: sekitar {tot:.0f} g (tanpa kabel, pegas, sekrup)")
print("\nHASIL AKHIR:", "SEMUA LOLOS" if ok_all else "ADA YANG GAGAL")
sys.exit(0 if ok_all else 1)
