"""Susun lembar visual pemasangan penahan sekrup (varian --penahan): langkah 1-4, hasil, dan potongan melalui penahan.
python gambar_pemasangan.py <folder_penahan> <folder_render> <berkas_keluaran_png>
  folder_render berisi langkah1..3.png, hasil_belakang.png, hasil_dalam.png dari render_pemasangan.py
"""
import sys, os, json, textwrap
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Rectangle
from shapely.geometry import Polygon
from PIL import Image

D, REN, OUTF = sys.argv[1:4]
R = os.path.join(D, "_ref")
S = json.load(open(os.path.join(R, "summary.json")))
P = S["penahan"]
XS = P["blocks"][0]["x"]                                   # bidang potong melalui sumbu sekrup (x = 23)


def section_polys(path, x0, clip=None):
    m = trimesh.load(path)
    sec = m.section(plane_origin=[x0, 0, 0], plane_normal=[1, 0, 0])
    if sec is None: return None
    acc = None
    for loop in sec.discrete:
        pg = Polygon(np.c_[loop[:, 1], loop[:, 2]])
        if not pg.is_valid: pg = pg.buffer(0)
        acc = pg if acc is None else acc.symmetric_difference(pg)
    return acc


def draw(ax, geom, fc, ec="k", lw=0.6, z=2, alpha=1.0, hatch=None):
    if geom is None or geom.is_empty: return
    for g in (geom.geoms if hasattr(geom, "geoms") else [geom]):
        if g.is_empty or g.geom_type != "Polygon": continue
        pts = np.asarray(g.exterior.coords)
        # lubang: polygon dengan hole -> compound path
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch
        verts = [pts]; codes = [[Path.MOVETO] + [Path.LINETO] * (len(pts) - 2) + [Path.CLOSEPOLY]]
        for h in g.interiors:
            hp = np.asarray(h.coords); verts.append(hp); codes.append([Path.MOVETO] + [Path.LINETO] * (len(hp) - 2) + [Path.CLOSEPOLY])
        ax.add_patch(PathPatch(Path(np.vstack(verts), np.concatenate(codes)), fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, hatch=hatch))


PARTS = [("shell_design.stl", "#e8a04a", "dinding shell"), ("plate_design.stl", "#454750", "back plate v2"),
         ("penahan_design.stl", "#ea1a8c", "penahan sekrup"), ("ref_PCB_hijau.stl", "#2e9a55", "PCB utama"),
         ("ref_Sekrup_M3x8.stl", "#b9bac2", "sekrup M3 x 8 flat head"), ("ref_TFT_PCB.stl", "#c02020", "PCB TFT"), ("ref_Kaca_touch.stl", "#1d2430", "kaca touch")]
SEC = {fn: section_polys(os.path.join(R, fn), XS) for fn, _, _ in PARTS}
SEC0 = {fn: section_polys(os.path.join(R, fn), 0.0) for fn, _, _ in PARTS}      # potongan di x = 0 (melalui batang strip, di atas rim plate)


def section_axes(ax, ylim, zlim, detail, sec=None):
    sec = sec or SEC
    for fn, col, nm in PARTS:
        if fn == "ref_Sekrup_M3x8.stl": continue
        draw(ax, sec[fn], col, z=2 if fn != "penahan_design.stl" else 3, lw=0.5 if detail else 0.3)
    draw(ax, sec["ref_Sekrup_M3x8.stl"], PARTS[4][1], z=4, lw=0.6)
    ax.set_xlim(*ylim); ax.set_ylim(*zlim); ax.set_aspect("equal"); ax.axis("off")


