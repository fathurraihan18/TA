"""Verifikasi otomatis cover (v2, v3 --bay, dan varian --rakit): mesh rapat, ukuran/posisi lubang, tabrakan komponen, keterjangkauan sekrup, fitur tipis."""
import sys, os, json, glob
import numpy as np
import trimesh
from trimesh.proximity import closest_point
from shapely.ops import unary_union

D = sys.argv[1] if len(sys.argv) > 1 else "."
R = os.path.join(D, "_ref")
S = json.load(open(os.path.join(R, "summary.json")))
shell = trimesh.load(os.path.join(R, "shell_design.stl"))
plate = trimesh.load(os.path.join(R, "plate_design.stl"))
ok_all = True


def report(name, ok, extra=""):
    global ok_all
    ok_all &= bool(ok)
    print(f"[{'OK ' if ok else 'GAGAL'}] {name} {extra}")


def solid(mesh, p):
    return bool(mesh.contains(np.array([p], float))[0])


print("=== 1. Integritas mesh ===")
for nm, m in (("shell", shell), ("plate", plate)):
    report(f"{nm} watertight", m.is_watertight, f"| winding konsisten={m.is_winding_consistent} | volume={m.volume:.0f} mm3")
    b = m.bounds
    print(f"      bbox X[{b[0][0]:.2f},{b[1][0]:.2f}] Y[{b[0][1]:.2f},{b[1][1]:.2f}] Z[{b[0][2]:.2f},{b[1][2]:.2f}]  -> {np.ptp(b[:,0]):.2f} x {np.ptp(b[:,1]):.2f} x {np.ptp(b[:,2]):.2f} mm")
    report(f"{nm} satu badan utuh", len(m.split(only_watertight=False)) == 1)

print("\n=== 2. Probe lubang (titik DI DALAM lubang harus kosong, titik TEPI harus padat) ===")
tol = 0.2
m = S["micro"]; j = S["jack"]; u = S["usbc"]; g = S["gland"]; s = S["switch"]; belt = S["belt"]
cav_hx = S["cavity"][0] / 2; out_hx = S["outer"][0] / 2
cav_yb, cav_yt = S.get("cavity_y", [-S["cavity"][1] / 2, S["cavity"][1] / 2])      # dinding dalam Bawah / Atas
out_yb, out_yt = S.get("outer_y", [-S["outer"][1] / 2, S["outer"][1] / 2])
cav_hy = cav_yt; out_hy = out_yt                                                     # sisi ATAS (jack, saklar)
wall_y = lambda side: cav_yt if side > 0 else cav_yb
z_top = S["z"]["top"]


def probe_rect_x(ycen, zc, w, h, xs):  # lubang menembus sumbu X (dinding Kanan)
    inside = [(x, ycen + sy * (w / 2 - 0.1), zc + sz * (h / 2 - 0.1)) for x in xs for sy in (-1, 1) for sz in (-1, 1)] + [(x, ycen, zc) for x in xs]
    outside = [(x, ycen + sy * (w / 2 + 0.25), zc) for x in xs for sy in (-1, 1)] + [(x, ycen, zc + sz * (h / 2 + 0.25)) for x in xs for sz in (-1, 1)]
    return all(not solid(shell, p) for p in inside) and all(solid(shell, p) for p in outside)


def probe_rect_y(xcen, zc, w, h, ys):  # lubang menembus sumbu Y (dinding Atas/Bawah)
    inside = [(xcen + sx * (w / 2 - 0.1), y, zc + sz * (h / 2 - 0.1)) for y in ys for sx in (-1, 1) for sz in (-1, 1)] + [(xcen, y, zc) for y in ys]
    outside = [(xcen + sx * (w / 2 + 0.25), y, zc) for y in ys for sx in (-1, 1)] + [(xcen, y, zc + sz * (h / 2 + 0.25)) for y in ys for sz in (-1, 1)]
    return all(not solid(shell, p) for p in inside) and all(solid(shell, p) for p in outside)


