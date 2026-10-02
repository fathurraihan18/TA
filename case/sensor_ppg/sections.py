"""Gambar potongan klip (A, B, C + komponen referensi) memakai trimesh + matplotlib.
python sections.py <folder_output_make_clip> <png_keluar> [psi_derajat]"""
import sys, os, json
import numpy as np, trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly

D = sys.argv[1]; OUT = sys.argv[2]
PSI = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
R = os.path.join(D, "_ref")
S = json.load(open(os.path.join(R, "summary.json")))
XP = S["XP"]
M = {k: trimesh.load(os.path.join(R, f"{k}_desain.stl")) for k in "ABC"}
G = {k: trimesh.load(os.path.join(R, f"ref_{k}.stl")) for k in ("Modul_HW605", "Kabel_4_inti", "Kawat_bundel", "Pegas", "Sekrup_engsel")}
if PSI:
    T = trimesh.transformations.rotation_matrix(np.radians(PSI), [0, 1, 0], [XP, 0, 0])
    M["B"] = M["B"].copy(); M["B"].apply_transform(T)
COL = {"A": "#c9ccd3", "B": "#e9b872", "C": "#8fa6cf", "Modul_HW605": "#222222", "Kabel_4_inti": "#c03030", "Kawat_bundel": "#e0b020", "Pegas": "#888888", "Sekrup_engsel": "#111111"}


def draw(ax, meshes, origin, normal, uax, vax, title, xlim=None, ylim=None):
    for k, m in meshes.items():
        sec = m.section(plane_origin=origin, plane_normal=normal)
        if sec is None: continue
        for ent in sec.discrete:
            pts = np.asarray(ent)
            u = pts @ uax; v = pts @ vax
            ax.add_patch(MPoly(np.c_[u, v], closed=True, fc=COL[k], ec="k", lw=0.4, alpha=0.9, zorder=3 if k in "ABC" else 5))
    ax.set_aspect("equal"); ax.set_title(title, fontsize=7)
    if xlim: ax.set_xlim(*xlim)
    if ylim: ax.set_ylim(*ylim)
    ax.grid(True, lw=0.2); ax.tick_params(labelsize=6)


allm = {**M, **G}
fig, axs = plt.subplots(3, 3, figsize=(18, 12))
X = np.array([1, 0, 0]); Y = np.array([0, 1, 0]); Z = np.array([0, 0, 1])
draw(axs[0, 0], allm, [0, 0, 0], Y, X, Z, "potongan XZ di y=0", (-2, 70), (-15, 14))
draw(axs[0, 1], allm, [0, -8.4, 0], Y, X, Z, "potongan XZ di y=-8,4 (terowongan kabel)", (-2, 70), (-15, 14))
draw(axs[0, 2], allm, [0, 4.5, 0], Y, X, Z, "potongan XZ di y=+4,5 (lug engsel)", (-2, 70), (-15, 14))
for ax, x0 in zip(axs[1], (22.0, 28.0, 33.0)):
    draw(ax, allm, [x0, 0, 0], X, Y, Z, f"potongan YZ di x={x0}", (-14, 14), (-15, 14))
for ax, x0 in zip(axs[2], (46.0, 55.0, 63.0)):
    draw(ax, allm, [x0, 0, 0], X, Y, Z, f"potongan YZ di x={x0}", (-14, 14), (-15, 14))
fig.suptitle(f"Klip PPG  psi={PSI} derajat", fontsize=9)
fig.tight_layout()
fig.savefig(OUT, dpi=90)
print("OK", OUT)
