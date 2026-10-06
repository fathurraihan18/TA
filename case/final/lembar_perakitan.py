"""Lembar A3 perakitan (2 halaman) untuk draf TA:
Hal. 1  tampak eksplode bernomor (A = lapisan cover, B = modul elektronik di atas PCB) + daftar komponen 17 item.
Hal. 2  sistem lengkap (perangkat + klip PPG + 3 elektroda, tampak rebah) dengan keterangan warna, jalur sambungan, dan tabel penandaan lead.
python lembar_perakitan.py <render_sistem_dir> <render_elektroda_dir> <out_dir>
"""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle
from PIL import Image
from common import *

RS = sys.argv[1]
RE = sys.argv[2]
OUT = sys.argv[3]
os.makedirs(OUT, exist_ok=True)

BOM = [
    (1, "Shell depan", 1, "PETG putih. Jendela layar 3,5\", lubang saklar KCD11, lubang gland PG7, dinding tanpa boss."),
    (2, "Back plate + sayap sabuk", 1, "PETG putih. 2 slot sabuk, lubang sekrup M3 countersunk, penutup belakang."),
    (3, "Penahan sekrup (3 bagian kecil)", 3, "PETG putih. Strip 62 mm (Atas), strip 24 mm dan blok 10 mm (Bawah), masing-masing berlubang M3."),
    (4, "Sekrup M3 x 8 flat head", 4, "Mengunci back plate ke shell melalui penahan (x = +-23 mm, y = +-25,25 mm)."),
    (5, "Layar TFT 3,5\" ILI9488", 1, "480 x 320, modul PCB merah. Dipasang pada 4 standoff."),
    (6, "Standoff M3 20 mm + baut", 4, "Kuning (kuningan). Menghubungkan PCB custom dengan PCB layar."),
    (7, "PCB custom (Gerber)", 1, "Hijau. Tempat ESP32, AD8232, modul powerbank, konektor PPG."),
    (8, "ESP32 DevKit C V4", 1, "ESP32-WROOM-32E, 2 x 19 pin, mikro-USB; pada soket PCB."),
    (9, "Modul ECG AD8232", 1, "PCB merah, jack TRS 3,5 mm menghadap ke tepi PCB."),
    (10, "Modul powerbank / boost", 1, "PCB biru: pengisi baterai + penaik tegangan 5 V."),
    (11, "Baterai PALO 103450", 1, "Li-ion 3,7 V 2000 mAh, 10 x 34 x 50 mm, JST 2-pin."),
    (12, "Saklar rocker KCD11", 1, "10 x 15 mm, snap-in pada dinding Atas shell."),
    (13, "Cable gland PG7 + mur", 1, "Kabel PPG 3 - 6,5 mm menembus dinding Kanan shell (di bawah lubang USB-C)."),
    (14, "Kabel PPG 4 inti", 1, "Dari konektor PCB (JST) melalui gland menuju klip."),
    (15, "Klip pulse oximeter (A, B, C + HW-605)", 1, "Rahang bawah A, rahang atas B, tutup C (cetak 3D) + modul MAX30102 HW-605, pegas, sekrup engsel."),
    (16, "Kabel lead 3 inti + plug TRS 3,5 mm", 1, "Plug masuk jack AD8232; kabel bercabang 3 lead."),
    (17, "Elektroda ECG sekali pakai", 3, "Merah = RA, kuning = LA, hijau = RL (snap konektor)."),
]


def balloon(ax, xy, n, r=3.4):
    ax.add_patch(Circle(xy, r, fc="white", ec="k", lw=0.7, zorder=10))
    ax.text(xy[0], xy[1], str(n), fontsize=7.2, fontweight="bold", ha="center", va="center", zorder=11)


def put(ax, png, box, anc_json=None, pad=10):
    """taruh render (PNG RGBA) terpotong ke dalam box=(x0,y0,w,h) kertas; kembalikan fungsi anchor -> koordinat kertas dan bbox gambar."""
    im = Image.open(png).convert("RGBA")
    crop, cb = crop_alpha(im, pad)
    rx, ry, rw, rh = box
    k = min(rw / crop.width, rh / crop.height)
    w, h = crop.width * k, crop.height * k
    x0, y0 = rx + (rw - w) / 2, ry + (rh - h) / 2
    ax.imshow(np.asarray(crop), extent=(x0, x0 + w, y0, y0 + h), origin="upper", zorder=2, interpolation="lanczos")
    A = None
    if anc_json:
        a = json.load(open(anc_json))
        A = {n: (x0 + (v[0] - cb[0]) * k, y0 + h - (v[1] - cb[1]) * k) for n, v in a.items() if not n.startswith("_")}
    return A, (x0, y0, w, h)


