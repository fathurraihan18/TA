"""Susun lembar A3: (1) gambar eksplode bernomor + tabel komponen, (2) penempatan komponen & baterai.
Jalankan: python susun_perakitan.py <folder_case> <folder_render> <folder_output>
"""
import sys, os, json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image

CASE, REN, OUTD = sys.argv[1:4]
os.makedirs(OUTD, exist_ok=True)
S = json.load(open(os.path.join(CASE, "_ref", "summary.json")))
IT = json.load(open(os.path.join(REN, "items.json")))
ITEMS, BAT = IT["ITEMS"], IT["BAT"]
V3 = bool(S.get("battery"))                                      # v3 = ruang baterai di sisi Bawah, tidak menumpuk
YB_OUT, YT_OUT = S.get("outer_y", [-S["outer"][1] / 2, S["outer"][1] / 2])
CAV_YB, CAV_YT = S.get("cavity_y", [-S["cavity"][1] / 2, S["cavity"][1] / 2])
FS = 6.3


def rj(n): return json.load(open(os.path.join(REN, n)))


# ------------------------------------------------------------------ daftar komponen (penjelasan jelas)
BOM = [
    (1, "Shell depan (cover)", 1, "PETG cetak 3D. 105,0 x 63,5 x 34,4 mm, dinding 3 mm. Jendela layar 79 x 52 mm; lubang micro-USB (Bawah), jack elektroda + saklar (Atas), USB-C + gland (Kanan)."),
    (2, "Layar TFT 3,5\" ILI9488 + touch", 1, "480 x 320 piksel, antarmuka SPI. Modul 98,0 x 56,34 mm; area aktif 73,44 x 48,96 mm; kaca touch 85 x 55 x 3 mm. Menghadap jendela shell."),
    (3, "Standoff M3 20 mm + baut", 4, "Menahan TFT 20 mm di atas PCB. Ekor ulir 5 mm + mur di belakang PCB; kepala baut 3 mm di sisi depan TFT."),
    (4, "PCB utama (custom, Gerber)", 1, "98,03 x 56,16 mm, 4 lubang M3. Soket ESP32, header AD8232, konektor baterai (JST 2-pin), PPG (4-pin), saklar (JST)."),
    (5, "ESP32 DevKit C V4", 1, "Mikrokontroler: akuisisi sinyal dan inferensi LightGBM. Dipasang di soket; port micro-USB menghadap sisi Bawah."),
    (6, "Modul AD8232 (SparkFun)", 1, "Akuisisi ECG 1-lead, 35,56 x 27,94 mm. Jack 3,5 mm menghadap sisi Atas (pusat 61,3 mm dari tepi Kiri PCB)."),
    (7, "Kabel elektroda + plug 3,5 mm", 1, "Kabel 3 lead (RA, LA, RL) menuju elektroda. Keluar lewat lubang bulat 7,2 mm di sisi Atas."),
    (8, "Modul powerbank TYPE-C 5V boost", 1, "Pengisian baterai dan keluaran 5 V. Port USB-C menghadap sisi Kanan (pusat 18,1 mm dari tepi Atas PCB)."),
    (9, "Baterai Li-ion PALO 103450", 1, "3,7 V 2000 mAh, 10 x 34 x 50 mm. Rebah di atas PCB, rapat sisi Bawah; kabel merah/hitam ke konektor JST 2-pin di PCB."),
    (10, "Sensor PPG MAX30102 + kabel", 1, "Konektor 4-pin di PCB (sisi Kanan). Kabel keluar lewat gland PG7 menuju modul sensor jari di luar casing."),
    (11, "Saklar rocker KCD11 mini", 1, "ON/OFF daya, 10 x 15 mm snap-in. Dipasang datar di dinding sisi Atas (lubang 14 x 9 mm)."),
    (12, "Cable gland PG7 + mur", 1, "Jalur kabel PPG 3 - 6,5 mm, ulir 12,5 mm. Mur masuk kantong segi-enam di dinding sisi Kanan."),
    (13, "Back plate + sayap sabuk", 1, "PETG. 133 x 63,5 mm; 4 tiang penyangga PCB; 2 slot sabuk 6 x 44 mm untuk pinggang atau bahu."),
    (14, "Sekrup M3 x 8 flat head", 4, "Mengikat back plate ke boss di dinding Atas/Bawah (mengulir sendiri, tertanam 4,8 mm)."),
]
if V3:
    def _bom_set(n, desc):
        i = [k for k, r in enumerate(BOM) if r[0] == n][0]
        BOM[i] = (BOM[i][0], BOM[i][1], BOM[i][2], desc)
    def _fm(v):
        t = f"{v:.2f}".replace(".", ",")
        return t[:-1] if t.endswith("0") else t
    _ov = f"{S['pcb']['y0'] - S['battery']['y0']:.1f}".replace(".", ",")
    _bom_set(1, f"PETG cetak 3D. {_fm(S['outer'][0])} x {_fm(S['outer'][1])} x 34,4 mm, dinding 3 mm; sisi Bawah diperlebar {_fm(S['bay'])} mm untuk baterai. Jendela layar 79 x 52 mm; lubang micro-USB (Bawah), jack + saklar (Atas), USB-C + gland (Kanan).")
    _bom_set(9, f"3,7 V 2000 mAh, 10 x 34 x 50 mm. Rebah di atas PCB sisi Bawah, TIDAK menumpuk modul (celah 0,6 mm); menjorok {_ov} mm di luar tepi PCB, ditopang 3 rusuk back plate. Kabel merah/hitam ke JST 2-pin.")
    _bom_set(13, f"PETG. {_fm(S['plate'][0])} x {_fm(S['plate'][1])} mm; 4 tiang penyangga PCB; 3 rusuk + 2 stopper penyangga baterai; 2 slot sabuk 6 x 44 mm untuk pinggang atau bahu.")