ang = np.linspace(0, 2 * np.pi, 12, endpoint=False)
RK = S.get("rakit")
dw = (2.2, 2.8) if RK else (1.5, 2.8)           # varian --rakit: alur dalam dinding sedalam <= 1.75 mm -> probe di bagian luar dinding
report("micro-USB (BAWAH) 12.2 x 8.2 mm", probe_rect_y(m["x"], m["zc"], m["w"] + tol, m["h"] + tol, [cav_yb - dw[0], cav_yb - dw[1]]))
r_in, r_out = (j["d"] + tol) / 2 - 0.1, (j["d"] + tol) / 2 + 0.25
ins = [(j["x"] + r_in * np.cos(a), y, j["zc"] + r_in * np.sin(a)) for a in ang for y in (cav_hy + dw[0], cav_hy + dw[1])]
outs = [(j["x"] + r_out * np.cos(a), y, j["zc"] + r_out * np.sin(a)) for a in ang for y in (cav_hy + dw[0], cav_hy + dw[1])]
report("jack AD8232 (ATAS) bulat d=7.2 mm", all(not solid(shell, p) for p in ins) and all(solid(shell, p) for p in outs))
report("USB-C powerbank (KANAN) 10.4 x 4.6 mm", probe_rect_x(u["y"], u["zc"], u["w"] + tol, u["h"] + tol, [-cav_hx - 1.0, -cav_hx - 2.5]))
gx_mid = -(out_hx + g["out"] - g["plate"] / 2)
r_in, r_out = g["hole"] / 2 - 0.1, g["hole"] / 2 + 0.3
ins = [(gx_mid, g["y"] + r_in * np.cos(a), g["zc"] + r_in * np.sin(a)) for a in ang]
outs = [(gx_mid, g["y"] + r_out * np.cos(a), g["zc"] + r_out * np.sin(a)) for a in ang]
report(f"gland PG7 lubang d={g['hole']:.1f} mm", all(not solid(shell, p) for p in ins) and all(solid(shell, p) for p in outs))
R_hex = g["nut_af"] / np.sqrt(3)
x_pocket = -(out_hx + g["out"] - g["plate"] - 2.0)
ins = [(x_pocket, g["y"] + (R_hex - 0.5) * np.cos(np.radians(90 + 60 * k)), g["zc"] + (R_hex - 0.5) * np.sin(np.radians(90 + 60 * k))) for k in range(6)]
outs = [(x_pocket, g["y"] + (g["nut_af"] / 2 + 0.4), g["zc"]), (x_pocket, g["y"] - (g["nut_af"] / 2 + 0.4), g["zc"])]
report(f"kantong mur segi-enam AF {g['nut_af']:.1f}", all(not solid(shell, p) for p in ins) and all(solid(shell, p) for p in outs))
y_pan = out_hy - s["panel"] / 2
pts_in = [(s["x"] + sx * 6.8, y_pan, s["zc"] + sz * 4.4) for sx in (-1, 1) for sz in (-1, 1)] + [(s["x"], y_pan, s["zc"])]
pts_out = [(s["x"] + sx * 7.4, y_pan, s["zc"]) for sx in (-1, 1)] + [(s["x"], y_pan, s["zc"] + sz * 4.9) for sz in (-1, 1)]
report("saklar KCD11 datar: jendela panel 14.1 x 9.1 mm", all(not solid(shell, p) for p in pts_in) and all(solid(shell, p) for p in pts_out))
pts_rec = [(s["x"] + sx * 8.0, cav_hy + 0.8, s["zc"] + sz * 5.4) for sx in (-1, 1) for sz in (-1, 1)]
pts_rec_out = [(s["x"] + 8.6, cav_hy + 0.8, s["zc"]), (s["x"], cav_hy + 0.8, s["zc"] + 5.9)]
report("saklar KCD11: lekuk panel 1.6 mm (16.6 x 11.2)", all(not solid(shell, p) for p in pts_rec) and all(solid(shell, p) for p in pts_rec_out))
w = S["window"]
pin = [(w[2] + sx * (w[0] / 2 - 0.9), sy * (w[1] / 2 - 0.9), 32.7) for sx in (-1, 1) for sy in (-1, 1)] + [(w[2], 0, 32.7)]
pout = [(w[2] + sx * (w[0] / 2 + 0.3), 0, 32.7) for sx in (-1, 1)] + [(w[2], sy * (w[1] / 2 + 0.3), 32.7) for sy in (-1, 1)]
report("jendela layar 79 x 52 mm", all(not solid(shell, p) for p in pin) and all(solid(shell, p) for p in pout))
ok_slot = True
for sgn in (1, -1):
    cx = sgn * belt["slot_cx"]
    ocy = (out_yb + out_yt) / 2                                   # slot dipusatkan pada tengah outline (v3: tidak di Y=0)
    ins = [(cx + dx, ocy + dy, -2.0) for dx in (-2.5, 0, 2.5) for dy in (-belt["slot_l"] / 2 + 3.2, 0, belt["slot_l"] / 2 - 3.2)]
    outs = [(cx + sgn_ * (belt["slot_w"] / 2 + 0.4), ocy, -2.0) for sgn_ in (-1, 1)] + [(cx, ocy + sgn_ * (belt["slot_l"] / 2 + 0.4), -2.0) for sgn_ in (-1, 1)]
    ok_slot &= all(not solid(plate, p) for p in ins) and all(solid(plate, p) for p in outs)
