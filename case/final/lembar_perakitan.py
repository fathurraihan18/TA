"""Lembar A3 perakitan (2 halaman) untuk draf TA. Tulisan dibuat besar; daftar komponen, tabel, dan catatan ditulis ke berkas keterangan (ket.py).
Hal. 1  tampak eksplode bernomor (A = lapisan cover, B = modul elektronik di atas PCB) + nama tiap nomor + warna.
Hal. 2  sistem lengkap (perangkat, klip PPG, 3 elektroda) dan penempatan pada pengguna.
python lembar_perakitan.py <render_sistem_dir> <out_dir> [fig_jurnal_1kolom.png]
"""
import os, sys, json, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle
from PIL import Image
from common import *
import ket

RS = sys.argv[1]
OUT = sys.argv[2]
FIG1 = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)

BOM = [
    (1, "Shell depan", 1, "PETG putih. Jendela layar 3,5\", lubang saklar KCD11, lubang gland PG7, dinding tanpa boss."),
    (2, "Back plate + sayap sabuk", 1, "PETG putih. 2 slot sabuk, 4 lubang sekrup M3 countersunk."),
    (3, "Penahan sekrup (3 bagian kecil)", 3, "PETG putih. Strip 62 mm (Atas), strip 24 mm dan blok 10 mm (Bawah), masing-masing berlubang pilot M3."),
    (4, "Sekrup M3 x 8 flat head", 4, "Mengunci back plate ke shell melalui penahan (x = +-23 mm, y = +-25,25 mm)."),
    (5, "Layar TFT 3,5\" ILI9488", 1, "480 x 320 piksel, modul PCB merah. Dipasang pada 4 standoff."),
    (6, "Standoff M3 20 mm + baut", 4, "Kuningan. Menghubungkan PCB custom dengan PCB layar."),
    (7, "PCB custom (Gerber)", 1, "Hijau. Tempat ESP32, AD8232, modul powerbank, dan konektor PPG."),
    (8, "ESP32 DevKit C V4", 1, "ESP32-WROOM-32E, 2 x 19 pin, mikro-USB; dipasang pada soket PCB."),
    (9, "Modul ECG AD8232", 1, "PCB merah. Jack TRS 3,5 mm menghadap ke tepi Atas casing."),
    (10, "Modul powerbank / boost", 1, "PCB biru: pengisi baterai dan penaik tegangan 5 V, port USB-C ke dinding Kanan."),
    (11, "Baterai PALO 103450", 1, "Li-ion 3,7 V 2000 mAh, 10 x 34 x 50 mm, konektor JST 2 pin."),
    (12, "Saklar rocker KCD11", 1, "10 x 15 mm, snap-in pada dinding Atas shell."),
    (13, "Cable gland PG7 + mur", 1, "Kabel PPG 3 - 6,5 mm menembus dinding Kanan shell (di bawah lubang USB-C)."),
    (14, "Kabel PPG 4 inti", 1, "Dari konektor PCB (JST) lewat gland menuju klip: VIN, GND, SDA, SCL."),
    (15, "Klip pulse oximeter + HW-605", 1, "Rahang bawah A, rahang atas B, tutup C (cetak 3D), modul MAX30102 HW-605, pegas, sekrup engsel."),
    (16, "Kabel lead 3 inti + plug TRS", 1, "Plug 3,5 mm masuk ke jack AD8232; kabel bercabang 3 lead."),
    (17, "Elektroda ECG sekali pakai", 3, "Merah = RA, kuning = LA, hijau = RL (konektor snap)."),
]
SHORT = {1: "Shell depan", 2: "Back plate + sayap", 3: "Penahan sekrup", 4: "Sekrup M3 x 8", 5: "Layar TFT 3,5\"", 6: "Standoff M3 20 mm", 7: "PCB custom",
         8: "ESP32 DevKit C V4", 9: "Modul AD8232", 10: "Modul powerbank", 11: "Baterai PALO 103450", 12: "Saklar KCD11", 13: "Cable gland PG7",
         14: "Kabel PPG 4 inti", 15: "Klip pulse oximeter", 16: "Kabel lead + plug TRS", 17: "Elektroda ECG (3)"}


def balloon(ax, xy, n, r=4.6):
    ax.add_patch(Circle(xy, r, fc="white", ec="k", lw=0.9, zorder=10))
    ax.text(xy[0], xy[1], str(n), fontsize=7.2, fontweight="bold", ha="center", va="center", zorder=11)


