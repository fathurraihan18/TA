"""Ilustrasi gaya jurnal: penempatan 3 elektroda EKG (RA, LA, RL), sensor PPG jepit jari, dan perangkat di sabuk.
Vektor (PDF/SVG) + PNG/TIFF 600 dpi. Ukuran kolom IEEE: 1 kolom 3,5 in, 2 kolom 7,16 in. Font Liberation Sans (setara Arial), teks akhir >= 6,5 pt.

python gambar_jurnal_elektroda.py <folder_keluaran>
Keluaran: Fig_Elektroda_2kolom.(pdf|svg|png|tif), Fig_Elektroda_1kolom.(pdf|svg|png|tif), Caption_Fig_Elektroda.txt
Konvensi: tampak anterior (pasien menghadap pembaca): sisi KANAN pasien di KIRI gambar.
"""
import sys, os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, Polygon, Rectangle, FancyArrowPatch, PathPatch
from matplotlib.path import Path

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({
    "font.family": "Liberation Sans", "font.size": 7.5, "axes.linewidth": 0.5,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
    "lines.linewidth": 0.6, "savefig.dpi": 600,
})
COL = {"RA": "#C62828", "LA": "#F2B705", "RL": "#2E7D32"}          # merah / kuning / hijau (spidol pada kabel pengguna: RA, LA, RL)
TXT = {"RA": "white", "LA": "black", "RL": "white"}
INK = "#222222"; GRY = "#8a8a8a"; LG = "#e9e9e9"; MG = "#bdbdbd"


def catmull(pts, closed=False, n=14):
    P = np.array(pts, float)
    if closed: P = np.vstack([P[-1], P, P[0], P[1]])
    else: P = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed: out.append(P[-2])
    return np.array(out)


# ---------------------------------------------------------------- siluet tubuh (satuan ~ 6,4 mm; lebar bahu ~ 36 cm)
half = [(-6, 139), (-13, 133.5), (-24, 130), (-35, 125), (-42, 117), (-45.5, 104), (-47, 88), (-47.5, 72), (-47.5, 56),
        (-39.5, 56), (-38.5, 72), (-36.5, 90), (-33.5, 104), (-31, 109), (-29.5, 96), (-28.5, 80), (-26.5, 66), (-25, 56), (-27, 44), (-29, 30)]


def body_outline():
    L = catmull(half, False, 10)
    R = L[::-1].copy(); R[:, 0] *= -1
    return np.vstack([L, np.array([(-29, 30), (29, 30)]), R])                 # bagian bawah dipotong lurus (pinggul)


def draw_torso(ax, with_clip=True):
    bo = body_outline()
    ax.add_patch(Polygon(bo, closed=True, fc=LG, ec=INK, lw=0.7, zorder=1, joinstyle="round"))
    # kepala + leher
    ax.add_patch(Ellipse((0, 151), 23, 28, fc=LG, ec=INK, lw=0.7, zorder=2))
    ax.add_patch(Polygon([(-5.8, 138.5), (5.8, 138.5), (5.2, 143), (-5.2, 143)], fc=LG, ec="none", zorder=3))
    ax.plot([-5.8, -5.2], [138.5, 143], color=INK, lw=0.7, zorder=3); ax.plot([5.8, 5.2], [138.5, 143], color=INK, lw=0.7, zorder=3)
    # penanda anatomi tipis: klavikula, sternum, puting, tepi iga, pusar
    for s in (-1, 1):
        cl = catmull([(s * 3, 128), (s * 11, 126.5), (s * 21, 125.5), (s * 31, 123.5)], False, 12)
        ax.plot(cl[:, 0], cl[:, 1], color=GRY, lw=0.5, zorder=2)
        ax.add_patch(Circle((s * 14, 99), 1.1, fc="none", ec=GRY, lw=0.5, zorder=2))
        rb = catmull([(s * 2, 84), (s * 12, 82), (s * 21, 86), (s * 27, 96)], False, 12)
        ax.plot(rb[:, 0], rb[:, 1], color=GRY, lw=0.5, zorder=2)
    ax.plot([0, 0], [128, 86], color=GRY, lw=0.5, zorder=2)
    ax.add_patch(Circle((0, 64), 0.8, fc=GRY, ec="none", zorder=2))
    # sabuk
    ax.add_patch(Rectangle((-28.6, 40.5), 57.2, 5.0, fc="#666666", ec=INK, lw=0.5, zorder=4))
    ax.add_patch(Rectangle((-1.2, 40.2), 2.4, 5.6, fc="#b9b9b9", ec=INK, lw=0.4, zorder=5))