report(f"2 slot sabuk {belt['slot_w']:.0f} x {belt['slot_l']:.0f} mm di sayap (X=+-{belt['slot_cx']:.1f})", ok_slot)

print("\n=== 2b. Boss sekrup penutup benar-benar ada dan berlubang pilot ===" if not RK else "\n=== 2b. Varian --rakit: tanpa boss di dinding, sekrup samping + lug di plate, alur konektor ===")
ok_boss = True
holes = json.load(open(os.path.join(D, "data", "pcb_holes.json")))["holes"]
XH_, YH_ = 56.007, 33.655
if not RK:
    for (px, py) in S["screws"]:
        side = 1 if py > 0 else -1
        zmid = 2.0
        mid_block = (px + 3.5, py, zmid)                       # badan boss (harus padat)
        ring = [(px + 1.42 * np.cos(a), py + 1.42 * np.sin(a), zmid) for a in ang]   # dinding lubang pilot (r 1.35) harus padat
        axis = (px, py, zmid)                                   # sumbu pilot harus kosong
        top_axis = (px, py, S["screw"]["boss_top"] - 0.3)
        ok_boss &= solid(shell, mid_block) and all(solid(shell, p_) for p_ in ring) and (not solid(shell, axis)) and (not solid(shell, top_axis))
        # boss harus menyatu dengan dinding: titik antara boss dan dinding padat
        ok_boss &= solid(shell, (px, wall_y(side) + side * 0.2, zmid)) and solid(shell, (px, wall_y(side) - side * 5.0, zmid))
    report("4 boss sekrup ada (padat), menempel di dinding, pilot Ø2.7 terbuka", ok_boss)

    # boss tidak boleh berada di bawah kaki komponen (lubang bor PCB) -> jarak >= 1.5 mm dari tepi boss
    ok_lead = True; min_gap = 99
    for (px, py) in S["screws"]:
        side = 1 if py > 0 else -1
        bx0, bx1 = px - 5.0, px + 5.0
        by0, by1 = sorted([wall_y(side) + side * 0.3, wall_y(side) - side * 6.0])
        for h in holes:
            hx, hy = -(h["xg"] - XH_), -(h["yg"] - YH_)
            dx = max(bx0 - hx, 0, hx - bx1); dy = max(by0 - hy, 0, hy - by1)
            gap = np.hypot(dx, dy) - h["d"] / 2
            min_gap = min(min_gap, gap)
    report("boss sekrup jauh dari kaki komponen/solder PCB (>= 1.5 mm)", min_gap >= 1.5, f"(jarak terdekat {min_gap:.2f} mm)")

