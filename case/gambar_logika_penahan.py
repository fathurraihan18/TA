"""Gambar 'logika gaya' penahan: ke mana beban sekrup dan beban pelepasan plate mengalir, dan mengapa penahan harus menempel ke shell.
python gambar_logika_penahan.py <folder_penahan> <berkas_png>
"""
import sys, os, json, textwrap
import numpy as np, trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from shapely.geometry import Polygon

D, OUTF = sys.argv[1:3]
R = os.path.join(D, "_ref")
S = json.load(open(os.path.join(R, "summary.json"))); P = S["penahan"]
XS = P["blocks"][0]["x"]


def sec(fn):
    m = trimesh.load(os.path.join(R, fn)); sc = m.section(plane_origin=[XS, 0, 0], plane_normal=[1, 0, 0])
    acc = None
    for loop in sc.discrete:
        pg = Polygon(np.c_[loop[:, 1], loop[:, 2]]); pg = pg if pg.is_valid else pg.buffer(0)
        acc = pg if acc is None else acc.symmetric_difference(pg)
    return acc


def draw(ax, g, fc, z=2):
    for gg in (g.geoms if hasattr(g, "geoms") else [g]):
        if gg.geom_type != "Polygon" or gg.is_empty: continue
        v = [np.asarray(gg.exterior.coords)]; c = [[Path.MOVETO] + [Path.LINETO] * (len(v[0]) - 2) + [Path.CLOSEPOLY]]
        for h in gg.interiors:
            hp = np.asarray(h.coords); v.append(hp); c.append([Path.MOVETO] + [Path.LINETO] * (len(hp) - 2) + [Path.CLOSEPOLY])
        ax.add_patch(PathPatch(Path(np.vstack(v), np.concatenate(c)), fc=fc, ec="k", lw=0.5, zorder=z))


fig = plt.figure(figsize=(16.54, 8.4), dpi=200); fig.patch.set_facecolor("white")
fig.text(0.5, 0.955, "Logika penahan: mengapa harus menempel ke shell, dan mengapa tidak lepas", ha="center", fontsize=17, fontweight="bold")
yb, yt = S["cavity_y"]
ax = fig.add_axes([0.03, 0.10, 0.50, 0.78]); ax.axis("off")
y0, y1, z0, z1 = yt - 17.5, yt + 5.0, -6.2, 9.2
for fn, col in (("shell_design.stl", "#e8a04a"), ("plate_design.stl", "#454750"), ("penahan_design.stl", "#ea1a8c"), ("ref_PCB_hijau.stl", "#2e9a55")):
    draw(ax, sec(fn), col, 2 if fn != "penahan_design.stl" else 3)
draw(ax, sec("ref_Sekrup_M3x8.stl"), "#b9bac2", 4)
blk = [b for b in P["blocks"] if b["side"] > 0][0]; ba, bb = blk["y"]
ax.add_patch(Rectangle((bb, S["z"]["split"]), P["gap"], P["top"] - S["z"]["split"], fc="#f4e842", ec="#8a7d00", lw=0.5, zorder=5))
ax.set_xlim(y0, y1); ax.set_ylim(z0, z1); ax.set_aspect("equal")


def arr(p0, p1, col, lw=2.6, style="-|>", ls="-", ms=16, z=10):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, color=col, lw=lw, mutation_scale=ms, zorder=z, linestyle=ls))