NAME = {n: nm for n, nm, q, d in BOM}


# ------------------------------------------------------------------ util gambar
def crop_alpha(path, margin=14):
    im = Image.open(path).convert("RGBA")
    arr = np.asarray(im)
    a = arr[..., 3]
    if a.min() > 250:                       # latar putih tidak transparan -> deteksi piksel non-putih
        a = (arr[..., :3].min(-1) < 236).astype(np.uint8) * 255
    ys, xs = np.where(a > 8)
    box = (max(xs.min() - margin, 0), max(ys.min() - margin, 0), min(xs.max() + margin, im.width), min(ys.max() + margin, im.height))
    return im.crop(box), box, im.size


class Panel:
    """menempatkan citra pada kotak (x,y,w,h mm) dan memetakan koordinat piksel asli -> kertas."""
    def __init__(self, ax, path, region, crop=True, margin=14):
        self.ax = ax
        if crop:
            self.im, self.box, self.size = crop_alpha(path, margin)
        else:
            im = Image.open(path).convert("RGBA"); self.im, self.box, self.size = im, (0, 0, im.width, im.height), im.size
        rx, ry, rw, rh = region
        w, h = self.im.size
        self.s = min(rw / w, rh / h)
        self.w_mm, self.h_mm = w * self.s, h * self.s
        self.x0 = rx + (rw - self.w_mm) / 2
        self.y0 = ry + (rh - self.h_mm) / 2
        ax.imshow(np.asarray(self.im), extent=(self.x0, self.x0 + self.w_mm, self.y0, self.y0 + self.h_mm), origin="upper",
                  interpolation="lanczos", zorder=2)
        self.region = region

    def pt(self, px, py):
        return (self.x0 + (px - self.box[0]) * self.s, self.y0 + (self.h_mm - (py - self.box[1]) * self.s))

    def pt_norm(self, nx, ny):
        W, H = self.size
        return self.pt(nx * W, (1 - ny) * H)


def balloons(ax, panel, anchors, which, rad=3.6, dist=16, avoid_center=None, font=8.5, bounds=None, manual=None):
    rx, ry, rw, rh = panel.region
    bx0, by0, bx1, by1 = bounds or (rx + rad + 1, ry + rad + 1, rx + rw - rad - 1, ry + rh - rad - 1)
    pts = {}
    for k in which:
        if k not in anchors: continue
        pts[k] = np.array(panel.pt_norm(*anchors[k]))
    c = np.mean(list(pts.values()), axis=0) if avoid_center is None else np.array(avoid_center)
    pos = {}
    for k, p in pts.items():
        v = p - c
        n = np.linalg.norm(v)
        v = v / n if n > 1e-6 else np.array([0, 1.0])
        pos[k] = p + v * dist
    for _ in range(300):
        moved = False
        ks = list(pos)
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                d = pos[ks[i]] - pos[ks[j]]
                L = np.linalg.norm(d)
                if L < 2 * rad + 3.5:
                    u = d / L if L > 1e-6 else np.array([1.0, 0])
                    pos[ks[i]] += u * 0.7; pos[ks[j]] -= u * 0.7; moved = True
        for k in ks:
            pos[k][0] = min(max(pos[k][0], bx0), bx1); pos[k][1] = min(max(pos[k][1], by0), by1)
        if not moved: break
    for k, (mx_, my_) in (manual or {}).items():
        if k in pts: pos[k] = pts[k] + np.array([mx_, my_], float)
    for k in pos:
        a, b = pts[k], pos[k]
        d = b - a; L = np.linalg.norm(d); u = d / L if L > 1e-6 else np.array([0, 1.0])
        ax.plot([a[0], (b - u * rad)[0]], [a[1], (b - u * rad)[1]], lw=0.5, color="k", zorder=6)
        ax.plot([a[0]], [a[1]], marker="o", ms=2.2, color="k", zorder=7)
        ax.add_patch(Circle(b, rad, fc="white", ec="k", lw=0.8, zorder=8))
        ax.text(b[0], b[1], str(ITEMS[k]), fontsize=font, ha="center", va="center", zorder=9, fontweight="bold")
    return pos