else:
    ZS = RK["z"]
    # (a) tidak ada boss di dinding: ruang di sisi dalam dinding Atas/Bawah harus kosong sepanjang tinggi tumpukan rendah (Z 0 ... 4.3)
    free = True
    for sx_ in (-40.0, -23.0, 0.0, 9.0, 23.0, 40.0):
        for sd in (+1, -1):
            for dy in (1.0, 3.0, 5.5):
                for zz in (0.0, 2.0, 4.0):
                    free &= not solid(shell, (sx_, wall_y(sd) - sd * dy, zz))
    report("tanpa boss: dinding dalam Atas/Bawah rata (jalur tumpukan bebas)", free)
    # (b) lubang tembus sekrup samping Ø3.4 di dinding, sumbu bebas dan dinding sekitarnya padat
    ok_h = True
    for sx_, sd in RK["pos"]:
        if True:
            yy = wall_y(sd) + sd * 1.5                                          # tengah ketebalan dinding (3 mm)
            rr = RK["clear_d"] / 2
            ok_h &= not solid(shell, (sx_, yy, ZS)) and not solid(shell, (sx_ + rr - 0.3, yy, ZS)) and not solid(shell, (sx_, yy, ZS + rr - 0.3))
            ok_h &= solid(shell, (sx_ + rr + 0.3, yy, ZS)) and solid(shell, (sx_, yy, ZS + rr + 0.3)) and solid(shell, (sx_, yy, ZS - rr - 0.3))
            ok_h &= solid(shell, (sx_, yy, S["z"]["split"] + 0.3))                  # tepi belakang dinding di bawah lubang masih utuh
    report(f"4 lubang sekrup samping Ø{RK['clear_d']:.1f} menembus dinding Atas/Bawah; dinding di bawah lubang utuh", ok_h, f"(Z sumbu = {ZS:.1f}, tepi bawah lubang Z = {ZS - RK['clear_d'] / 2:.2f}, bidang belah {S['z']['split']:.1f})")
    report("lubang sekrup samping tidak memotong bidang belah (sisa dinding >= 0.5 mm di bawah lubang)", ZS - RK["clear_d"] / 2 > S["z"]["split"] + 0.5)
    # (c) lug di plate: padat, menempel dinding dengan celah, pilot sejajar lubang dinding, puncak di bawah PCB
    ok_l = True; gaps = []
    for lg in RK["lugs"]:
        ya, yb = lg["y"]; mid = (ya + yb) / 2; sd = lg["side"]
        ok_l &= solid(plate, (lg["x"] + 3.5, mid, 1.0)) and solid(plate, (lg["x"] - 3.5, mid, 1.0)) and solid(plate, (lg["x"], mid, 0.0))
        ok_l &= not solid(plate, (lg["x"], mid + sd * 1.0, ZS)) and not solid(plate, (lg["x"], lg["pilot_y"][0] + 0.5, ZS)) and solid(plate, (lg["x"], lg["pilot_y"][0] + 0.5, ZS + 1.6))
        ok_l &= solid(plate, (lg["x"], mid, lg["top"] - 0.2)) and not solid(plate, (lg["x"], mid, lg["top"] + 0.2))
        gaps.append(S["z"]["pcb"][0] - lg["top"])
    report("4 lug di plate padat; pilot Ø2.6 horizontal sejajar lubang di dinding; puncak lug di bawah PCB", ok_l, f"(celah puncak lug ke PCB {min(gaps):.2f} mm)")
    ok_gap = True
    for lg in RK["lugs"]:
        ok_gap &= not solid(plate, (lg["x"], wall_y(lg["side"]) - lg["side"] * 0.1, 1.0)) and not solid(shell, (lg["x"], wall_y(lg["side"]) - lg["side"] * 0.1, 1.0))
    report("celah lug ke dinding dalam 0.25 mm (plate bisa dimasukkan)", ok_gap)
    # (d) lug tidak berada di bawah kaki komponen (lubang bor PCB)
    ok_lead = True; min_gap = 99
    for lg in RK["lugs"]:
        bx0, bx1 = lg["x"] - RK["lug_w"] / 2, lg["x"] + RK["lug_w"] / 2
        by0, by1 = lg["y"]
        for h in holes:
            hx, hy = -(h["xg"] - XH_), -(h["yg"] - YH_)
            dx = max(bx0 - hx, 0, hx - bx1); dy = max(by0 - hy, 0, hy - by1)
            min_gap = min(min_gap, np.hypot(dx, dy) - h["d"] / 2)
    report("lug jauh dari kaki komponen/solder PCB (>= 1.5 mm)", min_gap >= 1.5, f"(jarak terdekat {min_gap:.2f} mm)")
    # (e) alur dalam dinding untuk konektor yang menjorok: rongga alur ada, kulit luar dinding >= 1.0 mm
    for gv in RK["grooves"]:
        xm = (gv["x"][0] + gv["x"][1]) / 2; ym = (gv["y"][0] + gv["y"][1]) / 2; zm = (gv["z"][0] + gv["z"][1]) / 2
        ok_g = not solid(shell, (xm, ym, 3.0)) and not solid(shell, (xm, ym, gv["z"][1] - 0.3))
        if gv["nama"] == "jack":  skin = out_yt - (gv["y"][1])
        elif gv["nama"] == "micro":  skin = (gv["y"][0]) - out_yb
        else: skin = (gv["x"][0]) - (-out_hx)
        report(f"alur konektor '{gv['nama']}' ada dan kulit dinding luar tersisa {skin:.2f} mm (>= 1.0)", ok_g and skin >= 1.0)

