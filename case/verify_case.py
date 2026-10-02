"""Verifikasi otomatis cover: mesh rapat, ukuran/posisi lubang, dan tabrakan dengan komponen fisik."""
import sys, os, json, glob
import numpy as np
import trimesh

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


print("=== 1. Integritas mesh ===")
for nm, m in (("shell", shell), ("plate", plate)):
    report(f"{nm} watertight", m.is_watertight, f"| winding konsisten={m.is_winding_consistent} | volume={m.volume:.0f} mm3")
    b = m.bounds
    print(f"      bbox X[{b[0][0]:.2f},{b[1][0]:.2f}] Y[{b[0][1]:.2f},{b[1][1]:.2f}] Z[{b[0][2]:.2f},{b[1][2]:.2f}]  -> {np.ptp(b[:,0]):.2f} x {np.ptp(b[:,1]):.2f} x {np.ptp(b[:,2]):.2f} mm")
    parts = m.split(only_watertight=False)
    report(f"{nm} satu badan utuh", len(parts) == 1, f"({len(parts)} komponen terpisah)")

print("\n=== 2. Probe lubang (titik DI DALAM lubang harus kosong, titik TEPI harus padat) ===")


def solid(p):
    return bool(shell.contains(np.array([p], float))[0])


def probe_rect_x(name, ycen, zc, w, h, xs):  # lubang menembus sumbu X
    inside = [(x, ycen + sy * (w / 2 - 0.1), zc + sz * (h / 2 - 0.1)) for x in xs for sy in (-1, 1) for sz in (-1, 1)] + [(x, ycen, zc) for x in xs]
    outside = [(x, ycen + sy * (w / 2 + 0.25), zc) for x in xs for sy in (-1, 1)] + [(x, ycen, zc + sz * (h / 2 + 0.25)) for x in xs for sz in (-1, 1)]
    return all(not solid(p) for p in inside) and all(solid(p) for p in outside)


def probe_rect_y(name, xcen, zc, w, h, ys):
    inside = [(xcen + sx * (w / 2 - 0.1), y, zc + sz * (h / 2 - 0.1)) for y in ys for sx in (-1, 1) for sz in (-1, 1)] + [(xcen, y, zc) for y in ys]
    outside = [(xcen + sx * (w / 2 + 0.25), y, zc) for y in ys for sx in (-1, 1)] + [(xcen, y, zc + sz * (h / 2 + 0.25)) for y in ys for sz in (-1, 1)]
    return all(not solid(p) for p in inside) and all(solid(p) for p in outside)


tol = 0.2
m = S["micro"]; j = S["jack"]; u = S["usbc"]; g = S["gland"]; s = S["switch"]
cav_hy = S["cavity"][1] / 2; cav_hx = S["cavity"][0] / 2
out_hy = S["outer"][1] / 2; out_hx = S["outer"][0] / 2

