"""Uji tabrakan perakitan: setiap komponen vs shell/back plate, dan antar komponen."""
import sys, os, glob, json, itertools
import numpy as np, trimesh

CASE = sys.argv[1]
D = sys.argv[2] if len(sys.argv) > 2 else os.path.join(CASE, "_ref", "asm")     # arg2 (opsional): folder STL komponen lain
shell = trimesh.load(os.path.join(CASE, "_ref", "shell_design.stl"))
plate = trimesh.load(os.path.join(CASE, "_ref", "plate_design.stl"))
objs = {}
for f in sorted(glob.glob(os.path.join(D, "*.stl"))):
    nm = os.path.basename(f)[:-4]; key = nm.split("__")[0]
    objs[nm] = (key, trimesh.load(f))
print(len(objs), "objek komponen")


def vol_sample(a, b, n=6000):
    """cadangan untuk mesh tidak kedap (model komponen impor): tebar titik di permukaan a, hitung yang jatuh di dalam b
    (dan sebaliknya); hasil = perkiraan mm3 = fraksi titik x luas permukaan x 0,5 mm (tebal kulit) -> hanya indikator"""
    tot = 0.0
    for x, y in ((a, b), (b, a)):
        if not y.is_watertight: continue
        pts = x.sample(n)
        try: inside = y.contains(pts).mean()
        except Exception: continue
        tot += inside * x.area * 0.5
    return tot


def vol(a, b):
    try:
        if a.is_watertight and b.is_watertight:
            r = trimesh.boolean.intersection([a, b], engine="manifold")
            return abs(r.volume) if r is not None and len(r.faces) else 0.0
        return vol_sample(a, b)
    except Exception:
        return vol_sample(a, b)


print("\n=== A. Komponen vs shell dan back plate (harus 0 mm3) ===")
bad = 0
for nm, (key, m) in objs.items():
    for pn, pm in (("shell", shell), ("plate", plate)):
        # prefilter bbox
        if np.any(m.bounds[1] < pm.bounds[0]) or np.any(m.bounds[0] > pm.bounds[1]):
            continue
        v = vol(m, pm)
        if v > 0.5 or v != v:
            bad += 1
            print(f"  [TABRAK] {nm:34s} vs {pn:5s} : {v:.1f} mm3")
print("  total tabrakan:", bad)

print("\n=== B. Antar komponen (kelompok berbeda) ===")
allowed = {frozenset(p) for p in [("kabel_el", "ad8232"), ("ppg", "gland"), ("standoff", "pcb"), ("standoff", "tft"),
                                  ("esp32", "pcb"), ("sekrup", "plate"), ("ad8232", "pcb")]}
pairs = {}
names = list(objs)
for a, b in itertools.combinations(names, 2):
    ka, kb = objs[a][0], objs[b][0]
    if ka == kb: continue
    ma, mb = objs[a][1], objs[b][1]
    if np.any(ma.bounds[1] < mb.bounds[0] + 1e-6) or np.any(mb.bounds[1] < ma.bounds[0] + 1e-6):
        continue
    v = vol(ma, mb)
    if v > 0.5 or v != v:
        pairs[(ka, kb)] = pairs.get((ka, kb), 0) + (0 if v != v else v)
        pairs.setdefault(("det", ka, kb), []).append((a, b, round(v, 1)))
for k, v in pairs.items():
    if k[0] == "det": continue
    tag = "diizinkan (menyatu/menembus rumah/konektor)" if frozenset(k) in allowed else "PERHATIAN"
    print(f"  {k[0]:9s} x {k[1]:9s}  {v:8.1f} mm3   -> {tag}")
    if tag == "PERHATIAN":
        for d in pairs[("det",) + k][:4]:
            print("       ", d)