fig = plt.figure(figsize=(16.54, 11.69), dpi=200)
fig.patch.set_facecolor("white")
fig.text(0.5, 0.965, f"Pemasangan penahan sekrup ({os.path.basename(os.path.normpath(D)).split('_')[0]}): plate v2 dan 4 sekrup M3 x 8 dari belakang TIDAK berubah", ha="center", va="center", fontsize=17, fontweight="bold")
fig.text(0.5, 0.940, "Shell v2 yang bossnya sudah dipotong  |  penahan dicetak terpisah, dilem ke dinding sesudah tumpukan masuk  |  plate dipakai sebagai jig", ha="center", va="center", fontsize=10.5, color="#444444")

W, H = 0.30, 0.36
cells = [(0.025, 0.515), (0.350, 0.515), (0.675, 0.515), (0.025, 0.100), (0.350, 0.100)]
caps = [("1", "Tumpukan masuk lurus dari belakang", "TFT + standoff + PCB + modul didorong ke shell. Dinding dalam rata (bos sudah dibuang), tidak ada yang menghalangi."),
        ("2", "Penahan dipasang pada plate", ("Penahan (magenta): kaki-kakinya masuk ke celah rim plate, batangnya melintas di atas rim. " if P.get("strip") else "4 penahan (magenta) diletakkan di celah rim plate. ") + "4 sekrup M3 x 8 dari belakang plate menggigit penahan (cukup menempel)."),
        ("3", "Oleskan epoxy, masukkan plate + penahan", "Epoxy (kuning) tipis hanya pada muka penahan yang menghadap dinding. Tiang plate melingkupi ekor baut, penahan menyusur dinding di bawah PCB."),
        ("4", "Epoxy keras: penahan menempel di shell", "Lepas 4 sekrup dan plate. Penahan (magenta) tinggal di dinding, 0,7 mm di bawah PCB. Lalu pasang plate + 4 sekrup seperti v2."),
        ("5", "Hasil: tampak belakang", "Kepala sekrup flat head rata dengan plate: lubang tertutup, PCB dan solder tidak terlihat/tersentuh kulit.")]
imgs = ["langkah1.png", "langkah2.png", "langkah3.png", "hasil_dalam.png", "hasil_belakang.png"]
for (x, y), (no, ttl, cap), fn in zip(cells, caps, imgs):
    ax = fig.add_axes([x, y + 0.045, W, H - 0.045]); ax.axis("off")
    n_ = len(textwrap.wrap(cap, 70))
    im = Image.open(os.path.join(REN, fn)).convert("RGBA")
    a = np.asarray(im)[..., 3]; ys, xs = np.where(a > 8)
    pad = 20
    im = im.crop((max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, im.width), min(ys.max() + pad, im.height)))
    ax.imshow(np.asarray(im)); ax.set_xticks([]); ax.set_yticks([])
    if no in ("1", "3"):
        ax.annotate("dorong lurus\nke dalam", xy=(0.93, 0.62), xycoords="axes fraction", xytext=(0.93, 0.18), textcoords="axes fraction", ha="center", va="center", fontsize=9, color="#1f4e9c", fontweight="bold",
                    arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#1f4e9c", mutation_scale=18))
    fig.text(x + 0.005, y + H + 0.012, no, fontsize=17, fontweight="bold", color="white", ha="center", va="center",
             bbox=dict(boxstyle="circle,pad=0.35", fc="#1f4e9c", ec="none"))
    fig.text(x + 0.022, y + H + 0.012, ttl, fontsize=11.5, fontweight="bold", va="center")
    fig.text(x + 0.002, y + 0.040, "\n".join(textwrap.wrap(cap, 70)), fontsize=8.6, va="top", color="#222222")

# --- potongan melalui sumbu sekrup (x = 23): detail dinding Atas (besar) + penampang penuh (kecil)
X6, Y6 = 0.675, 0.100
fig.text(X6 + 0.005, Y6 + H + 0.012, "6", fontsize=17, fontweight="bold", color="white", ha="center", va="center", bbox=dict(boxstyle="circle,pad=0.35", fc="#1f4e9c", ec="none"))
fig.text(X6 + 0.022, Y6 + H + 0.012, f"Potongan melalui sumbu sekrup (x = {XS:.0f} mm)", fontsize=11.5, fontweight="bold", va="center")
yb, yt = S["cavity_y"]
axd = fig.add_axes([X6, Y6 + 0.075, 0.150 if P.get("strip") else 0.205, H - 0.075 - 0.02]); axd.set_facecolor("white")
yd0, yd1, zd0, zd1 = yt - 11.8, yt + 3.6, -4.4, 8.8
section_axes(axd, (yd0, yd1), (zd0, zd1), True)
blk = [b for b in P["blocks"] if b["side"] > 0][0]
ba, bb = blk["y"]


def dim_h(ax, x0, x1, y, text, dy=0.9, fs=7.4, col="k"):
    ax.annotate("", xy=(x1, y), xytext=(x0, y), arrowprops=dict(arrowstyle="<|-|>", lw=0.6, color=col, mutation_scale=6, shrinkA=0, shrinkB=0), zorder=9)
    ax.text((x0 + x1) / 2, y + dy, text, fontsize=fs, ha="center", va="bottom", color=col, zorder=9, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))