report("micro-USB (BAWAH) 12.2 x 8.2 mm", probe_rect_y("micro", m["x"], m["zc"], m["w"] + tol, m["h"] + tol, [-cav_hy - 1.5, -cav_hy - 2.8]))
# jack: lubang bulat
ang = np.linspace(0, 2 * np.pi, 12, endpoint=False)
r_in, r_out = (j["d"] + tol) / 2 - 0.1, (j["d"] + tol) / 2 + 0.25
ins = [(j["x"] + r_in * np.cos(a), y, j["zc"] + r_in * np.sin(a)) for a in ang for y in (cav_hy + 1.0, cav_hy + 2.5)]
outs = [(j["x"] + r_out * np.cos(a), y, j["zc"] + r_out * np.sin(a)) for a in ang for y in (cav_hy + 1.0, cav_hy + 2.5)]
report("jack AD8232 (ATAS) bulat d=7.2 mm", all(not solid(p) for p in ins) and all(solid(p) for p in outs))
report("USB-C powerbank (KANAN) 10.4 x 4.6 mm", probe_rect_x("usbc", u["y"], u["zc"], u["w"] + tol, u["h"] + tol, [-cav_hx - 1.0, -cav_hx - 2.5]))
# gland: lubang bulat d=19 menembus pelat tebal 3 mm
gx_mid = -(out_hx + g["out"] - g["plate"] / 2)
r_in, r_out = g["hole"] / 2 - 0.1, g["hole"] / 2 + 0.3
ins = [(gx_mid, g["y"] + r_in * np.cos(a), g["zc"] + r_in * np.sin(a)) for a in ang]
outs = [(gx_mid, g["y"] + r_out * np.cos(a), g["zc"] + r_out * np.sin(a)) for a in ang]
report("gland PG11 lubang d=19.0 mm", all(not solid(p) for p in ins) and all(solid(p) for p in outs))
# kantong mur segi-enam harus kosong di dalam, dan harus ada dinding
R_hex = g["nut_af"] / np.sqrt(3)
x_pocket = -(out_hx + g["out"] - g["plate"] - 2.0)
ins = [(x_pocket, g["y"] + (R_hex - 0.5) * np.cos(np.radians(90 + 60 * k)), g["zc"] + (R_hex - 0.5) * np.sin(np.radians(90 + 60 * k))) for k in range(6)]
report("kantong mur segi-enam (AF 24.6) kosong", all(not solid(p) for p in ins))
# saklar: jendela panel 13.7 x 9.2
y_panel = out_hy + s["out"] - s["panel"] / 2
pts_in = [(s["x"] + sx * 6.7, y_panel, s["zc"] + sz * 4.4) for sx in (-1, 1) for sz in (-1, 1)] + [(s["x"], y_panel, s["zc"])]
pts_out = [(s["x"] + sx * 7.05, y_panel, s["zc"]) for sx in (-1, 1)] + [(s["x"], y_panel, s["zc"] + sz * 4.9) for sz in (-1, 1)]
report("saklar KCD11 jendela 13.7 x 9.2 mm", all(not solid(p) for p in pts_in) and all(solid(p) for p in pts_out))
# jendela layar
w = S["window"]
pin = [(w[2] + sx * (w[0] / 2 - 0.9), sy * (w[1] / 2 - 0.9), 32.7) for sx in (-1, 1) for sy in (-1, 1)] + [(w[2], 0, 32.7)]  # sudut membulat r=2
pout = [(w[2] + sx * (w[0] / 2 + 0.3), 0, 32.7) for sx in (-1, 1)] + [(w[2], sy * (w[1] / 2 + 0.3), 32.7) for sy in (-1, 1)]
report("jendela layar 79 x 52 mm", all(not solid(p) for p in pin) and all(solid(p) for p in pout))

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
        except Exception as e:
            vol = float("nan")
        row.append((pn, vol))
    good = all((v < 0.5) for _, v in row)
    report(f"{nm:22s}", good, " ".join(f"{pn}:{v:.3f}mm3" for pn, v in row))

inter = trimesh.boolean.intersection([shell, plate], engine="manifold")
v = abs(inter.volume) if len(inter.faces) else 0.0
report("shell vs back plate saling menembus", v < 0.5, f"({v:.3f} mm3)")

print("\n=== 4. Jarak bebas (clearance) ===")
from trimesh.proximity import closest_point


def mindist(a_name, a_path, mesh):
    a = trimesh.load(a_path)
    pts = a.sample(4000)
    _, d, _ = closest_point(mesh, pts)
    return d.min()


for nm in ("PCB_hijau", "TFT_PCB", "Kaca_touch", "Baut_spacer"):
    f = os.path.join(R, f"ref_{nm}.stl")
    d_sh = mindist(nm, f, shell)
    d_pl = mindist(nm, f, plate)
    print(f"      {nm:14s} jarak min ke shell = {d_sh:.2f} mm | ke plate = {d_pl:.2f} mm")

print("\nHASIL AKHIR:", "SEMUA LOLOS" if ok_all else "ADA YANG GAGAL")
sys.exit(0 if ok_all else 1)