def electrode_pad(ax, xy, label, r=3.6, z=8):
    ax.add_patch(Circle(xy, r, fc="white", ec=INK, lw=0.6, zorder=z))
    ax.add_patch(Circle((xy[0] - 0.3, xy[1] - 0.3), r * 0.68, fc="#cfe8f7", ec="none", zorder=z + 0.1))
    ax.add_patch(Circle(xy, 1.05, fc="#9a9a9a", ec=INK, lw=0.4, zorder=z + 0.3))


def connector(ax, xy, label, ang_deg, z=9):
    c = COL[label]; a = math.radians(ang_deg); ex, ey = math.cos(a), math.sin(a); nx, ny = -ey, ex
    cx, cy = xy
    # tetesan: lingkaran r=2.2 dan ekor sempit
    th = np.linspace(0, 2 * math.pi, 40)
    pts = [(cx + 2.2 * math.cos(t), cy + 2.2 * math.sin(t)) for t in th]
    tail = [(cx + ex * 5.2 + nx * 1.1, cy + ey * 5.2 + ny * 1.1), (cx + ex * 5.2 - nx * 1.1, cy + ey * 5.2 - ny * 1.1)]
    from scipy.spatial import ConvexHull
    P = np.array(pts + tail); h = ConvexHull(P)
    ax.add_patch(Polygon(P[h.vertices], fc=c, ec=INK, lw=0.5, zorder=z))
    return (cx + ex * 6.0, cy + ey * 6.0)


def lead(ax, pts, z=6, lw=0.8, col="#555555"):
    C = catmull(pts, False, 16)
    ax.plot(C[:, 0], C[:, 1], color=col, lw=lw, zorder=z, solid_capstyle="round")