def put(ax, png, box, anc_json=None, pad=10):
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


def callouts(ax, A, bbox, numbers, margin=10.0, min_gap=11.5):
    x0, y0, w, h = bbox
    xc = x0 + w / 2
    sides = {"L": [], "R": []}
    for key, num in numbers:
        if key not in A: continue
        p = A[key]
        sides["L" if p[0] < xc else "R"].append([key, num, p, p[1]])
    for s, lst in sides.items():
        lst.sort(key=lambda t: t[3])
        for i in range(1, len(lst)):
            if lst[i][3] - lst[i - 1][3] < min_gap: lst[i][3] = lst[i - 1][3] + min_gap
        xb = x0 - margin if s == "L" else x0 + w + margin
        for key, num, p, yb in lst:
            ax.plot([p[0], xb], [p[1], yb], lw=0.5, color="k", zorder=8)
            ax.plot([p[0]], [p[1]], marker="o", ms=2.4, color="k", zorder=9)
            balloon(ax, (xb, yb), num)


def swatch_legend(ax, x, y, items, cols=3, dx=64, dy=7.0, fs=6.1, sw=6.5):
    for i, (col, txt) in enumerate(items):
        cx_ = x + (i % cols) * dx
        cy_ = y - (i // cols) * dy
        ax.add_patch(Rectangle((cx_, cy_ - sw / 2), sw, sw * 0.7, fc=col, ec="k", lw=0.5, zorder=7))
        ax.text(cx_ + sw + 2, cy_ - sw * 0.15, txt, fontsize=fs, va="center", zorder=7)


NUM_A = [("shell", 1), ("plate", 2), ("penahan", 3), ("sekrup", 4), ("tft", 5), ("standoff", 6), ("pcb", 7), ("saklar", 12), ("gland", 13)]
NUM_B = [("esp32", 8), ("ad8232", 9), ("boost", 10), ("baterai", 11), ("pcb", 7), ("kabel_ppg_dalam", 14)]

LEG = [("#e6e6e0", "Putih: cetak 3D"), ("#2e8f3e", "Hijau: PCB custom"), ("#c4222f", "Merah: PCB layar, AD8232"),
       ("#1d4fa8", "Biru: powerbank"), ("#e1b53a", "Kuning: baterai, standoff"), ("#2a2a2e", "Hitam: ESP32, header, saklar")]
LEAD = [("#d6202a", "RA", "merah", "bawah klavikula kanan"), ("#f2cf1d", "LA", "kuning", "bawah klavikula kiri"), ("#2fa046", "RL", "hijau", "perut kanan bawah")]


def page1():
    fig, ax = new_sheet()
    ax.text(210, 286.5, "Desain 3D alat ECG + PPG beserta komponennya (tampak eksplode)", fontsize=13, fontweight="bold", ha="center", va="center")
    label(ax, 12, 276, "A", 11, ha="left")
    ax.text(21, 276, "Lapisan cover", fontsize=7.5, va="center")
    A, bb = put(ax, os.path.join(RS, "eksplode_a.png"), (30, 44, 125, 226), os.path.join(RS, "eksplode_a.png.json"))
    callouts(ax, A, bb, NUM_A)
    label(ax, 182, 276, "B", 11, ha="left")
    ax.text(191, 276, "Modul elektronik di atas PCB custom", fontsize=7.5, va="center")
    A2, bb2 = put(ax, os.path.join(RS, "eksplode_b.png"), (200, 148, 200, 120), os.path.join(RS, "eksplode_b.png.json"))
    callouts(ax, A2, bb2, NUM_B, margin=8.0, min_gap=10.5)
    # nama tiap nomor (dua kolom)
    ax.text(180, 140, "Nomor komponen", fontsize=7.5, fontweight="bold", va="center")
    for i in range(17):
        col = 0 if i < 9 else 1
        row = i if i < 9 else i - 9
        xx, yy = 182 + col * 118, 130 - row * 7.6
        balloon(ax, (xx + 4.6, yy), i + 1, r=3.6)
        ax.text(xx + 11, yy, SHORT[i + 1], fontsize=6.6, va="center")
    ax.text(10, 40, "Warna", fontsize=7.5, fontweight="bold", va="center")
    swatch_legend(ax, 10, 32, LEG, cols=3, dx=82, dy=8.5, fs=6.4, sw=6.5)
    title_block(ax, "Perakitan: tampak eksplode", "ECG + PPG (ESP32, TFT 3,5\", AD8232, MAX30102)", 1, 2, scale="Skala: tidak diskalakan", ket="P-1")
    return fig


CROP = (324, 330, 1884, 1390)                 # kotak potong pada hero.png (2400 x 1500)
EXTRA = {"RA": (1386, 416), "LA": (1506, 702), "RL": (1662, 512), "lead": (1085, 600)}


def page2():
    fig, ax = new_sheet()
    ax.text(210, 286.5, "Sistem lengkap: perangkat, klip pulse oximeter, kabel lead, dan 3 elektroda ECG", fontsize=13, fontweight="bold", ha="center", va="center")
    label(ax, 12, 276, "A", 11, ha="left")
    ax.text(21, 276, "Tampak rebah di meja, layar menghadap atas", fontsize=7.5, va="center")
    im = Image.open(os.path.join(RS, "hero.png")).convert("RGB").crop(CROP)
    bx, by, bw, bh = 8, 98, 258, 172
    k = min(bw / im.width, bh / im.height)
    w, h = im.width * k, im.height * k
    x0, y0 = bx + (bw - w) / 2, by + (bh - h) / 2
    ax.imshow(np.asarray(im), extent=(x0, x0 + w, y0, y0 + h), origin="upper", zorder=2, interpolation="lanczos")
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=0.6, ec="k", zorder=3))
    A = json.load(open(os.path.join(RS, "hero.png.json")))
    A.update({k_: list(v) for k_, v in EXTRA.items()})
    P = lambda n: (x0 + (A[n][0] - CROP[0]) * k, y0 + h - (A[n][1] - CROP[1]) * k)
    pm = lambda dx, dy: (dx * 0.21, 297 - dy * 0.21)
    L = [("tft", "5  Layar TFT", P("tft"), (4, 18), "left"),
         ("shell", "1, 2  Casing", pm(560, 645), pm(450, 770), "abs_l"),
         ("gland", "13  Gland PG7", P("gland"), pm(280, 505), "abs_r"),
         ("kabel_ppg_luar", "14  Kabel PPG", P("kabel_ppg_luar"), pm(215, 545), "abs_r"),
         ("klip", "15  Klip PPG", P("klip"), (16, -6), "left"),
         ("plug", "16  Kabel lead + plug", P("plug"), (-6, 20), "right"),
         ("RA", "17  RA (merah)", P("RA"), (10, 7), "left"),
         ("RL", "17  RL (hijau)", P("RL"), pm(1203, 190), "abs_r"),
         ("LA", "17  LA (kuning)", P("LA"), (12, -4), "left")]
    for key, txt, p, off, ha in L:
        if ha.startswith("abs"):
            q = off; ha = "right" if ha == "abs_r" else "left"
        else:
            q = (p[0] + off[0], p[1] + off[1])
        leader(ax, p, q, txt, ha=ha)
    label(ax, 274, 276, "B", 11, ha="left")
    ax.text(283, 276, "Penempatan pada pengguna", fontsize=7.5, va="center")
    fig1 = FIG1 or glob.glob(os.path.join(os.path.dirname(os.path.dirname(RS)), "*Gambar_Jurnal", "Fig_Elektroda_1kolom.png"))[0]
    imb = Image.open(fig1).convert("RGB")
    bx, by, bw, bh = 268, 62, 146, 208
    kb = min(bw / imb.width, bh / imb.height)
    wb, hb = imb.width * kb, imb.height * kb
    xb, yb = bx + (bw - wb) / 2, by + (bh - hb) / 2
    ax.imshow(np.asarray(imb), extent=(xb, xb + wb, yb, yb + hb), origin="upper", zorder=2, interpolation="lanczos")
    # warna lead (kode warna elektroda)
    ax.text(10, 87, "Kode warna elektroda", fontsize=7.5, fontweight="bold", va="center")
    for i, (col, lb, nm, pos) in enumerate(LEAD):
        yy = 76 - i * 11
        ax.add_patch(Rectangle((10, yy - 4), 17, 8, fc=col, ec="k", lw=0.6, zorder=7))
        ax.text(18.5, yy, lb, fontsize=7.0, fontweight="bold", ha="center", va="center", color="white" if lb != "LA" else "black", zorder=8)
        ax.text(31, yy, f"{nm}: {pos}", fontsize=7.0, va="center")
    ax.text(10, 34, "Warna komponen", fontsize=7.5, fontweight="bold", va="center")
    swatch_legend(ax, 10, 26, LEG, cols=3, dx=82, dy=8.5, fs=6.4, sw=6.5)
    title_block(ax, "Sistem lengkap dan penempatan pada pengguna", "ECG + PPG (ESP32, TFT 3,5\", AD8232, MAX30102)", 2, 2, scale="Skala: tidak diskalakan", ket="P-2")
    return fig


