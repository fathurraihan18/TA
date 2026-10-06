"""Halaman 2 lembar perakitan: sistem lengkap (render hero), penempatan pada tubuh (gambar jurnal), tabel lead dan jalur sambungan."""
import os, json
import numpy as np
from PIL import Image
from matplotlib.patches import Rectangle
from common import *

CROP = (324, 330, 1884, 1390)                 # kotak potong pada hero.png (2400 x 1500)
# titik tunjuk tambahan pada hero (piksel hero.png): konektor elektroda dan kabel lead
EXTRA = {"RA": (1386, 416), "LA": (1506, 702), "RL": (1662, 512), "lead": (1085, 600)}


def make(hero_png, RS, RE, M):
    fig, ax = new_sheet()
    ax.text(210, 287.5, "Sistem lengkap: perangkat, klip pulse oximeter, kabel lead, dan 3 elektroda ECG", fontsize=13, fontweight="bold", ha="center", va="center")
    # ------------------------------------------------ panel A: hero
    label(ax, 12, 280, "A", 11, ha="left")
    ax.text(21, 280, "Sistem lengkap (tampak rebah di meja; layar menghadap atas)", fontsize=6.6, va="center")
    im = Image.open(hero_png).convert("RGB").crop(CROP)
    bx, by, bw, bh = 8, 112, 252, 164
    k = min(bw / im.width, bh / im.height)
    w, h = im.width * k, im.height * k
    x0, y0 = bx + (bw - w) / 2, by + (bh - h) / 2
    ax.imshow(np.asarray(im), extent=(x0, x0 + w, y0, y0 + h), origin="upper", zorder=2, interpolation="lanczos")
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=0.5, ec="k", zorder=3))
    A = json.load(open(os.path.join(RS, "hero.png.json")))
    A.update({k_: list(v) for k_, v in EXTRA.items()})
    P = lambda n: (x0 + (A[n][0] - CROP[0]) * k, y0 + h - (A[n][1] - CROP[1]) * k)
    pm = lambda dx, dy: (dx * 0.21, 297 - dy * 0.21)               # koordinat tampilan pratinjau 2000 px -> mm kertas
    shell_pt = pm(520, 598)                                          # titik pada dinding Bawah shell
    L = [("tft", "(5) Layar TFT 3,5\" ILI9488", P("tft"), (6, 20), "left"),
         ("shell", "(1, 2) Casing: shell depan + back plate", shell_pt, (-8, -24), "left"),
         ("gland", "(13) Cable gland PG7", P("gland"), pm(295, 505), "abs_r"),
         ("kabel_ppg_luar", "(14) Kabel PPG 4 inti", P("kabel_ppg_luar"), pm(196, 556), "abs_r"),
         ("klip", "(15) Klip pulse oximeter\n      (+ modul MAX30102 HW-605)", P("klip"), (14, -7), "left"),
         ("plug", "(16) Kabel lead 3 inti + plug TRS 3,5 mm", P("plug"), (-6, 18), "right"),
         ("RA", "(17) Elektroda RA (merah)", P("RA"), (10, 7), "left"),
         ("RL", "(17) Elektroda RL (hijau)", P("RL"), pm(1203, 188), "abs_r"),
         ("LA", "(17) Elektroda LA (kuning)", P("LA"), (12, -4), "left")]
    for key, txt, p, off, ha in L:
        if ha.startswith("abs"):
            q = off; ha = "right"
        else:
            q = (p[0] + off[0], p[1] + off[1])
        leader(ax, p, q, txt, ha=ha)
    # ------------------------------------------------ panel B: penempatan di tubuh
    label(ax, 274, 280, "B", 11, ha="left")
    ax.text(283, 280, "Penempatan pada pengguna (ilustrasi)", fontsize=6.6, va="center")
    import glob
    fig1 = glob.glob(os.path.join(os.path.dirname(os.path.dirname(RS)), "*Gambar_Jurnal", "Fig_Elektroda_1kolom.png"))[0]
    imb = Image.open(fig1).convert("RGB")
    bx, by, bw, bh = 270, 64, 142, 212
    kb = min(bw / imb.width, bh / imb.height)
    wb, hb = imb.width * kb, imb.height * kb
    xb = bx + (bw - wb) / 2
    yb = by + (bh - hb) / 2
    ax.imshow(np.asarray(imb), extent=(xb, xb + wb, yb, yb + hb), origin="upper", zorder=2, interpolation="lanczos")
    # ------------------------------------------------ tabel 1: lead
    tx, ty = 8, 106
    ax.text(tx, ty, "PENANDAAN LEAD ELEKTRODA (item 17)", fontsize=7.0, fontweight="bold", va="center")
    cw = [14, 22, 86, 122]
    rows = [("LEAD", "WARNA", "PENEMPATAN PADA TUBUH", "KETERANGAN"),
            ("RA", "Merah", "Bawah klavikula kanan (dekat bahu kanan)", "Right Arm: elektroda lengan kanan"),
            ("LA", "Kuning", "Bawah klavikula kiri (dekat bahu kiri)", "Left Arm: elektroda lengan kiri"),
            ("RL", "Hijau", "Perut kanan bawah (di atas pinggul kanan)", "Right Leg: elektroda referensi")]
    _table(ax, tx, ty - 3, cw, rows, rh=5.4, fs=6.2, cols_center=(0, 1))
    for i, col in enumerate(("#d6202a", "#f2cf1d", "#2fa046")):
        ax.add_patch(Rectangle((tx + cw[0] + cw[1] - 5.2, ty - 3 - 5.4 * (i + 1.5) - 1.4), 3.6, 2.8, fc=col, ec="k", lw=0.3, zorder=8))
    # ------------------------------------------------ tabel 2: jalur sambungan
    ty2 = 76
    ax.text(tx, ty2, "JALUR SAMBUNGAN SINYAL DAN DAYA", fontsize=7.0, fontweight="bold", va="center")
    cw2 = [22, 222]
    rows2 = [("JALUR", "URUTAN KOMPONEN (nomor item sesuai daftar komponen pada halaman 1)"),
             ("ECG", "Elektroda RA, LA, RL (17)  >  kabel lead 3 inti + plug TRS 3,5 mm (16)  >  jack modul AD8232 (9) pada dinding Atas  >  masukan ADC ESP32 (8)"),
             ("PPG", "HW-605 MAX30102 di klip (15)  >  kabel 4 inti VIN, GND, SDA, SCL (14)  >  gland PG7 (13) pada dinding Kanan  >  konektor PCB (7)  >  I2C ESP32 (8)"),
             ("Daya", "Baterai PALO 103450 (11)  >  modul powerbank/boost (10)  >  PCB custom (7) dan ESP32 (8); saklar KCD11 (12) pada dinding Atas"),
             ("Tampilan", "ESP32 (8)  >  konektor PCB custom (7)  >  layar TFT ILI9488 3,5\" (5) pada standoff (6)")]
    _table(ax, tx, ty2 - 3, cw2, rows2, rh=5.4, fs=5.9, cols_center=(0,))
    # ------------------------------------------------ catatan + legenda
    ax.text(tx, 42, "KETERANGAN WARNA", fontsize=7.0, fontweight="bold", va="center")
    M.swatch_legend(ax, tx, 37, M.LEG, cols=3, dx=82, dy=5.0, fs=5.9)
    notes = ["Catatan: (1) Elektroda, kabel lead, dan klip pada gambar A adalah model 3D ilustrasi (elektroda snap sekali pakai; warna sesuai lead).",
             "(2) Pewarnaan lead mengikuti kabel yang digunakan pada alat ini (merah RA, kuning LA, hijau RL).   (3) Gambar B hanya ilustrasi penempatan, bukan model medis."]
    for i, t in enumerate(notes):
        ax.text(tx, 15.2 - i * 3.6 + 0.0, t, fontsize=5.5, va="center")
    M.title_block(ax, "Sistem lengkap dan penempatan pada pengguna", "ECG + PPG (ESP32, TFT 3,5\", AD8232, MAX30102)", 2, 2, scale="Skala: tidak diskalakan")
    return fig


def _table(ax, x, y_top, widths, rows, rh=5.4, fs=6.2, cols_center=()):
    n = len(rows)
    wt = sum(widths)
    ax.add_patch(Rectangle((x, y_top - n * rh), wt, n * rh, fill=False, lw=0.7, ec="k", zorder=5))
    ax.add_patch(Rectangle((x, y_top - rh), wt, rh, fc="#e9e9e9", ec="k", lw=0.7, zorder=4))
    for i, r in enumerate(rows):
        yc = y_top - rh * (i + 0.5)
        if i > 0: hline(ax, x, x + wt, yc + rh / 2, lw=0.3)
        xx = x
        for c, cell in enumerate(r):
            ctr = c in cols_center
            ax.text(xx + (widths[c] / 2 if ctr else 1.2), yc, cell, fontsize=fs + (0.3 if i == 0 else 0), fontweight="bold" if i == 0 or c == 0 else "normal",
                    ha="center" if ctr else "left", va="center", zorder=7)
            xx += widths[c]
    xx = x
    for wc in widths[:-1]:
        xx += wc
        vline(ax, xx, y_top - n * rh, y_top, lw=0.3)