def panel_a(ax, compact=False):
    draw_torso(ax)
    pos = {"RA": (-17.5, 117.5), "LA": (17.5, 117.5), "RL": (-15.5, 52.0)}
    ang = {"RA": 205, "LA": -25, "RL": 205}
    # perangkat di sabuk (sisi kiri pasien dari pembaca: kanan gambar), kabel elektroda ke jack di sisi ATAS perangkat
    dev = Rectangle((6, 34.5), 17, 10.2, fc="white", ec=INK, lw=0.7, zorder=7)
    ax.add_patch(dev)
    ax.add_patch(Rectangle((7.6, 36.0), 9.8, 7.2, fc="#0f1b2d", ec=INK, lw=0.4, zorder=8))
    xs = np.linspace(8.0, 17.0, 40); ax.plot(xs, 39.6 + 1.6 * np.sin((xs - 8) * 1.2) * np.exp(-((xs - 12.5) / 3.5) ** 2) * 1.0, color="#4cd964", lw=0.5, zorder=9)
    ax.add_patch(Rectangle((18.2, 34.5 + 3.3), 4.4, 3.6, fc="#d4d4d4", ec=INK, lw=0.3, zorder=8))   # tanda saklar kecil
    jack = (14.0, 45.2)
    # kawat elektroda -> titik sambung -> kabel tunggal -> jack
    ends = {}
    for lb in ("RA", "LA", "RL"):
        ends[lb] = connector(ax, pos[lb], lb, ang[lb])
    J = (1.0, 76.0)
    lead(ax, [ends["RA"], (-8.0, 112.0), (-3.0, 90.0), J], z=6)
    lead(ax, [ends["LA"], (10.0, 111.0), (5.0, 92.0), J], z=6)
    lead(ax, [ends["RL"], (-14.0, 60.0), (-9.0, 70.0), J], z=6)
    ax.add_patch(Circle(J, 0.9, fc="#444444", ec=INK, lw=0.3, zorder=7))
    lead(ax, [J, (3.5, 66.0), (9.0, 55.0), (13.8, 49.0), jack], z=6, lw=1.3)
    # tangan: telapak (elips) di ujung lengan; tangan kiri pasien (kanan gambar) menjepit klip PPG di jari telunjuk
    ax.add_patch(Ellipse((-43.0, 49.5), 9.5, 14.0, fc=LG, ec=INK, lw=0.6, zorder=3))
    ax.add_patch(Ellipse((43.0, 49.5), 9.5, 14.0, fc=LG, ec=INK, lw=0.6, zorder=3))
    ax.add_patch(Polygon([(41.2, 44.0), (44.8, 44.0), (44.8, 31.0), (41.2, 31.0)], closed=True, fc=LG, ec=INK, lw=0.6, zorder=3, joinstyle="round"))   # jari telunjuk
    ax.add_patch(Rectangle((40.2, 29.2), 5.6, 9.0, fc="white", ec=INK, lw=0.7, zorder=8, joinstyle="round"))                                         # klip
    ax.add_patch(Rectangle((40.2, 29.2), 5.6, 3.0, fc="#bdbdbd", ec=INK, lw=0.5, zorder=9))
    lead(ax, [(42.8, 38.2), (40.0, 42.0), (33.0, 40.5), (23.2, 38.8)], z=6, lw=1.0, col="#333333")
    ax.text(0, 170.5, "Anterior view", ha="center", va="center", fontsize=7, color=INK, fontweight="bold")
    ax.text(-52, 158, "Patient's\nright", ha="center", va="center", fontsize=7, color=INK, style="italic")
    ax.text(52, 158, "Patient's\nleft", ha="center", va="center", fontsize=7, color=INK, style="italic")
    return pos, ang, ends, J, jack


def label_pointer(ax, xy, text, tx, ty, ha, color=INK, lw=0.5):
    ax.annotate(text, xy=xy, xytext=(tx, ty), fontsize=7, ha=ha, va="center", color=color,
                arrowprops=dict(arrowstyle="-", lw=lw, color=color, shrinkA=1, shrinkB=1), zorder=20)


import json as _json
import matplotlib.patheffects as pe
from PIL import Image as _Image

HUM_PNG = os.environ.get("HUM_PNG", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "FINAL_TA", "_render", "manusia", "manusia_full.png"))


def load_human():
    """render 3D torso (RGBA) + koordinat proyeksi; sisi atas (leher) dan bawah (paha) dipudarkan ke putih agar tidak terpotong kasar."""
    im = _Image.open(HUM_PNG).convert("RGBA")
    info = _json.load(open(HUM_PNG + ".json"))
    W, H = im.size
    zl = info["z_levels"]
    arr = np.asarray(im).astype(np.float32)
    rows = np.arange(H, dtype=np.float32)
    def ramp(y0, y1):                    # 0 pada y0, 1 pada y1 (halus)
        t = np.clip((rows - y0) / (y1 - y0), 0, 1); return t * t * (3 - 2 * t)
    top = ramp(zl["520"] - 0.0, zl["480"]) if "520" in zl else np.ones(H)
    bot = 1 - ramp(zl["-400"], zl["-450"]) if "-450" in zl else np.ones(H)
    arr[..., 3] *= (top * bot)[:, None]
    return arr.astype(np.uint8), info


