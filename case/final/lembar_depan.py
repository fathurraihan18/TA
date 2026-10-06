"""Halaman daftar gambar (hal. 1) dan lembar gambar jurnal (hal. terakhir) untuk PDF gabungan.
python lembar_depan.py <fig_jurnal_2kolom.png> <folder_keluaran>
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image
from common import *
import ket

FIG, OUT = sys.argv[1:3]            # FIG = salah satu berkas di folder jurnal (dipakai untuk menemukan folder)
os.makedirs(OUT, exist_ok=True)

LIST = [("PERAKITAN", [(2, "P-1", "Tampak eksplode dan nomor komponen"), (3, "P-2", "Sistem lengkap dan penempatan pada pengguna")]),
        ("GAMBAR KOMPONEN", [(4, "K-1", "ESP32 DevKit C V4"), (5, "K-2", "Modul ECG AD8232"), (6, "K-3", "Sensor PPG MAX30102 (HW-605)"),
                             (7, "K-4", "Elektroda EKG 3 lead dan plug 3,5 mm"), (8, "K-5", "Cable gland PG7 dan saklar KCD11"), (9, "K-6", "Komponen pendukung")]),
        ("GAMBAR TEKNIK COVER", [(10, "T-1", "Tampak depan, atas, bawah, kanan, kiri"), (11, "T-2", "Back plate, isometrik, skema sabuk"),
                                 (12, "T-3", "Potongan A-A, B-B, C-C, D-D"), (13, "T-4", "Penahan sekrup")]),
        ("GAMBAR TEKNIK KLIP PPG", [(14, "C-1", "Potongan dan dimensi utama"), (15, "C-2", "Tampak eksplode dan pemakaian")]),
        ("GAMBAR JURNAL", [(16, "J-1", "Penempatan elektroda RA, LA, RL dan klip PPG")])]


def daftar():
    fig, ax = new_sheet()
    ax.text(210, 276, "Gambar alat ECG + PPG", fontsize=19, fontweight="bold", ha="center", va="center")
    ax.text(210, 262, "Implementasi LightGBM ke ESP32 berbasis sinyal ECG dan PPG", fontsize=9, ha="center", va="center")
    y = 244
    for sec, rows in LIST:
        ax.text(40, y, sec, fontsize=8.0, fontweight="bold", va="center")
        hline(ax, 40, 380, y - 5, lw=0.6)
        y -= 11
        for pg, code, title in rows:
            ax.text(46, y, code, fontsize=8.0, fontweight="bold", va="center")
            ax.text(70, y, title, fontsize=8.0, va="center")
            ax.text(380, y, f"hal. {pg}", fontsize=8.0, va="center", ha="right")
            y -= 8.4
        y -= 4
    ax.text(40, 22, "Keterangan (daftar komponen, spesifikasi, catatan, tabel) ada di berkas terpisah: Keterangan_Gambar_ECG_PPG_A4.pdf", fontsize=6.6, va="center")
    return fig


def jurnal():
    fig, ax = new_sheet()
    ax.text(210, 286.5, "Penempatan elektroda RA, LA, RL dan klip PPG pada pengguna", fontsize=12, fontweight="bold", ha="center", va="center")
    d = os.path.dirname(FIG)
    for fn, bx, by, bw, bh in (("Fig04_Electrode_placement_male_torso.png", 20, 62, 150, 215), ("Fig05_Electrode_details.png", 180, 100, 210, 150)):
        im = Image.open(os.path.join(d, fn)).convert("RGB")
        k = min(bw / im.width, bh / im.height)
        w, h = im.width * k, im.height * k
        x0, y0 = bx + (bw - w) / 2, by + (bh - h) / 2
        ax.imshow(np.asarray(im), extent=(x0, x0 + w, y0, y0 + h), origin="upper", zorder=2, interpolation="lanczos")
    title_block(ax, "Gambar jurnal: penempatan elektroda", "RA merah, LA kuning, RL hijau; klip MAX30102", 16, 16, scale="Skala: tidak diskalakan", ket="J-1")
    return fig


if __name__ == "__main__":
    figs = {"00_Daftar": daftar(), "99_Jurnal": jurnal()}
    for n, f in figs.items():
        with PdfPages(os.path.join(OUT, f"{n}_A3.pdf")) as pdf:
            pdf.savefig(f, dpi=250)
        f.savefig(os.path.join(OUT, f"{n}_A3.png"), dpi=150)
    print("OK")