def callouts(ax, A, bbox, numbers, margin=9.0, min_gap=9.5):
    """balon bernomor di dua sisi gambar; garis penunjuk lurus ke titik anchor."""
    x0, y0, w, h = bbox
    xc = x0 + w / 2
    sides = {"L": [], "R": []}
    for key, num in numbers:
        if key not in A: continue
        p = A[key]
        sides["L" if p[0] < xc else "R"].append([key, num, p, p[1]])
    for s, lst in sides.items():
        lst.sort(key=lambda t: t[3])
        for i in range(1, len(lst)):                       # susun agar jarak antar balon >= min_gap
            if lst[i][3] - lst[i - 1][3] < min_gap: lst[i][3] = lst[i - 1][3] + min_gap
        xb = x0 - margin if s == "L" else x0 + w + margin
        for key, num, p, yb in lst:
            ax.plot([p[0], xb], [p[1], yb], lw=0.4, color="k", zorder=8)
            ax.plot([p[0]], [p[1]], marker="o", ms=1.8, color="k", zorder=9)
            balloon(ax, (xb, yb), num)


def bom_table(ax, x, y_top, widths, rows, row_h=6.0, fs=6.2, header=("ITEM", "NAMA KOMPONEN", "JML", "KETERANGAN")):
    import textwrap
    n = len(rows) + 1
    wt = sum(widths)
    ax.add_patch(Rectangle((x, y_top - n * row_h), wt, n * row_h, fill=False, lw=0.7, ec="k", zorder=5))
    ax.add_patch(Rectangle((x, y_top - row_h), wt, row_h, fc="#e9e9e9", ec="k", lw=0.7, zorder=4))
    xx = x
    for c, hd in enumerate(header):
        ax.text(xx + widths[c] / 2 if c in (0, 2) else xx + 1.2, y_top - row_h / 2, hd, fontsize=fs + 0.4, fontweight="bold", ha="center" if c in (0, 2) else "left", va="center", zorder=7)
        xx += widths[c]
    for i, r in enumerate(rows):
        yc = y_top - row_h * (i + 1.5)
        hline(ax, x, x + wt, yc + row_h / 2, lw=0.3)
        xx = x
        for c, cell in enumerate(r):
            txt = str(cell)
            if c == 3: txt = "\n".join(textwrap.wrap(txt, 78))
            if c == 1: txt = "\n".join(textwrap.wrap(txt, 34))
            ax.text(xx + widths[c] / 2 if c in (0, 2) else xx + 1.2, yc, txt, fontsize=fs if c != 3 else fs - 0.4, ha="center" if c in (0, 2) else "left", va="center", zorder=7, linespacing=1.05)
            xx += widths[c]
    xx = x
    for wcol in widths[:-1]:
        xx += wcol
        vline(ax, xx, y_top - n * row_h, y_top, lw=0.3)


