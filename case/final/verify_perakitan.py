"""Uji tabrakan rakitan v2d (bingkai asm): setiap pasang bagian dari kelompok berbeda dihitung irisan volumenya (manifold3d).
Kelompok: shell, plate, penahan, sekrup, pcb, tft, esp32, ad8232, boost, baterai, standoff, gland, saklar, kabel, klip.
python verify_perakitan.py <folder_v2d>
"""
import sys, os, glob, json, itertools
import numpy as np, trimesh, manifold3d as m3d

D = sys.argv[1]
REF = os.path.join(D, "_ref"); ASM = os.path.join(REF, "asm")
parts = []                                              # (kelompok, nama, trimesh)


def add(g, name, path):
    m = trimesh.load(path, force="mesh")
    m.merge_vertices()
    parts.append((g, name, m))


add("shell", "shell", os.path.join(REF, "shell_design.stl"))
add("plate", "plate", os.path.join(REF, "plate_design.stl"))
add("penahan", "penahan", os.path.join(REF, "penahan_design.stl"))
for f in sorted(glob.glob(os.path.join(ASM, "*__*.stl"))):
    g = os.path.basename(f).split("__")[0]
    if g in ("kabel_el", "ppg"): continue               # kabel luar/klip berada di luar casing
    add({"pcb": "pcb", "esp32": "esp32", "ad8232": "ad8232", "boost": "boost", "baterai": "baterai", "gland": "gland"}.get(g, g), os.path.basename(f)[:-4], f)
for f in glob.glob(os.path.join(REF, "ref_Sekrup_M3x8.stl")) + glob.glob(os.path.join(REF, "ref_Baut_spacer.stl")) + glob.glob(os.path.join(REF, "ref_Badan_saklar_KCD11.stl")) + glob.glob(os.path.join(REF, "ref_TFT_PCB.stl")) + glob.glob(os.path.join(REF, "ref_Kaca_touch.stl")):
    n = os.path.basename(f)[4:-4]
    g = {"Sekrup_M3x8": "sekrup", "Baut_spacer": "standoff", "Badan_saklar_KCD11": "saklar", "TFT_PCB": "tft", "Kaca_touch": "tft"}[n]
    add(g, n, f)


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


res = {}
for (ga, na, ma), (gb, nb, mb) in itertools.combinations(parts, 2):
    if ga == gb: continue
    if np.any(ma.bounds[1] < mb.bounds[0]) or np.any(mb.bounds[1] < ma.bounds[0]): continue
    try:
        v = (man(ma) ^ man(mb)).volume()
    except Exception as e:
        v = -1
    if v > 0.5:
        key = tuple(sorted((ga, gb)))
        res.setdefault(key, []).append((na, nb, v))
print("Kelompok yang saling menembus (irisan > 0,5 mm3):")
if not res: print("  tidak ada")
for k, lst in sorted(res.items()):
    print(f"  {k[0]} x {k[1]}: {sum(x[2] for x in lst):.1f} mm3 ({len(lst)} pasang)")
print("jumlah bagian diuji:", len(parts))