def dim_v(ax, x, z0, z1, text, dx=0.35, fs=7.4, col="k", ha="left"):
    ax.annotate("", xy=(x, z1), xytext=(x, z0), arrowprops=dict(arrowstyle="<|-|>", lw=0.6, color=col, mutation_scale=6, shrinkA=0, shrinkB=0), zorder=9)
    ax.text(x + dx, (z0 + z1) / 2, text, fontsize=fs, ha=ha, va="center", color=col, zorder=9, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))


axd.add_patch(Rectangle((bb, S["z"]["split"]), P["gap"], P["top"] - S["z"]["split"], fc="#f4e842", ec="#8a7d00", lw=0.5, zorder=5))
axd.annotate(f"celah epoxy\n{P['gap']:.1f} mm", xy=(bb + P["gap"] / 2, 3.6), xytext=(yt + 0.4, 6.2), fontsize=7.4, ha="left", va="center",
             arrowprops=dict(arrowstyle="-", lw=0.6, color="#8a7d00"), zorder=9, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
dim_v(axd, yt - 7.4, P["top"], S["z"]["pcb"][0], f"{S['z']['pcb'][0] - P['top']:.1f} mm", dx=0.3)
axd.annotate("penahan", xy=(ba + 1.0, 1.6), xytext=(yd0 + 0.3, 3.0), fontsize=8, color="#b00060", fontweight="bold", arrowprops=dict(arrowstyle="-", lw=0.7, color="#b00060"), zorder=9)
axd.annotate("sekrup M3 x 8, kepala rata", xy=(0.5 * (ba + bb), -3.0), xytext=(yd0 + 0.3, -3.9), fontsize=7.6, va="top", arrowprops=dict(arrowstyle="-", lw=0.6, color="k"), zorder=9)
axd.annotate("PCB utama", xy=(yd0 + 3.0, 5.8), xytext=(yd0 + 0.3, 8.2), fontsize=8, color="#1e6b3a", fontweight="bold", arrowprops=dict(arrowstyle="-", lw=0.6, color="#1e6b3a"), zorder=9)
axd.text(yd0 + 0.3, -1.9, "back plate", fontsize=7.8, color="white", zorder=9, fontweight="bold")
axd.text(yd1 - 0.3, 3.0, "dinding shell", fontsize=7.6, rotation=90, va="center", ha="right", color="#5b3508", zorder=9)
fig.text(X6 + 0.003, Y6 + 0.075 + H - 0.075 - 0.02 + 0.004, "detail dinding Atas (diperbesar)", fontsize=8.2, style="italic", va="bottom")
if P.get("strip"):
    # potongan kedua di x = 0: batang strip melintas di atas rim plate (celah 0.4 mm), tanpa sekrup
    axg = fig.add_axes([X6 + 0.158, Y6 + 0.075, 0.150, H - 0.075 - 0.02]); axg.set_facecolor("white")
    section_axes(axg, (yd0, yd1), (zd0, zd1), True, SEC0)
    rim_top = S["z"]["split"] + 2.0
    bar_z0 = [pc for pc in P["pieces"] if pc["nama"] == "strip"][0]["zbar"][0]
    axg.annotate(f"celah {bar_z0 - rim_top:.1f} mm", xy=(yt - 0.8, 0.5 * (rim_top + bar_z0)), xytext=(yd0 + 0.3, 0.6), fontsize=7.6, arrowprops=dict(arrowstyle="-", lw=0.6, color="k"), zorder=9, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
    axg.annotate("batang strip", xy=(yt - 3.0, 3.2), xytext=(yd0 + 0.3, 6.4), fontsize=8, color="#b00060", fontweight="bold", arrowprops=dict(arrowstyle="-", lw=0.7, color="#b00060"), zorder=9)
    axg.annotate("rim plate", xy=(yt - 1.4, -0.2), xytext=(yd0 + 0.3, -1.4), fontsize=7.8, color="#222222", fontweight="bold", arrowprops=dict(arrowstyle="-", lw=0.6, color="#222222"), zorder=9, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
    fig.text(X6 + 0.158, Y6 + 0.075 + H - 0.075 - 0.02 + 0.004, f"potongan di x = 0 (di atas rim plate)", fontsize=8.2, style="italic", va="bottom")
else:
    axf = fig.add_axes([X6 + 0.215, Y6 + 0.075, 0.085, H - 0.075 - 0.02])
    section_axes(axf, (S["outer_y"][0] - 2, S["outer_y"][1] + 2), (-4.5, 35), False)
    axf.add_patch(Rectangle((yd0, zd0), yd1 - yd0, zd1 - zd0, fc="none", ec="#1f4e9c", lw=1.0, ls="--", zorder=9))
    axf.text(S["outer_y"][1] + 1.0, 13, "ATAS", fontsize=7, rotation=90, color="#1f4e9c", va="center")
    axf.text(S["outer_y"][0] - 1.0, 13, "BAWAH", fontsize=7, rotation=90, color="#1f4e9c", va="center", ha="right")
    fig.text(X6 + 0.215, Y6 + 0.075 + H - 0.075 - 0.02 + 0.004, "penampang penuh", fontsize=8.2, style="italic", va="bottom")
fig.text(X6 + 0.002, Y6 + 0.040, "\n".join(textwrap.wrap("Penahan (magenta) berada di antara dinding dan lantai plate, tepat di bawah PCB. Sekrup masuk dari belakang menembus plate dan menggigit penahan. "
         "Catatan: sesudah dilem, tumpukan tidak bisa ditarik keluar dari belakang tanpa memotong penahan.", 70)), fontsize=8.6, va="top", color="#222222")

# legenda warna
leg = [("#e8a04a", "shell"), ("#454750", "back plate"), ("#ea1a8c", "penahan"), ("#f4e842", "epoxy"), ("#b9bac2", "sekrup"), ("#2e9a55", "PCB"), ("#c02020", "TFT")]
for i, (c, n) in enumerate(leg):
    fig.patches.append(Rectangle((0.030 + i * 0.075, 0.032), 0.010, 0.014, transform=fig.transFigure, fc=c, ec="k", lw=0.4))
    fig.text(0.044 + i * 0.075, 0.039, n, fontsize=9, va="center")
fig.text(0.975, 0.039, f"Gambar ilustrasi (baterai tidak digambar); dimensi dari model CAD case/{os.path.basename(os.path.normpath(D))}", fontsize=8, ha="right", va="center", color="#555555")
fig.savefig(OUTF, dpi=200)
fig.savefig(os.path.splitext(OUTF)[0] + ".pdf")
print("OK", OUTF)