def new_sheet():
    fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 420); ax.set_ylim(0, 297); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((5, 5), 410, 287, fill=False, lw=1.0, ec="k"))
    return fig, ax


def bom_table(ax, x0, y_top, widths, rows, row_h=5.3, header=("ITEM", "NAMA KOMPONEN", "JML", "KETERANGAN (spesifikasi, fungsi, posisi)")):
    xs = np.cumsum([x0] + list(widths))
    h = row_h * (len(rows) + 1)
    ax.add_patch(Rectangle((x0, y_top - h), sum(widths), h, fill=False, lw=0.9, ec="k", zorder=5))
    ax.add_patch(Rectangle((x0, y_top - row_h), sum(widths), row_h, fc="#e6e6e6", ec="k", lw=0.6, zorder=4))
    for i in range(1, len(widths)):
        ax.plot([xs[i], xs[i]], [y_top, y_top - h], lw=0.5, color="k", zorder=5)
    for c, t in enumerate(header):
        ax.text(xs[c] + 1.2 if c in (1, 3) else (xs[c] + xs[c + 1]) / 2, y_top - row_h / 2, t, fontsize=6.4, fontweight="bold",
                ha="left" if c in (1, 3) else "center", va="center", zorder=7)
    for r, (no, nm, q, d) in enumerate(rows):
        yy = y_top - row_h * (r + 1)
        ax.plot([x0, x0 + sum(widths)], [yy, yy], lw=0.4, color="k", zorder=5)
        ym = yy - row_h / 2
        ax.text((xs[0] + xs[1]) / 2, ym, str(no), fontsize=6.4, ha="center", va="center", zorder=7)
        ax.text(xs[1] + 1.2, ym, nm, fontsize=6.4, ha="left", va="center", zorder=7)
        ax.text((xs[2] + xs[3]) / 2, ym, str(q), fontsize=6.4, ha="center", va="center", zorder=7)
        ax.text(xs[3] + 1.2, ym, d, fontsize=5.5, ha="left", va="center", zorder=7)


# =============================================================== HALAMAN 1
def page1():
    fig, ax = new_sheet()
    ax.text(210, 287.5, "Gambar 3.x  Desain 3D beserta komponennya (tampak eksplode) - alat ECG + PPG", fontsize=12, fontweight="bold", ha="center", va="center")
    pa = Panel(ax, os.path.join(REN, "render_eksplodeA.png"), (8, 108, 262, 172))
    anchA = rj("anchors_eksplodeA.json")
    balloons(ax, pa, anchA, ["shell", "tft", "standoff", "pcb", "saklar", "gland", "plate", "sekrup"], dist=15, font=8.5)
    ax.text(10, 276, "A. Perakitan utama", fontsize=8, fontweight="bold")
    # gambar B
    pb = Panel(ax, os.path.join(REN, "render_eksplodeB.png"), (272, 174, 140, 104))
    anchB = rj("anchors_eksplodeB.json")
    balloons(ax, pb, anchB, ["pcb", "esp32", "ad8232", "kabel_el", "boost", "baterai", "ppg"], dist=13, font=8.0,
             manual={"kabel_el": (11, 2), "ad8232": (15, -3), "ppg": (-14, 0)})
    ax.text(274, 276, "B. Komponen di atas PCB (diangkat)", fontsize=8, fontweight="bold")
    # inset rakitan jadi
    pf = Panel(ax, os.path.join(REN, "render_rakitan_depan.png"), (272, 104, 140, 66), crop=True, margin=20)
    ax.text(274, 170, "C. Rakitan jadi", fontsize=8, fontweight="bold")
    # tabel
    ax.text(10, 101.5, "DAFTAR KOMPONEN", fontsize=8, fontweight="bold")
    bom_table(ax, 8, 99, [11, 58, 9, 326], BOM)
    ax.text(8, 12.5, "Warna: jingga/hitam = casing PETG; hijau = PCB utama; merah = TFT/AD8232; biru = powerbank/PPG; kuning = baterai. Angka pada balon = nomor item.",
            fontsize=5.8, va="center")
    return fig