def panel_a_3d(ax):
    arr, info = load_human()
    H, W = arr.shape[:2]
    ax.imshow(arr, extent=(0, W, H, 0), zorder=1, interpolation="lanczos")
    ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.set_aspect("equal"); ax.axis("off")
    halo = [pe.withStroke(linewidth=2.2, foreground="white")]
    def tag(lb, dx, dy, col, txtcol):
        x, y = info[lb]
        ax.text(x + dx * W, y + dy * H, lb, fontsize=7.5, fontweight="bold", color=txtcol, ha="center", va="center", path_effects=halo, zorder=20)
    tag("RA", -0.002, -0.050, COL["RA"], COL["RA"]); tag("LA", 0.002, -0.050, "#9a7400", "#9a7400"); tag("RL", -0.002, -0.050, COL["RL"], COL["RL"])
    def callout(key, tx, ty, text, ha="center", color=INK):
        x, y = info[key]
        ax.annotate(text, xy=(x, y), xytext=(tx * W, ty * H), fontsize=7, ha=ha, va="center", color=color,
                    arrowprops=dict(arrowstyle="-", lw=0.5, color=color, shrinkA=1, shrinkB=2), zorder=20,
                    bbox=dict(fc="white", ec="none", pad=1.2, alpha=0.9))
    callout("device", 0.66, 0.69, "Wearable device\n(ESP32 + AD8232 + TFT)")
    callout("clip", 0.40, 0.915, "Finger-clip PPG sensor\n(MAX30102)")
    ax.text(0.04 * W, 0.075 * H, "Patient's\nright", fontsize=7, style="italic", ha="left", va="center", color=INK, zorder=20)
    ax.text(0.96 * W, 0.075 * H, "Patient's\nleft", fontsize=7, style="italic", ha="right", va="center", color=INK, zorder=20)
    ax.text(0.5 * W, 0.03 * H, "Anterior view", fontsize=7, fontweight="bold", ha="center", va="center", color=INK, zorder=20)
    return info


def figure_2col():
    arr, info = load_human(); H, W = arr.shape[:2]
    fh = 4.75
    fig = plt.figure(figsize=(7.16, fh))
    wa = fh * W / H / 7.16                                           # lebar panel (a) sebagai pecahan lebar gambar
    axa = fig.add_axes([0.0, 0.0, wa, 1.0])
    panel_a_3d(axa)
    axa.text(0.0, 0.0, "(a)", fontsize=9, fontweight="bold", va="top", ha="left", transform=axa.transAxes, zorder=30) if False else fig.text(0.002, 0.995, "(a)", fontsize=9, fontweight="bold", va="top")
    x0 = wa + 0.02
    wr = 1.0 - x0 - 0.01
    axb = fig.add_axes([x0 + 0.05 * wr, 0.665, 0.62 * wr, 0.31]); axb.set_aspect("equal"); axb.axis("off")
    axb.set_xlim(-34, 52); axb.set_ylim(-31, 30)
    detail_top(axb, "RA", ox=0.0, oy=0.0)
    axb2 = fig.add_axes([x0, 0.44, wr, 0.20]); axb2.set_aspect("equal"); axb2.axis("off")
    axb2.set_xlim(-30, 52); axb2.set_ylim(-23, 11)
    detail_side(axb2, "RA", ox=0.0, oy=0.0)
    fig.text(x0, 0.975, "(b)", fontsize=9, fontweight="bold", va="top")
    axc = fig.add_axes([x0, 0.03, wr, 0.33]); axc.axis("off"); axc.set_xlim(0, 1); axc.set_ylim(0, 1)
    table(axc)
    fig.text(x0, 0.405, "(c)", fontsize=9, fontweight="bold", va="top")
    return fig


def figure_1col():
    arr, info = load_human(); H, W = arr.shape[:2]
    fig = plt.figure(figsize=(3.5, 3.5 * H / W))
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    panel_a_3d(ax)
    return fig