print("\n=== 3. Tabrakan komponen fisik vs rumah (volume irisan harus 0) ===")
refs = sorted(glob.glob(os.path.join(R, "ref_*.stl")))
for f in refs:
    nm = os.path.basename(f)[4:-4]
    ref = trimesh.load(f)
    row = []
    for pn, pm in (("shell", shell), ("plate", plate)):
        try:
            inter = trimesh.boolean.intersection([ref, pm], engine="manifold")
            vol = abs(inter.volume) if inter is not None and len(inter.faces) else 0.0
        except Exception:
            vol = float("nan")
        row.append((pn, vol))
    if nm == "Sekrup_samping_M3":
        eng_s, eng_p = row[0][1], row[1][1]
        R_ = S["rakit"]
        eng_len = R_["screw_len"] - (S["outer"][1] - S["cavity"][1]) / 2 - R_["lug_gap"]
        exp = 4 * np.pi * (1.5 ** 2 - (R_["pilot_d"] / 2) ** 2) * eng_len
        good = eng_s < 0.5 and (exp * 0.5 < eng_p < exp * 1.3)         # shank lewat lubang dinding tanpa irisan; ulir menggigit lug
        report(f"{nm:22s}", good, f"vs shell {eng_s:.2f} mm3 (harus 0); ulir tertanam di lug {eng_p:.1f} mm3 (perkiraan {exp:.1f}, tertanam {eng_len:.2f} mm)")
    elif nm.startswith("Sekrup"):
        # sekrup M3 mengulir sendiri ke lubang pilot 2.7 mm: irisan dgn shell = volume ulir (diharapkan kecil), dgn plate = 0
        eng = row[0][1]
        exp = 4 * np.pi * (1.5 ** 2 - (S.get("pilot", 2.7) / 2) ** 2) * (S["screw"]["boss_top"] - S["z"]["split"])
        good = (exp * 0.5 < eng < exp * 1.3) and row[1][1] < 0.5   # harus ADA cengkeraman ulir (bukan 0) tapi tidak berlebihan
        report(f"{nm:22s}", good, f"ulir tertanam {eng:.1f} mm3 (perkiraan {exp:.1f}); vs plate {row[1][1]:.2f}")
    else:
        good = all((v < 0.5) for _, v in row)
        report(f"{nm:22s}", good, " ".join(f"{pn}:{v:.3f}mm3" for pn, v in row))
inter = trimesh.boolean.intersection([shell, plate], engine="manifold")
v = abs(inter.volume) if len(inter.faces) else 0.0
report("shell vs back plate saling menembus", v < 0.5, f"({v:.3f} mm3)")