xs_ = 0.5 * (ba + bb)
# (1) sekrup menjepit plate dan penahan (saling tarik)
yl_ = ba + 0.8                                                              # jalur panah di sisi kiri sekrup, di dalam penahan dan plate
arr((yl_, -3.2), (yl_, -0.9), "#6fb0ff", lw=3.0); arr((yl_, 3.6), (yl_, 0.5), "#6fb0ff", lw=3.0)
ax.text(yl_ - 0.9, 1.6, "(1)", color="#1f4e9c", fontsize=13, fontweight="bold", ha="right", va="center", bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
# (2) beban pelepasan: tarikan luar pada plate
arr((yt - 0.5, -2.0), (yt - 0.5, -5.9), "#c00000", lw=3.2)
ax.text(yt - 1.4, -5.6, "(2)", color="#c00000", fontsize=13, fontweight="bold", ha="right", va="center")
# (3) jalur beban: plate -> sekrup -> penahan -> epoxy -> dinding
for (p0, p1) in (((xs_ + 3.7, -2.0), (xs_ + 3.7, 0.2)), ((xs_ + 3.7, 2.8), ((bb + 0.15), 2.8))):
    pass
arr((xs_ + 0.1, -2.6), (xs_ + 0.1, 2.9), "#e07000", lw=2.0, ls="--")
arr((xs_ + 0.1, 2.9), (bb + 0.15, 2.9), "#e07000", lw=2.0, ls="--")
arr((bb + 0.15, 2.9), (bb + 1.8, 2.9), "#e07000", lw=2.0, ls="--")
ax.text(bb + 0.4, 5.2, "(3)", color="#e07000", fontsize=13, fontweight="bold", va="center")
ax.text(y0 + 0.2, 8.6, "PCB utama", color="#1e6b3a", fontsize=11, fontweight="bold")
ax.text(y0 + 0.2, -3.0, "back plate v2", color="white", fontsize=11, fontweight="bold")
ax.text(xs_ - 3.4, 3.9, "penahan", color="#7a0040", fontsize=10, fontweight="bold", ha="right", va="center", bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.9))
ax.text(yt + 2.4, 5.0, "dinding\nshell", color="#5b3508", fontsize=10, fontweight="bold", ha="center", va="center", zorder=9)
ax.annotate("epoxy", xy=(bb + 0.15, 0.2), xytext=(bb - 3.3, -0.6), fontsize=10, color="#8a7d00", fontweight="bold", arrowprops=dict(arrowstyle="-", lw=0.8, color="#8a7d00"), zorder=9)

txt = [("(1)  Sekrup M3 dari belakang", "menarik PLATE ke atas dan PENAHAN ke bawah: keduanya saling menjepit. Gaya sekrup berputar di dalam pasangan sekrup-penahan-plate dan TIDAK membebani shell. Itu sebabnya sekrup boleh dikencangkan tanpa takut merobek lem."),
       ("(2)  Plate hanya akan lepas bila ditarik ke belakang", "(guncangan, tarikan sabuk). Plate ditahan sekrup, sekrup ditahan penahan."),
       ("(3)  Beban itu diteruskan penahan ke dinding lewat EPOXY.", "Jadi satu-satunya penghubung ke shell adalah bidang lem. Maka: bidang lem harus LUAS, bersih, dan kasar (diamplas), dan beban lepas sebenarnya kecil dibanding kekuatan lem."),
       ("Mengapa penahan tidak bisa 'hanya tertahan bentuk':", "dinding dalam shell rata (tidak ada tonjolan atau lekuk untuk dikait) dan penahan berada di bawah PCB. Menjepit plate dari luar (seperti jig) tidak menahan apa pun karena jig tidak terikat ke shell. Satu-satunya cara tanpa lem adalah mengait lewat lubang di dinding (sekrup samping, v2b).")]
yy = 0.86
for hd, body in txt:
    fig.text(0.56, yy, hd, fontsize=12, fontweight="bold", va="top")
    fig.text(0.56, yy - 0.040, "\n".join(textwrap.wrap(body, 78)), fontsize=10.2, va="top", color="#222222")
    yy -= 0.040 + 0.030 * (len(textwrap.wrap(body, 78))) + 0.040
# tabel luas lem
rows = []
for pc in P.get("pieces", [dict(nama="blok", x=[b["x"] - P["w"] / 2, b["x"] + P["w"] / 2], zbar=[-0.5, P["top"]], feet=[b["x"]]) for b in P["blocks"]]):
    L = pc["x"][1] - pc["x"][0]; zb = pc["zbar"]
    area = L * (zb[1] - zb[0]) + (sum(P["w"] * (zb[0] - S["z"]["split"]) for _ in pc["feet"]) if zb[0] > S["z"]["split"] else 0)
    rows.append((pc["nama"], L, area))
tot = sum(r[2] for r in rows)
fig.text(0.56, 0.145, "Luas bidang lem (penahan terhadap dinding):\n" + "   |   ".join(f"{n} {a:.0f} mm2" for n, L, a in rows) + f"   |   total {tot:.0f} mm2",
         fontsize=10, fontweight="bold", color="#1f4e9c", va="top")
fig.text(0.56, 0.095, "\n".join(textwrap.wrap("Epoxy pada PETG yang diamplas: geser sekitar 2-4 MPa, jadi kemampuan sebenarnya ratusan newton (perkiraan; belum diuji pada printer dan epoxy Anda).", 92)), fontsize=9, color="#444444", va="top")
fig.text(0.03, 0.018, "Warna: panah biru = gaya sekrup, merah = tarikan luar pada plate, jingga putus-putus = jalur beban. Potongan melalui sumbu sekrup (x = 23 mm).", fontsize=9, color="#444444")
fig.savefig(OUTF, dpi=200)
print("OK", OUTF)
