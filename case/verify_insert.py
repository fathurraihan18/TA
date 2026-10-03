"""Uji URUTAN PERAKITAN: apakah tumpukan rangkaian (TFT + standoff + PCB + modul) bisa dimasukkan dari belakang rongga shell
dengan gerakan lurus (+Z), dan apakah back plate bisa dipasang sesudahnya?

python verify_insert.py <folder_case> [langkah_mm]

Tumpukan digeser dari posisi di luar shell (d = tinggi tumpukan) sampai posisi akhir (d = 0); pada tiap langkah dihitung
irisan tiap komponen dengan shell. Komponen yang dipasang dari luar sesudahnya (saklar, gland, plug jack, sekrup, baterai
yang direkat belakangan) tidak diikutkan. Konektor yang menembus lubang dinding (micro-USB, USB-C, hidung jack) memang
mengiris dinding bila tidak ada alur: itu ikut dilaporkan.
"""
import sys, os, json, glob
import numpy as np, trimesh

CASE = sys.argv[1]
STEP = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
R = os.path.join(CASE, "_ref")
shell = trimesh.load(os.path.join(R, "shell_design.stl"))
plate = trimesh.load(os.path.join(R, "plate_design.stl"))
S = json.load(open(os.path.join(R, "summary.json")))

SKIP = {"Sekrup_M3x8", "Sekrup_samping_M3", "Badan_saklar_KCD11", "Gland_PG7_+_mur", "Area_aktif"}      # dipasang dari luar / bukan bagian padat
parts = {}
for f in sorted(glob.glob(os.path.join(R, "ref_*.stl"))):
    nm = os.path.basename(f)[4:-4]
    if nm in SKIP: continue
    m = trimesh.load(f)
    if nm == "Plug_jack_AD8232":                       # hanya laras jack di papan; plug kabel dipasang dari luar sesudahnya
        m = m.slice_plane([0, 29.7, 0], [0, -1, 0], cap=True)
    parts[nm] = m
zmax = max(m.bounds[1][2] for m in parts.values())
print(f"{len(parts)} bagian tumpukan: {', '.join(parts)}; tinggi total sampai Z = {zmax:.1f} mm")


def vol(a, b):
    if np.any(a.bounds[1] < b.bounds[0]) or np.any(a.bounds[0] > b.bounds[1]):
        return 0.0
    try:
        r = trimesh.boolean.intersection([a, b], engine="manifold")
        return abs(r.volume) if r is not None and len(r.faces) else 0.0
    except Exception:
        return float("nan")


z_split = S["z"]["split"]
d0 = zmax - z_split + 1.0
ds = list(np.arange(d0, -1e-9, -STEP)) + [0.0]
first = {}
worst = {}
for d in ds:
    for nm, m in parts.items():
        mm = m.copy(); mm.apply_translation((0, 0, -d))
        v = vol(mm, shell)
        if v > 0.3 or v != v:
            first.setdefault(nm, d); worst[nm] = max(worst.get(nm, 0), 0 if v != v else v)
print(f"\nGeser tumpukan lurus ke depan dari d = {d0:.0f} mm (di luar shell) sampai d = 0 (posisi akhir), langkah {STEP} mm")
if not first:
    print("[OK ] tidak ada irisan sepanjang jalur: tumpukan bisa dimasukkan lurus dari belakang.")
else:
    for nm in first:
        print(f"[TABRAK] {nm:22s} mulai menabrak shell pada d = {first[nm]:5.1f} mm, irisan terbesar {worst[nm]:8.1f} mm3")

# back plate dipasang terakhir: tidak boleh menabrak shell maupun tumpukan pada posisi akhir (selain pin masuk soket)
print("\nBack plate (posisi akhir) terhadap tumpukan dan shell:")
bad = 0
for nm, m in parts.items():
    v = vol(m, plate)
    if v > 0.3:
        bad += 1; print(f"  [TABRAK] plate x {nm}: {v:.1f} mm3")
v = vol(shell, plate)
if v > 0.3:
    bad += 1; print(f"  [TABRAK] plate x shell: {v:.1f} mm3")
if not bad:
    print("  [OK ] plate tidak menabrak apa pun pada posisi akhir")

# plate dipasang dari belakang dengan gerakan lurus: tidak boleh menabrak shell di sepanjang jalur (plate masuk dari d=zlim ke 0)
print("\nPlate digeser lurus dari belakang (tumpukan sudah di dalam):")
first_p = {}
for d in np.arange(6.0, -1e-9, -STEP):
    pm = plate.copy(); pm.apply_translation((0, 0, -d))
    for nm, tgt in (("shell", shell),) + tuple(parts.items()):
        v = vol(pm, tgt)
        if v > 0.3 and nm not in first_p:
            first_p[nm] = (d, v)
if not first_p:
    print("  [OK ] plate masuk tanpa menabrak shell atau komponen")
else:
    for nm, (d, v) in first_p.items():
        print(f"  [TABRAK] plate mulai menabrak {nm} pada d = {d:.1f} mm ({v:.1f} mm3)")