if RK:
    print("\n=== 4. Sekrup samping: keterjangkauan ===")
    sc = trimesh.load(os.path.join(R, "ref_Sekrup_samping_M3.stl"))
    R_ = RK
    eng_len = R_["screw_len"] - (S["outer"][1] - S["cavity"][1]) / 2 - R_["lug_gap"]
    print(f"      M3 x {R_['screw_len']:.0f} kepala bulat Ø{R_['head_d']:.1f} x {R_['head_h']:.1f} | tembus dinding 3.0 + celah {R_['lug_gap']:.2f} | tertanam di lug {eng_len:.2f} mm (pilot {R_['pilot_depth']:.1f} mm)")
    report("tertanam di lug >= 4.5 mm (cukup untuk M3 ulir sendiri di PETG)", eng_len >= 4.5)
    report("ujung sekrup berhenti di dalam pilot (tidak tembus lug)", eng_len <= R_["pilot_depth"] - 0.2)
    tip_y_in = min(abs(sc.bounds[0][1]), abs(sc.bounds[1][1]))
    pcbm_ = trimesh.load(os.path.join(R, "ref_PCB_hijau.stl"))
    d_tip = closest_point(pcbm_, sc.sample(3000))[1].min()
    report("sekrup samping tidak menyentuh PCB (celah >= 1 mm)", d_tip >= 1.0, f"(jarak {d_tip:.2f} mm)")
    sh_ = trimesh.load(os.path.join(R, "ref_Baut_spacer.stl"))
    d_sp = closest_point(sh_, sc.sample(3000))[1].min()
    report("sekrup samping tidak menyentuh ekor baut/mur PCB (celah >= 3 mm)", d_sp >= 3.0, f"(jarak {d_sp:.2f} mm)")
else:
  print("\n=== 4. Sekrup penutup: keterjangkauan ===")
  sc = trimesh.load(os.path.join(R, "ref_Sekrup_M3x8.stl"))
  tip_z = sc.bounds[1][2]
  eng = tip_z - S["z"]["split"]
  print(f"      panjang M3 = {S['screw']['len']:.0f} mm | kepala rata di Z={S['z']['plate_bottom']:.1f} | ujung ulir di Z={tip_z:.2f} | tertanam di boss = {eng:.2f} mm")
  report("ujung sekrup tidak menyentuh PCB (celah >= 0.3 mm)", S["z"]["pcb"][0] - tip_z >= 0.3, f"(celah {S['z']['pcb'][0] - tip_z:.2f} mm)")
  report("tertanam di boss >= 4.5 mm (cukup untuk M3 ulir sendiri di PETG)", eng >= 4.5)
  report("ujung sekrup masih di dalam boss/pilot", tip_z <= S["screw"]["boss_top"] + 0.2)

print("\n=== 5. Jarak bebas (clearance) ===")
from trimesh.proximity import closest_point
for nm in ("PCB_hijau", "TFT_PCB", "Kaca_touch", "Baut_spacer", "Badan_saklar_KCD11", "Gland_PG7_+_mur"):
    f = os.path.join(R, f"ref_{nm}.stl")
    a = trimesh.load(f)
    pts = a.sample(3000)
    d_sh = closest_point(shell, pts)[1].min()
    d_pl = closest_point(plate, pts)[1].min()
    print(f"      {nm:20s} jarak min ke shell = {d_sh:.2f} mm | ke plate = {d_pl:.2f} mm")
sw = trimesh.load(os.path.join(R, "ref_Badan_saklar_KCD11.stl"))
tft = trimesh.load(os.path.join(R, "ref_TFT_PCB.stl"))
gap = tft.bounds[0][2] - sw.bounds[1][2]
report("badan saklar tidak menyentuh PCB TFT", gap >= 0.8, f"(celah vertikal {gap:.2f} mm)")

print("\n=== 6. Fitur tipis (< 0.9 mm tidak akan tercetak dengan nozzle 0.4) ===")
for nm, mesh, zs in (("shell", shell, np.arange(-0.4, 33.9, 0.25)), ("plate", plate, np.arange(-3.4, 11.8, 0.25))):
    found = []
    for z in zs:
        sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if sec is None:
            continue
        p, T = sec.to_planar()
        U = unary_union(p.polygons_full)
        lost = U.difference(U.buffer(-0.45, join_style=2).buffer(0.45, join_style=2))
        for gm in (lost.geoms if hasattr(lost, "geoms") else [lost]):
            if gm.area > 0.3:
                c = gm.centroid.coords[0]
                found.append((round(z, 2), round(gm.area, 2), np.round(trimesh.transform_points([[c[0], c[1], 0]], T)[0][:2], 1).tolist()))
    report(f"{nm}: tidak ada fitur tipis", len(found) == 0, f"({len(found)} potongan)" + (f" contoh {found[:3]}" if found else ""))