def swatch_legend(ax, x, y, items, cols=3, dx=64, dy=5.4, fs=6.1):
    for i, (col, txt) in enumerate(items):
        cx_ = x + (i % cols) * dx
        cy_ = y - (i // cols) * dy
        ax.add_patch(Rectangle((cx_, cy_ - 1.8), 5.0, 3.6, fc=col, ec="k", lw=0.4, zorder=7))
        ax.text(cx_ + 6.5, cy_, txt, fontsize=fs, va="center", zorder=7)


NUM_A = [("shell", 1), ("plate", 2), ("penahan", 3), ("sekrup", 4), ("tft", 5), ("standoff", 6), ("pcb", 7), ("saklar", 12), ("gland", 13)]
NUM_B = [("esp32", 8), ("ad8232", 9), ("boost", 10), ("baterai", 11), ("pcb", 7), ("kabel_ppg_dalam", 14)]

LEG = [("#e6e6e0", "Putih: bagian cetak 3D (PETG)"), ("#2e8f3e", "Hijau: PCB custom (Gerber)"), ("#c4222f", "Merah: PCB layar TFT, modul AD8232"),
       ("#1d4fa8", "Biru: modul powerbank / boost"), ("#e1b53a", "Kuning: baterai, standoff"), ("#2a2a2e", "Hitam/abu: ESP32, header, saklar"),
       ("#d6202a", "Elektroda merah = RA (lengan kanan)"), ("#f2cf1d", "Elektroda kuning = LA (lengan kiri)"), ("#2fa046", "Elektroda hijau = RL (kaki kanan)")]


def page1():
    fig, ax = new_sheet()
    ax.text(210, 287.5, "Desain 3D alat ECG + PPG beserta komponennya (tampak eksplode)", fontsize=13, fontweight="bold", ha="center", va="center")
    # ---- panel A
    label(ax, 14, 280, "A", 11, ha="left")
    ax.text(24, 280, "Lapisan cover (urutan dari atas: shell, layar, tumpukan PCB, penahan, back plate, sekrup)", fontsize=6.6, va="center")
    A, bb = put(ax, os.path.join(RS, "eksplode_a.png"), (30, 42, 118, 232), os.path.join(RS, "eksplode_a.png.json"))
    callouts(ax, A, bb, NUM_A)
    # ---- panel B
    label(ax, 178, 280, "B", 11, ha="left")
    ax.text(188, 280, "Modul elektronik di atas PCB custom (diangkat)", fontsize=6.6, va="center")
    A2, bb2 = put(ax, os.path.join(RS, "eksplode_b.png"), (198, 190, 196, 86), os.path.join(RS, "eksplode_b.png.json"))
    callouts(ax, A2, bb2, NUM_B, margin=7.0, min_gap=9.0)
    # ---- BOM
    bom_table(ax, 172, 184, [11, 60, 10, 157], [(a, b, c, d) for a, b, c, d in BOM], row_h=6.2)
    # ---- legenda warna + catatan
    ax.text(10, 36, "KETERANGAN WARNA", fontsize=7.0, fontweight="bold", va="center")
    swatch_legend(ax, 10, 30.5, LEG, cols=3, dx=80, dy=5.2)
    notes = ["Catatan: (1) Baterai digambar rebah penuh; tepinya bertumpu di atas modul AD8232 dan powerbank (beri isolasi/busa 1 mm); casing tidak berubah.",
             "(2) Klip pulse oximeter (item 15) dan elektroda (item 17) berada di luar casing: lihat halaman 2.   (3) Gambar 3D ilustrasi; dua dari empat sekrup (item 4) tertutup back plate pada sudut pandang ini. Ukuran: lihat gambar teknik."]
    for i, t in enumerate(notes):
        ax.text(10, 11.2 - i * 3.6, t, fontsize=5.6, va="center")
    title_block(ax, "Perakitan: tampak eksplode dan daftar komponen", "ECG + PPG (ESP32, TFT 3,5\", AD8232, MAX30102)", 1, 2, scale="Skala: tidak diskalakan")
    return fig


def page2(hero_png):
    fig, ax = new_sheet()
    ax.text(210, 287.5, "Sistem lengkap: perangkat, klip pulse oximeter, kabel lead dan 3 elektroda ECG", fontsize=13, fontweight="bold", ha="center", va="center")
    A, bb = put(ax, hero_png, (10, 100, 400, 180), os.path.join(RS, "hero.png.json") if os.path.exists(os.path.join(RS, "hero.png.json")) else None, pad=14)
    return fig, ax, A, bb


if __name__ == "__main__":
    pages = [page1()]
    hero = os.path.join(RS, "hero.png")
    if os.path.exists(hero):
        try:
            import lembar_perakitan_p2
            pages.append(lembar_perakitan_p2.make(hero, RS, RE, sys.modules[__name__]))
        except ImportError:
            pages.append(page2(hero)[0])
    with PdfPages(os.path.join(OUT, "Gambar_Perakitan_ECG_PPG_A3.pdf")) as pdf:
        for f in pages: pdf.savefig(f, dpi=250)
    for i, f in enumerate(pages, 1):
        f.savefig(os.path.join(OUT, f"Gambar_Perakitan_Hal{i}_A3.png"), dpi=200)
    print("OK", len(pages), "halaman")