def detail_top(ax, lb, ox, oy):
    """tampak atas elektroda (mm), seperti model 3D: pad Ø45, gel biru, snap, konektor berwarna."""
    ax.add_patch(Circle((ox, oy), 22.5, fc="white", ec=INK, lw=0.6))
    ax.add_patch(Circle((ox - 1.5, oy - 2.0), 17.0, fc="#bfe3f7", ec="none"))
    ax.add_patch(Circle((ox + 9.5, oy + 6.5), 9.5, fc="#bfe3f7", ec="none"))
    sx, sy = ox + 9.5, oy + 6.5
    a = math.radians(35); ex, ey = math.cos(a), math.sin(a)
    from scipy.spatial import ConvexHull
    th = np.linspace(0, 2 * math.pi, 50)
    P = np.array([(sx + 6.1 * math.cos(t), sy + 6.1 * math.sin(t)) for t in th] + [(sx + ex * 12 + 3.1 * math.cos(t), sy + ey * 12 + 3.1 * math.sin(t)) for t in th])
    h = ConvexHull(P)
    ax.add_patch(Polygon(P[h.vertices], fc=COL[lb], ec=INK, lw=0.6, zorder=5))
    ax.text(sx + ex * 1.2, sy + ey * 1.2, lb, rotation=35, ha="center", va="center", fontsize=6.5, color=TXT[lb], fontweight="bold", zorder=6)
    ax.annotate("", xy=(ox - 22.5, oy - 26), xytext=(ox + 22.5, oy - 26), arrowprops=dict(arrowstyle="<->", lw=0.5, color=INK))
    ax.text(ox, oy - 27.4, "Ø45 mm", ha="center", va="top", fontsize=6.5)
    ax.annotate("hydrogel", xy=(ox - 12, oy - 9), xytext=(ox - 36, oy + 14), fontsize=6.5, color="#2c6f95", ha="center", arrowprops=dict(arrowstyle="-", lw=0.4, color="#2c6f95"))
    ax.text(ox, oy + 26.5, "top view", fontsize=6.5, ha="center", color="#555555", style="italic")


def detail_side(ax, lb, ox, oy):
    """tampak samping (skala mm, sama dengan model 3D): busa 1,2; gel 0,25; flens + stud snap; konektor tinggi 6,4 dengan relief tarik 5 rusuk."""
    x0 = ox - 22.5; y0 = oy - 6.0                                      # y0 = sisi kulit
    ax.add_patch(Rectangle((x0, y0), 45, 1.2, fc="white", ec=INK, lw=0.5))                                  # pad busa
    ax.add_patch(Rectangle((x0 + 5.5, y0 + 1.2), 34, 0.25, fc="#9fd3f0", ec="none"))                      # gel
    sx = ox + 9.5 * 0.0 + 4.0
    ax.add_patch(Rectangle((sx - 4.9, y0 + 1.45), 9.8, 0.7, fc="#c8c8cc", ec=INK, lw=0.4, zorder=3))       # flens snap
    ax.add_patch(Rectangle((sx - 1.9, y0 + 2.15), 3.8, 1.5, fc="#c8c8cc", ec=INK, lw=0.4, zorder=3))       # leher
    ax.add_patch(Ellipse((sx, y0 + 3.65 + 0.9), 5.2, 4.8, fc="#c8c8cc", ec=INK, lw=0.4, zorder=3))         # kepala
    zb, zt = y0 + 2.35, y0 + 8.75                                                                           # dasar dan puncak konektor
    ax.add_patch(Polygon([(sx - 6.1, zb), (sx + 12, zb), (sx + 12, zt), (sx - 6.1, zt)], fc=COL[lb], ec=INK, lw=0.5, zorder=4))
    for i in range(5):
        xr = sx + 12 + i * 1.7
        ax.add_patch(Rectangle((xr, zb + 1.6 + 0.07 * i), 1.0, 3.2 - 0.14 * i, fc=COL[lb], ec=INK, lw=0.4, zorder=4))
    ax.plot([sx + 12 + 5 * 1.7, sx + 12 + 5 * 1.7 + 9.0], [zb + 3.2, zb + 3.2], color="#555555", lw=1.0)
    ax.annotate("", xy=(x0 - 3.0, y0), xytext=(x0 - 3.0, zt), arrowprops=dict(arrowstyle="<->", lw=0.5, color=INK))
    ax.text(x0 - 4.2, (y0 + zt) / 2, "8.8", rotation=90, ha="right", va="center", fontsize=6.5)
    ax.annotate("foam pad 1.2 mm", xy=(x0 + 12, y0 + 0.6), xytext=(x0 + 4, y0 - 6.5), fontsize=6.5, ha="left", arrowprops=dict(arrowstyle="-", lw=0.4, color=INK))
    ax.annotate("snap stud", xy=(sx + 0.5, y0 + 4.2), xytext=(sx - 12, y0 + 15), fontsize=6.5, ha="center", arrowprops=dict(arrowstyle="-", lw=0.4, color=INK))
    ax.annotate("lead connector", xy=(sx + 7, zt), xytext=(sx + 15, y0 + 15), fontsize=6.5, ha="center", arrowprops=dict(arrowstyle="-", lw=0.4, color=INK))
    ax.text(ox + 8, y0 - 14.0, "side view (dimensions in mm)", fontsize=6.5, ha="center", color="#555555", style="italic")