if S.get("battery"):
    print("\n=== 6b. Ruang baterai (v3): tanpa menumpuk, penyangga, jarak bebas ===")
    B = S["battery"]; C = S["cradle"]; pcb = S["pcb"]
    bat = trimesh.load(os.path.join(R, "ref_Baterai_PALO103450.stl"))
    d_sh = closest_point(shell, bat.sample(4000))[1].min()
    d_pl = closest_point(plate, bat.sample(4000))[1].min()
    report("baterai 10 x 34 x 50 muat di rongga tanpa menyentuh shell", d_sh >= 0.35, f"(jarak min {d_sh:.2f} mm)")
    report("baterai tidak menyentuh back plate (rusuk + stopper)", d_pl >= 0.1, f"(jarak min {d_pl:.2f} mm)")
    report("tepi Atas baterai berhenti sebelum tepi Bawah modul AD8232/powerbank (Y=-0.5)", B["y1"] <= -0.5 - 0.5, f"(celah {-0.5 - B['y1']:.2f} mm)")
    report("baterai 34 mm: dinding dalam Bawah ke tepi Bawah baterai", abs((B["y0"] - S["cavity_y"][0])) >= 0.35, f"(celah {B['y0'] - S['cavity_y'][0]:.2f} mm)")
    over = pcb["y0"] - B["y0"]
    print(f"      baterai menjorok {over:.2f} mm melewati tepi Bawah PCB (tepi PCB Y={pcb['y0']:.2f}); tepi dalam dinding Bawah Y={S['cavity_y'][0]:.2f}")
    ok_rib = True
    for rx_ in C["ribs_x"]:
        for yy in (C["y"][0] + 0.5, (C["y"][0] + C["y"][1]) / 2, C["y"][1] - 0.2):
            ok_rib &= solid(plate, (rx_, yy, C["top"] - 0.3)) and (not solid(plate, (rx_, yy, C["top"] + 0.3)))
    report(f"{len(C['ribs_x'])} rusuk penyangga baterai padat dan berakhir tepat di bawah alas baterai", ok_rib, f"(puncak Z={C['top']:.2f}, alas baterai Z={B['z0']:.2f})")
    ok_stop = all(solid(plate, ((a + b) / 2, (C["stop_y"][0] + C["stop_y"][1]) / 2, B["z0"] + 2.0)) for a, b in
                  ((B["x0"] - 0.4 - C["stop_w"], B["x0"] - 0.4), (B["x1"] + 0.4, B["x1"] + 0.4 + C["stop_w"])))
    report("2 stopper ujung baterai ada, di luar badan baterai", ok_stop)
    pcbm = trimesh.load(os.path.join(R, "ref_PCB_hijau.stl"))
    d_rib = closest_point(pcbm, np.array([[rx_, C["y"][1], C["top"]] for rx_ in C["ribs_x"]]))[1].min()
    report("rusuk tidak menyentuh PCB utama", d_rib >= 0.3, f"(jarak {d_rib:.2f} mm)")
    ok_bar = (B["z1"] <= S["z"]["tft"][0] - 5.0)
    report("puncak baterai (datar) >= 5 mm di bawah PCB TFT, ruang saklar/kabel aman", ok_bar, f"(puncak Z={B['z1']:.1f}, PCB TFT Z={S['z']['tft'][0]:.1f})")

print("\n=== 7. Estimasi massa (PETG 1.27 g/cm3, 3 perimeter + infill 20 % ~ 55 % volume) ===")
for nm, mesh in (("shell", shell), ("plate", plate)):
    print(f"      {nm}: volume {mesh.volume/1000:.1f} cm3 -> sekitar {mesh.volume/1000*1.27*0.55:.0f} g")
print(f"      total cover: sekitar {(shell.volume+plate.volume)/1000*1.27*0.55:.0f} g (belum termasuk elektronik)")

print("\nHASIL AKHIR:", "SEMUA LOLOS" if ok_all else "ADA YANG GAGAL")
sys.exit(0 if ok_all else 1)