def write_ket():
    ket.begin("P-1", "Perakitan: tampak eksplode dan daftar komponen")
    ket.table(["No.", "Nama komponen", "Jml", "Keterangan"], [[a, b, c, d] for a, b, c, d in BOM], widths=[0.9, 3.2, 0.8, 7.0], align=["c", "l", "c", "l"])
    ket.sub("Warna pada gambar")
    ket.items(["Putih: bagian cetak 3D (PETG).", "Hijau: PCB custom (Gerber).", "Merah: PCB layar TFT dan modul AD8232.", "Biru: modul powerbank.",
               "Kuning: baterai dan standoff.", "Hitam dan abu: ESP32, header, saklar."])
    ket.sub("Catatan")
    ket.items(["Baterai digambar rebah penuh. Ruang kosong sisi Bawah hanya 27,8 mm sedangkan baterai 34 mm, jadi tepinya menumpuk 6,1 mm di atas modul AD8232 dan powerbank. "
               "Di rakitan nyata baterai agak miring (sekitar 11 derajat) dan perlu isolasi atau busa 1 mm. Casing tidak diubah.",
               "Dua dari empat sekrup (item 4) tertutup back plate pada sudut pandang ini.",
               "Klip (item 15) dan elektroda (item 17) berada di luar casing, lihat gambar halaman 2.",
               "Gambar 3D hanya ilustrasi. Ukuran ada di gambar teknik."], numbered=True)
    ket.begin("P-2", "Sistem lengkap dan penempatan pada pengguna")
    ket.sub("Penandaan lead elektroda (item 17)")
    ket.table(["Lead", "Warna", "Penempatan pada tubuh", "Keterangan"],
              [["RA", "Merah", "Bawah klavikula kanan, dekat bahu kanan", "Right Arm: elektroda lengan kanan"],
               ["LA", "Kuning", "Bawah klavikula kiri, dekat bahu kiri", "Left Arm: elektroda lengan kiri"],
               ["RL", "Hijau", "Perut kanan bawah, di atas pinggul kanan", "Right Leg: elektroda referensi"]], widths=[0.8, 1.2, 4.2, 4.0], align=["c", "c", "l", "l"])
    ket.sub("Jalur sambungan sinyal dan daya (nomor item sesuai P-1)")
    ket.table(["Jalur", "Urutan komponen"],
              [["ECG", "Elektroda RA, LA, RL (17) > kabel lead 3 inti + plug TRS 3,5 mm (16) > jack modul AD8232 (9) di dinding Atas > masukan ADC ESP32 (8)"],
               ["PPG", "HW-605 MAX30102 di klip (15) > kabel 4 inti VIN, GND, SDA, SCL (14) > gland PG7 (13) di dinding Kanan > konektor PCB (7) > I2C ESP32 (8)"],
               ["Daya", "Baterai PALO 103450 (11) > modul powerbank/boost (10) > PCB custom (7) dan ESP32 (8). Saklar KCD11 (12) di dinding Atas."],
               ["Tampilan", "ESP32 (8) > konektor PCB custom (7) > layar TFT ILI9488 3,5\" (5) yang dipasang pada standoff (6)"]], widths=[1.2, 9.0], align=["c", "l"])
    ket.sub("Catatan")
    ket.items(["Elektroda, kabel lead, dan klip pada gambar A adalah model 3D ilustrasi (elektroda snap sekali pakai). Warnanya mengikuti kabel yang dipakai di alat: merah RA, kuning LA, hijau RL.",
               "Gambar B hanya menunjukkan penempatan. Torso adalah model 3D untuk ilustrasi, bukan model medis. Klip PPG dipasang di jari telunjuk kanan."], numbered=True)
    ket.save(os.path.join(OUT, "ket_perakitan.json"))


if __name__ == "__main__":
    pages = [page1(), page2()]
    write_ket()
    with PdfPages(os.path.join(OUT, "Gambar_Perakitan_ECG_PPG_A3.pdf")) as pdf:
        for f in pages: pdf.savefig(f, dpi=250)
    for i, f in enumerate(pages, 1):
        f.savefig(os.path.join(OUT, f"Gambar_Perakitan_Hal{i}_A3.png"), dpi=200)
    print("OK", len(pages), "halaman")