def table(ax):
    rows = [("RA", "Red", "Right arm", "right infraclavicular fossa"),
            ("LA", "Yellow", "Left arm", "left infraclavicular fossa"),
            ("RL", "Green", "Right leg (reference)", "right lower abdomen / iliac crest")]
    ax.text(0.0, 0.97, "Lead", fontsize=7, fontweight="bold", va="center")
    ax.text(0.15, 0.97, "Colour", fontsize=7, fontweight="bold", va="center")
    ax.text(0.34, 0.97, "Function / position", fontsize=7, fontweight="bold", va="center")
    ax.plot([0, 1], [0.90, 0.90], color=INK, lw=0.5)
    y = 0.76
    for lb, cn, fn, loc in rows:
        ax.add_patch(Ellipse((0.045, y), 0.085, 0.115, fc=COL[lb], ec=INK, lw=0.4, clip_on=False))
        ax.text(0.045, y, lb, fontsize=6, ha="center", va="center", color=TXT[lb], fontweight="bold")
        ax.text(0.15, y, cn, fontsize=7, va="center")
        ax.text(0.34, y + 0.05, fn, fontsize=7, va="center")
        ax.text(0.34, y - 0.05, loc, fontsize=6.4, va="center", color="#444444")
        y -= 0.20
    ax.plot([0, 1], [0.16, 0.16], color=INK, lw=0.5)
    ax.text(0.0, 0.07, "Three-lead cable (grey wires) with a 3.5 mm plug into the AD8232 jack.", fontsize=6.4, va="center", color="#444444")


CAP = """Fig. X. Placement of the three ECG electrodes and the finger-clip PPG sensor. (a) Anterior view (patient's right on the reader's left): RA (red) below the right clavicle, LA (yellow) below the left clavicle, and RL (green, reference) on the right lower abdomen; the three leads join one cable that plugs into the AD8232 jack of the wearable device worn on the belt, and the MAX30102 finger clip is worn on the right index finger. (b) Top and side views of a disposable snap electrode (Ø45 mm foam pad, hydrogel, snap stud) with the colour-coded lead connector. (c) Lead labels, colours and positions.
"""
CAP_ID = """Gambar X. Penempatan tiga elektroda EKG dan sensor PPG jepit jari. (a) Tampak anterior (sisi kanan pasien berada di kiri pembaca): RA (merah) di bawah klavikula kanan, LA (kuning) di bawah klavikula kiri, dan RL (hijau, referensi) di perut kanan bawah; ketiga kabel menyatu menjadi satu kabel yang ditancapkan ke jack AD8232 pada perangkat di sabuk, sedangkan klip MAX30102 dipasang pada jari telunjuk kanan. (b) Tampak atas dan samping elektroda sekali pakai berpengait snap (pad busa Ø45 mm, hidrogel, kancing snap) dengan konektor berkode warna. (c) Label, warna, dan posisi kabel.
"""

for name, fn in (("Fig_Elektroda_2kolom", figure_2col), ("Fig_Elektroda_1kolom", figure_1col)):
    fig = fn()
    base = os.path.join(OUT, name)
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".svg")
    fig.savefig(base + ".png", dpi=600)
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(base + ".png").convert("RGB"); im.save(base + ".tif", compression="tiff_lzw", dpi=(600, 600))
    except Exception as e:
        print("tif gagal", e)
    plt.close(fig)
    print("saved", name)
open(os.path.join(OUT, "Caption_Fig_Elektroda.txt"), "w").write("EN:\n" + CAP + "\nID:\n" + CAP_ID)
