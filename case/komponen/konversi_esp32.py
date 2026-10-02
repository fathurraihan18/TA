"""Konversi model STEP ESP32 (esp32_Wroom_30pins_C-Type.STEP) menjadi STL per bagian (mm) yang disesuaikan dengan ESP32 38-pin Anda:
  - konektor USB-C diganti micro-USB (dibuat di make_assembly), PCB diperpanjang 2,55 mm di sisi USB,
  - baris pin dilengkapi menjadi 19 pin per baris (30 pin -> 38 pin) dengan jarak 2,54 mm, strip plastik hitam ikut dilengkapi.
python konversi_esp32.py <file.STEP> <folder_keluar>
Koordinat keluaran: PCB bawah z=0 (PCB atas z=1,6), pusat X=0, ujung USB di -Y, antena di +Y, baris pin x=+-12,7."""
import sys, os, json
import numpy as np, trimesh, cascadio

src, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
glb = os.path.join(out, "_esp32.glb")
cascadio.step_to_glb(src, glb, tol_linear=0.02, tol_angular=0.1, tol_relative=False)
sc = trimesh.load(glb)
G = {}
for k, g in sc.geometry.items():
    g = g.copy(); g.apply_scale(1000.0); g.merge_vertices()
    nm = (k.split("C-Type")[-1] or "_0").strip("_")
    G[nm] = g
# --- klasifikasi komponen di bagian "1" (PCB + pin + USB)
comps = G["1"].split(only_watertight=False)
pcb = [c for c in comps if np.ptp(c.bounds[:, 0]) > 25 and np.ptp(c.bounds[:, 1]) > 40]
pins = [c for c in comps if c.bounds[0][2] < -9]
usb = [c for c in comps if c.bounds[0][1] < -20.2 and abs(c.centroid[0]) < 5.5 and c not in pcb and c not in pins]
rest = [c for c in comps if all(c is not x for x in pcb + pins + usb)]
print("bagian 1:", len(comps), "komponen -> pcb", len(pcb), "pin", len(pins), "usb", len(usb), "lain", len(rest))
EXT = 2.54 + 0.01                      # perpanjangan PCB di sisi USB
# --- PCB: geser titik-titik ujung (y < -25) sebesar -EXT
P = trimesh.util.concatenate(pcb)
v = P.vertices.copy()
v[v[:, 1] < -25.0, 1] -= EXT
P = trimesh.Trimesh(v, P.faces, process=False)
# --- pin 15 -> 19 per baris (tambah 4 pin di sisi USB), strip plastik "9" ikut
pin_all = trimesh.util.concatenate(pins)
pins_ext = [pin_all]
for kk in range(1, 5):
    c = pin_all.copy(); c.apply_translation([0, -2.54 * kk, 0]); pins_ext.append(c)
PIN = trimesh.util.concatenate(pins_ext)
st = G["9"]
st_ext = [st]
# strip: 150 komponen kecil; gandakan bagian ujung (y < -15) sebanyak 4 kali bergeser
sc_comps = st.split(only_watertight=False)
cell = [c for c in sc_comps if c.centroid[1] < -15.2]
for kk in range(1, 5):
    for c in cell:
        c2 = c.copy(); c2.apply_translation([0, -2.54 * kk, 0]); st_ext.append(c2)
STRIP = trimesh.util.concatenate(st_ext)
# --- simpan
parts = {
    "pcb": (P, [0.02, 0.025, 0.03]),
    "pin": (PIN, [0.8, 0.72, 0.4]),
    "strip": (STRIP, [0.03, 0.03, 0.03]),
    "perisai": (G["7"], [0.8, 0.8, 0.82]),
    "teks_perisai": (G["2"], [0.05, 0.05, 0.06]),
    "modul_pcb": (G["3"], [0.12, 0.12, 0.14]),
    "smd_a": (G["0"], [0.55, 0.52, 0.42]),
    "smd_b": (G["4"], [0.05, 0.04, 0.04]),
    "smd_c": (G["5"], [0.3, 0.3, 0.3]),
    "smd_d": (G["6"], [0.35, 0.35, 0.37]),
    "tombol": (G["8"], [0.7, 0.5, 0.2]),
}
if rest:
    parts["lain"] = (trimesh.util.concatenate(rest), [0.6, 0.6, 0.62])
info = {}
for k, (m, col) in parts.items():
    path = os.path.join(out, f"esp32_{k}.stl")
    m.export(path)
    info[k] = dict(file=os.path.basename(path), color=col, bounds=np.round(m.bounds, 2).tolist())
json.dump(info, open(os.path.join(out, "esp32_parts.json"), "w"), indent=1)
allm = trimesh.util.concatenate([m for m, _ in parts.values()])
print("total bounds", np.round(allm.bounds, 2).tolist())
os.remove(glb)

# --- untuk pratinjau (render_komponen): tambahkan konektor micro-USB (menggantikan USB-C pada STEP); pada rakitan
#     konektor ini dibuat oleh make_assembly.py, jadi daftar ini TIDAK dipakai di sana (esp32_parts.json tetap tanpa USB)
def _box(x0, x1, y0, y1, z0, z1):
    m = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0)); m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)); return m
_pv = dict(info)
for k, (m_, col) in {"usb": (_box(-3.75, 3.75, -29.93, -24.33, 0.0, 2.6), [0.75, 0.75, 0.78]),
                     "usb_slot": (_box(-2.7, 2.7, -29.98, -29.43, 0.8, 1.8), [0.02, 0.025, 0.03])}.items():
    path = os.path.join(out, f"esp32_{k}.stl"); m_.export(path)
    _pv[k] = dict(file=os.path.basename(path), color=col, bounds=np.round(m_.bounds, 2).tolist())
json.dump(_pv, open(os.path.join(out, "render_parts.json"), "w"), indent=1)