# =============================================================== HALAMAN 2
def callout(ax, p, text, dx=0, dy=0, ha="left", fs=6.4, at=None):
    q = at if at is not None else (p[0] + dx, p[1] + dy)
    ax.plot([p[0], q[0]], [p[1], q[1]], lw=0.5, color="k", zorder=6)
    ax.plot([p[0]], [p[1]], marker="o", ms=2.0, color="k", zorder=7)
    ax.text(q[0] + (0.8 if ha == "left" else -0.8), q[1], text, fontsize=fs, ha=ha, va="center", zorder=8,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


def page2():
    fig, ax = new_sheet()
    ax.text(210, 287.5, "Penempatan komponen dan baterai - alat ECG + PPG", fontsize=12, fontweight="bold", ha="center", va="center")
    # ---- A. denah (tampak depan PCB, shell/TFT dilepas)
    rx, ry, rw, rh = 8, 142, 210, 128
    pd = Panel(ax, os.path.join(REN, "render_denah.png"), (rx, ry, rw, rh), crop=False)
    W, H = pd.size
    sc_px = W / 125.0

    YCM = (YB_OUT + YT_OUT) / 2                                        # kamera denah berpusat di tengah outline (v3: Y = -3,4)

    def M(X, Y): return pd.pt(W / 2 + X * sc_px, H / 2 - (Y - YCM) * sc_px)

    ax.text(rx + 1, 279, "A. DENAH PENEMPATAN (tampak depan PCB; layar TFT, shell, saklar dan gland dilepas)", fontsize=7.5, fontweight="bold", va="center")
    anc = rj("anchors_denah.json")
    balloons(ax, pd, anc, ["pcb", "esp32", "ad8232", "boost", "baterai", "ppg"], dist=11, font=8.0,
             bounds=(rx + 4, ry + 4, rx + rw - 4, ry + rh - 10), avoid_center=M(0, 0), manual=({"ppg": (-6.2, -3.6)} if V3 else None))
    for (X, Y, t, rot) in ((28, 34.6, "ATAS", 0), (0, -49.0 if V3 else -39.0, "BAWAH", 0), (-57.0, 14, "KANAN", 90), (57.0, 0, "KIRI", -90)):
        x_, y_ = M(X, Y)
        ax.text(x_, y_, t, fontsize=7.5, fontweight="bold", color="#1a4fa0", ha="center", va="center", rotation=rot, zorder=8)
    b = BAT
    P = lambda X, Y: M(X, Y)

    def dimh(X0, X1, Y, off, text):
        x0, y0 = P(X0, Y); x1, _ = P(X1, Y); yl = y0 + off
        for xx in (x0, x1): ax.plot([xx, xx], [y0, yl + (0.8 if off > 0 else -0.8)], lw=0.35, color="k", zorder=7)
        ax.annotate("", xy=(x1, yl), xytext=(x0, yl), arrowprops=dict(arrowstyle="<|-|>", lw=0.5, color="k", mutation_scale=5, shrinkA=0, shrinkB=0), zorder=8)
        ax.text((x0 + x1) / 2, yl - 0.8, text, fontsize=6.3, ha="center", va="top", zorder=9)

    def dimv(Y0, Y1, X, off, text):
        x0, y0 = P(X, Y0); _, y1 = P(X, Y1); xl = x0 + off
        for yy in (y0, y1): ax.plot([x0, xl + (0.8 if off > 0 else -0.8)], [yy, yy], lw=0.35, color="k", zorder=7)
        ax.annotate("", xy=(xl, y1), xytext=(xl, y0), arrowprops=dict(arrowstyle="<|-|>", lw=0.5, color="k", mutation_scale=5, shrinkA=0, shrinkB=0), zorder=8)
        ax.text(xl - 0.9, (y0 + y1) / 2, text, fontsize=6.3, rotation=90, ha="right", va="center", zorder=9)

    fm = lambda v: f"{v:.1f}".replace(".", ",")
    pcb = S["pcb"]
    if not V3:
        dimh(b["x0"], b["x1"], pcb["y0"], -4.6, fm(b["x1"] - b["x0"]))
        dimh(pcb["x0"], b["x0"], pcb["y0"], -9.6, fm(b["x0"] - pcb["x0"]))
        dimh(b["x1"], pcb["x1"], pcb["y0"], -9.6, fm(pcb["x1"] - b["x1"]))
        dimv(b["y0"], b["y1"], pcb["x0"], -4.6, fm(b["y1"] - b["y0"]))
        ya, yb = -0.5, b["y1"]
        xa, xb = max(b["x0"], -48.7), min(b["x1"], 12.7)
        x0p, y0p = P(xa, ya); x1p, y1p = P(xb, yb)
        ax.add_patch(Rectangle((x0p, y0p), x1p - x0p, y1p - y0p, fill=False, hatch="////", ec="#c00000", lw=0.8, zorder=8))
        lx, ly = P(-30, yb + 16)
        ax.text(lx, ly, f"tumpang tindih {fm(yb - ya)} mm: baterai di atas tepi\nBawah modul AD8232 dan powerbank", fontsize=6.4, color="#c00000", ha="center", va="center", zorder=9,
                bbox=dict(fc="white", ec="#c00000", lw=0.5, pad=1.2, alpha=0.92))
        ax.plot([lx, P(-30, ya + 3.0)[0]], [ly - 4.5, P(-30, ya + 3.0)[1]], lw=0.6, color="#c00000", zorder=8)
    else:
        def dimh3(X0, Y0, X1, Y1, yline, text):             # garis ukur horizontal; garis bantu dari (X0,Y0) dan (X1,Y1) turun ke yline
            xa_, ya_ = P(X0, Y0); xb_, yb_ = P(X1, Y1); yl = P(0, yline)[1]
            ax.plot([xa_, xa_], [ya_ - 0.8, yl - 0.8], lw=0.35, color="k", zorder=7)
            ax.plot([xb_, xb_], [yb_ - 0.8, yl - 0.8], lw=0.35, color="k", zorder=7)
            ax.annotate("", xy=(xb_, yl), xytext=(xa_, yl), arrowprops=dict(arrowstyle="<|-|>", lw=0.5, color="k", mutation_scale=5, shrinkA=0, shrinkB=0), zorder=8)
            ax.text((xa_ + xb_) / 2, yl - 0.8, text, fontsize=6.3, ha="center", va="top", zorder=9)
        y_dim1, y_dim2 = b["y0"] - 4.6, b["y0"] - 9.6
        dimh3(b["x0"], b["y0"], b["x1"], b["y0"], y_dim1, fm(b["x1"] - b["x0"]))
        dimh3(pcb["x0"], pcb["y0"], b["x0"], b["y0"], y_dim2, fm(b["x0"] - pcb["x0"]))
        dimh3(b["x1"], b["y0"], pcb["x1"], pcb["y0"], y_dim2, fm(pcb["x1"] - b["x1"]))
        dimv(b["y0"], b["y1"], pcb["x0"], -13.0, fm(b["y1"] - b["y0"]))
        dimv(b["y0"], pcb["y0"], b["x0"], -3.4, fm(pcb["y0"] - b["y0"]))
        # dinding dalam casing (garis putus) + rusuk/stopper back plate di bawah baterai (garis putus biru)
        xw0, yw0 = P(-S["cavity"][0] / 2, CAV_YB); xw1, yw1 = P(S["cavity"][0] / 2, CAV_YT)
        ax.add_patch(Rectangle((xw0, yw0), xw1 - xw0, yw1 - yw0, fill=False, lw=0.6, ec="#555555", ls=(0, (6, 2)), zorder=5))
        ax.text(xw1 - 1.0, yw0 + 1.8, "dinding dalam casing (diperlebar di Bawah)", fontsize=5.6, color="#555555", ha="right", va="bottom", zorder=9)
        C_ = S["cradle"]
        for rx_ in C_["ribs_x"]:
            xa_, ya_ = P(rx_ - C_["rib_w"] / 2, C_["y"][0]); xb_, yb_ = P(rx_ + C_["rib_w"] / 2, C_["y"][1])
            ax.add_patch(Rectangle((xa_, ya_), xb_ - xa_, yb_ - ya_, fill=False, ec="#1f4e9c", lw=0.7, ls=(0, (3, 1.5)), zorder=8))
        for sx_ in (BAT["x0"] - 0.4 - C_["stop_w"], BAT["x1"] + 0.4):
            xa_, ya_ = P(sx_, C_["stop_y"][0]); xb_, yb_ = P(sx_ + C_["stop_w"], C_["stop_y"][1])
            ax.add_patch(Rectangle((xa_, ya_), xb_ - xa_, yb_ - ya_, fill=False, ec="#1f4e9c", lw=0.7, ls=(0, (3, 1.5)), zorder=8))
        tx_, ty_ = P(46.5, -37.4)
        ax.text(tx_, ty_, "rusuk + stopper back plate (biru putus)\nmenopang bagian yang menjorok " + fm(pcb["y0"] - b["y0"]) + " mm", fontsize=5.6, color="#1f4e9c", ha="right", va="center", zorder=9)
        lx, ly = P(-30, 13.0)
        ax.text(lx, ly, f"TANPA MENUMPUK: celah {fm(-0.5 - b['y1'])} mm ke tepi Bawah\nmodul AD8232 dan powerbank", fontsize=6.4, color="#1b7a2f", ha="center", va="center", zorder=9,
                bbox=dict(fc="white", ec="#1b7a2f", lw=0.5, pad=1.2, alpha=0.92))
        ax.plot([lx, P(-30, b["y1"] + 0.4)[0]], [ly - 4.5, P(-30, b["y1"] + 0.4)[1]], lw=0.6, color="#1b7a2f", zorder=8)

    # ---- B/C. render jadi + label port
    pf = Panel(ax, os.path.join(REN, "render_rakitan_depan.png"), (230, 195, 182, 82), crop=True, margin=22)
    ax.text(224, 279, "B. Tampak jadi (depan)", fontsize=7.5, fontweight="bold", va="center")
    pt = rj("points_depan.json")
    PF = {k: pf.pt_norm(*v) for k, v in pt.items()}
    if os.environ.get("DBG"): print("PF", {k: tuple(round(x,1) for x in v) for k, v in PF.items()}, "panelB", pf.x0, pf.y0, pf.w_mm, pf.h_mm)
    callout(ax, PF["layar"], "Layar TFT 3,5\" + ECG", at=(368, 236))
    callout(ax, PF["saklar"], "Saklar ON/OFF (Atas)", at=(368, 258))
    callout(ax, PF["kabel_el"], "Kabel elektroda (jack Atas)", ha="right", at=(312, 271))
    callout(ax, PF["usbc"], "USB-C powerbank (Kanan)", ha="right", at=(268, 238))
    callout(ax, PF["gland"], "Gland PG7 + kabel PPG", ha="right", at=(268, 221))
    callout(ax, PF["sensor"], "Sensor PPG (sensor jari)", ha="right", at=(268, 203))
    pr = Panel(ax, os.path.join(REN, "render_rakitan_belakang.png"), (230, 112, 182, 78), crop=True, margin=22)
    ax.text(224, 193, "C. Tampak jadi (belakang): sayap slot sabuk", fontsize=7.5, fontweight="bold", va="center")
    pb_ = rj("points_belakang.json")
    PR = {k: pr.pt_norm(*v) for k, v in pb_.items()}
    if os.environ.get("DBG"): print("PR", {k: tuple(round(x,1) for x in v) for k, v in PR.items()}, "panelC", pr.x0, pr.y0, pr.w_mm, pr.h_mm)
    callout(ax, PR["sekrup"], "Sekrup M3 x 8 (4x)", ha="right", at=(262, 178))
    callout(ax, PR["slot1"], "Slot sabuk 6 x 44 (2x)", ha="right", at=(262, 166))
    callout(ax, PR["plate"], "Back plate", ha="right", at=(262, 128))
    callout(ax, PR["slot2"], "Slot sabuk", at=(346, 116))

    # ---- D. potongan samping (v2: X = -10 mm; v3: X = -12 mm lewat rusuk penyangga, baterai, header AD8232 dan jack)
    sx0, sy0, k = 20, 20, 2.45
    kk = k * (0.95 if not V3 else 0.88)
    zc = lambda z: sy0 + (z + 3.5) * kk
    yc = lambda y: sx0 + (y - YB_OUT) * kk
    X_SEC = -12 if V3 else -10
    ax.text(10, 118, f"D. POTONGAN SAMPING di X = {X_SEC} mm (melalui baterai, " + ("rusuk penyangga, " if V3 else "") + "header AD8232 dan jack)", fontsize=7.5, fontweight="bold", va="center")

    def R(y0_, y1_, z0_, z1_, fc, ec="k", lw=0.5, hatch=None, z=3, alpha=1.0):
        ax.add_patch(Rectangle((yc(y0_), zc(z0_)), (y1_ - y0_) * kk, (z1_ - z0_) * kk, fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=z, alpha=alpha))

    HY_, CAVY = YT_OUT, CAV_YT
    R(YB_OUT, HY_, -3.5, -0.5, "#444444")
    R(YB_OUT, CAV_YB, -0.5, 33.9, "#e08a2a"); R(CAVY, HY_, -0.5, 33.9, "#e08a2a")
    R(YB_OUT, -26, 31.5, 33.9, "#222222"); R(26, HY_, 31.5, 33.9, "#222222")
    R(pcb["y0"], pcb["y1"], 5.0, 6.6, "#2f9a55")
    R(b["y0"], b["y1"], b["z0"], b["z1"], "#f2c230", z=5)
    R(-0.5, 27.5, 10.4, 12.0, "#c8326a", z=4)
    if V3:
        R(-0.5, 2.0, 6.6, 10.4, "#222222", z=4)
        C_ = S["cradle"]
        R(CAV_YB + 0.2, CAV_YB + 1.4, -0.5, 1.5, "#6f86a8", z=4)                       # rim penengah
        R(C_["y"][0], C_["y"][1], -0.5, C_["top"], "#6f86a8", z=4)                      # rusuk di bawah baterai
    else:
        R(-0.5, 2.0, 6.6, 10.4, "#222222", z=6, alpha=0.55, ec="#c00000", lw=0.9)
    R(14.0, 27.5, 12.0, 18.0, "#1a1a1a", z=4); R(27.5, 29.7, 12.2, 17.8, "#1a1a1a", z=4)
    R(-28.17, 28.17, 26.6, 28.2, "#b0201f"); R(-27.5, 27.5, 28.2, 31.2, "#101820")
    if not V3:
        R(-0.5, b["y1"], 10.4, 12.0, "#ffffff", ec="#c00000", lw=0.8, hatch="////", z=7)
    ax.text(yc((b["y0"] + b["y1"]) / 2 - (0 if V3 else 3)), zc(11.6), "BATERAI 10 x 34 x 50", fontsize=6.5, ha="center", va="center", fontweight="bold", zorder=9)
    ax.text(yc(17), zc(11.2), "AD8232", fontsize=6, ha="center", va="center", color="white", zorder=9)
    ax.text(yc(0), zc(29.7), "PCB TFT + kaca", fontsize=6, ha="center", va="center", color="white", zorder=9)
    ax.text(yc((YB_OUT + HY_) / 2), zc(-2.0), "BACK PLATE", fontsize=6, ha="center", va="center", color="white", zorder=9)
    ax.text(yc(-12 if V3 else -6), zc(5.8), "PCB utama", fontsize=5.6, ha="center", va="center", color="white", zorder=9)
    ax.text(yc(YB_OUT) - 1.5, zc(15), "BAWAH", fontsize=7, rotation=90, ha="right", va="center", fontweight="bold", color="#1a4fa0")
    ax.text(yc(HY_) + 1.5, zc(26), "ATAS", fontsize=7, rotation=90, ha="left", va="center", fontweight="bold", color="#1a4fa0")
    ax.text(yc(20), zc(20.5), "jack + plug", fontsize=5.8, ha="center", va="center", zorder=9)
    # garis acuan Z di tepi kanan + dimensi
    xr = yc(HY_) + 5
    for zz in (6.6, 16.6, 26.6):
        ax.plot([yc(b["y1"]), xr + 22], [zc(zz), zc(zz)], lw=0.3, color="#777777", dashes=(5, 2), zorder=2)
    def zd(z0_, z1_, xpos, text):
        ax.annotate("", xy=(xpos, zc(z1_)), xytext=(xpos, zc(z0_)), arrowprops=dict(arrowstyle="<|-|>", lw=0.5, color="k", mutation_scale=5, shrinkA=0, shrinkB=0), zorder=8)
        ax.text(xpos + 1.3, (zc(z0_) + zc(z1_)) / 2, text, fontsize=6.2, va="center", ha="left", zorder=9)
    zd(6.6, 16.6, xr + 10, "10,0  tinggi baterai")
    zd(16.6, 26.6, xr + 10, "10,0  celah ke PCB TFT")
    callout(ax, (yc(CAV_YB + 0.18), zc(9.0)), f"celah {fm(b['y0'] - CAV_YB)} mm ke dinding", 9, 14, fs=6.0)
    if V3:
        zl = 20.6                                                       # garis ukur di atas baterai
        for yy_ in (b["y0"], pcb["y0"]):
            ax.plot([yc(yy_), yc(yy_)], [zc(16.6 if yy_ == b["y0"] else 6.6), zc(zl + 0.8)], lw=0.35, color="k", dashes=(3, 1.5), zorder=8)
        ax.annotate("", xy=(yc(pcb["y0"]), zc(zl)), xytext=(yc(b["y0"]), zc(zl)), arrowprops=dict(arrowstyle="<|-|>", lw=0.5, color="k", mutation_scale=5, shrinkA=0, shrinkB=0), zorder=8)
        ax.text((yc(b["y0"]) + yc(pcb["y0"])) / 2, zc(zl) + 0.9, fm(pcb["y0"] - b["y0"]) + " (menjorok)", fontsize=6.0, ha="center", va="bottom", zorder=9)
        ax.plot([yc(-0.8), yc(-0.8)], [zc(16.6), zc(zl + 0.8)], lw=0.35, color="k", dashes=(3, 1.5), zorder=8)
        callout(ax, (yc(-0.8), zc(14.0)), f"celah {fm(-0.5 - b['y1'])} mm (tidak menumpuk)", 9, 11, fs=6.0)
        callout(ax, (yc(-31.5), zc(2.8)), "rusuk back plate (penopang baterai)", at=(yc(-24.0), zc(1.6)), fs=6.0)
    if V3:
        ax.text(yc(b["y0"]) + 1.0, zc(17.7), "Y = " + fm(b["y0"]), fontsize=5.8, ha="left", zorder=9)
        ax.text(yc(b["y1"]) - 1.0, zc(17.7), "Y = " + fm(b["y1"]), fontsize=5.8, ha="right", zorder=9)
    else:
        ax.text(yc(b["y0"]) + 1, zc(1.2), "Y = " + fm(b["y0"]), fontsize=5.8, zorder=9)
        ax.text(yc(b["y1"]), zc(1.2), "Y = +" + fm(b["y1"]), fontsize=5.8, ha="center", zorder=9)

    # ---- penjelasan
    ax.add_patch(Rectangle((222, 12), 190, 98, fill=False, lw=0.6, ec="k", zorder=2))
    notes_v2 = [
        "PENJELASAN PENEMPATAN BATERAI (sisi Bawah)",
        "1. Baterai PALO 103450 (3,7 V, 2000 mAh, 10 x 34 x 50 mm) rebah di atas PCB, rapat ke sisi Bawah (celah " + fm(b['y0'] + 28.75) + " mm",
        "    ke dinding). Sisi 50 mm sejajar sumbu Kiri-Kanan; sisi 34 mm sejajar Atas-Bawah.",
        "2. Posisi: " + fm(b['x0'] - pcb['x0']) + " mm dari tepi Kanan PCB sampai " + fm(pcb['x1'] - b['x1']) + " mm dari tepi Kiri PCB; Y " + fm(b['y0']) + " ... +" + fm(b['y1']) + " mm.",
        "3. Kabel baterai (merah +, hitam -) di sisi Kiri baterai ke konektor JST 2-pin di PCB (X +11,7; Y -13,1 / -15,1).",
        "4. Puncak baterai Z = 16,6 mm; celah ke PCB TFT (26,6 mm) = 10,0 mm. Saklar (Z 16,5-25,5; X +3) tidak mengganggu.",
        "5. Area kosong PCB sisi Bawah hanya 27,8 mm, baterai 34 mm: menumpuk " + fm(b['y1'] + 0.5) + " mm di atas tepi Bawah modul AD8232",
        "    dan powerbank (pilihan pengguna). Gambar D: baterai rebah penuh, irisan = arsir merah. Pada rakitan nyata tepi baterai",
        "    bertumpu di atas modul (Z >= 12,0), baterai miring sekitar 11 derajat, puncaknya sekitar 22,9 mm (celah 3,7 mm ke PCB TFT).",
        "    Beri isolasi/busa 1 mm antara baterai dan komponen modul.",
        "6. Rumah tidak berubah: rongga dalam 99,0 x 57,5 mm, tinggi dalam 32,0 mm.",
    ]
    over_ = pcb["y0"] - b["y0"]
    notes_v3 = [
        "PENJELASAN PENEMPATAN BATERAI (sisi Bawah) - VERSI v3: TANPA MENUMPUK",
        "1. Baterai PALO 103450 (3,7 V, 2000 mAh, 10 x 34 x 50 mm) rebah di atas PCB. Sisi 50 mm sejajar Kiri-Kanan, sisi 34 mm Atas-Bawah.",
        "2. Posisi: " + fm(b['x0'] - pcb['x0']) + " mm dari tepi Kanan PCB s.d. " + fm(pcb['x1'] - b['x1']) + " mm dari tepi Kiri PCB; Y " + fm(b['y0']) + " ... " + fm(b['y1']) + "; Z 6,6 ... 16,6 mm.",
        "3. Tepi Atas baterai berhenti " + fm(-0.5 - b['y1']) + " mm sebelum tepi Bawah modul AD8232 dan powerbank (Y = -0,5): tidak ada tumpang tindih.",
        "4. PCB hanya menyediakan 27,8 mm, baterai 34 mm, jadi " + fm(over_) + " mm baterai menjorok keluar tepi Bawah PCB. Rongga casing sisi",
        "    Bawah diperlebar " + fm(S['bay']) + " mm (dinding dalam " + fm(CAV_YB - pcb['y0']).replace('-', '') + " mm dari tepi PCB). Lubang dan ukuran lain tidak berubah.",
        "5. Bagian yang menjorok ditopang 3 rusuk dan dijaga 2 stopper di back plate (puncak rusuk 0,15 mm di bawah alas baterai).",
        "6. Celah baterai: 0,4 mm ke dinding Bawah, 10,0 mm ke PCB TFT (Z 26,6). Saklar (Z 16,5-25,5; X +3) dan jack tidak terganggu.",
        "7. Kabel baterai (merah +, hitam -) di sisi Kiri baterai ke konektor JST 2-pin di PCB (X +11,7; Y -13,1 / -15,1).",
        "8. Rekatkan baterai ke PCB dengan double tape tipis; lapisi kapton jika ada pad/jalur terbuka di bawahnya agar tidak korslet.",
    ]
    notes = notes_v3 if V3 else notes_v2
    for i, t in enumerate(notes):
        ax.text(225, 104 - i * 5.2, t, fontsize=6.8 if i else 8.0, fontweight="bold" if i == 0 else "normal", va="center", zorder=7)
    ax.text(225, 104 - len(notes) * 5.2 - 1.0, "TINGGI TIAP LAPISAN (Z, mm, dari ujung ekor baut)", fontsize=7.4, fontweight="bold", va="center")
    zt = [("Back plate", "-3,5 ... -0,5"), ("Ekor baut + mur", "0 ... 5,0"), ("PCB utama", "5,0 ... 6,6"), ("Baterai", "6,6 ... 16,6"),
          ("AD8232 (jack pusat 15,0)", "10,4 ... 12,0"), ("ESP32 DevKit", "15,1 ... 19,8"), ("PCB TFT", "26,6 ... 28,2"), ("Kaca touch", "28,2 ... 31,2"), ("Pelat depan shell", "31,5 ... 33,9")]
    for i, (n_, z_) in enumerate(zt):
        col, row = divmod(i, 5)
        ax.text(225 + col * 95, 104 - len(notes) * 5.2 - 6.5 - row * 4.4, f"{n_}:  {z_}", fontsize=6.8, va="center")
    ax.text(225, 15.5, "CATATAN: gambar 3D adalah ilustrasi; posisi PPG, kapasitor dan konektor kecil diperkirakan dari foto dan Gerber.", fontsize=5.5, va="center", color="#444444")
    return fig


if __name__ == "__main__":
    f1, f2 = page1(), page2()
    with PdfPages(os.path.join(OUTD, "Gambar_Perakitan_Komponen_A3.pdf")) as pdf:
        pdf.savefig(f1, dpi=300); pdf.savefig(f2, dpi=300)
    f1.savefig(os.path.join(OUTD, "Gambar_Perakitan_Hal1_Eksplode_A3.png"), dpi=200)
    f2.savefig(os.path.join(OUTD, "Gambar_Perakitan_Hal2_Penempatan_A3.png"), dpi=200)
    print("OK")
