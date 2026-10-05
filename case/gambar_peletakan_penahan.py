"""Denah peletakan 3 penahan (varian --penahan --strip) di dalam shell, tampak depan-belakang dari belakang, dengan nomor, koordinat, dan zona terlarang.
python gambar_peletakan_penahan.py <folder_penahan> <berkas_png>
Orientasi gambar sama dengan semua gambar tampak depan dan dengan pratinjau plate: KANAN perangkat (-X, sisi gland/USB-C) di KIRI gambar,
KIRI perangkat (+X) di kanan gambar, ATAS (+Y, sisi jack AD8232 + saklar) di atas.
"""
import sys, os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

D, OUTF = sys.argv[1:3]
S = json.load(open(os.path.join(D, "_ref", "summary.json"))); P = S["penahan"]
holes = json.load(open(os.path.join(D, "data", "pcb_holes.json")))["holes"]
XH, YH = 56.007, 33.655
CX, CY = S["cavity"][0] / 2, S["cavity"][1] / 2
OX, OY = S["outer"][0] / 2, S["outer"][1] / 2
PC = ["#e91e8c", "#f28c0f", "#14aacc"]
NAME = ["1", "2", "3"]

fig = plt.figure(figsize=(16.54, 11.69), dpi=170); fig.patch.set_facecolor("white")
fig.text(0.5, 0.965, "Peletakan 3 penahan sekrup di dalam shell (denah tembus, tampak seperti dari depan: KANAN di kiri gambar)", ha="center", fontsize=17, fontweight="bold")
ax = fig.add_axes([0.04, 0.34, 0.92, 0.58]); ax.set_aspect("equal"); ax.axis("off")
ax.set_xlim(-OX - 12, OX + 12); ax.set_ylim(-OY - 14, OY + 14)

# dinding
ax.add_patch(Rectangle((-OX, -OY), 2 * OX, 2 * OY, fc="#f0c58a", ec="k", lw=1.2, zorder=1))
ax.add_patch(Rectangle((-CX, -CY), 2 * CX, 2 * CY, fc="white", ec="k", lw=1.0, zorder=2))
# PCB (garis putus)
pc = S["pcb"]
ax.add_patch(Rectangle((pc["x0"], pc["y0"]), pc["x1"] - pc["x0"], pc["y1"] - pc["y0"], fc="#2e9a55", alpha=0.10, ec="#2e9a55", lw=1.2, ls="--", zorder=3))
# kaki / lubang PCB
for h in holes:
    ax.add_patch(Circle((-(h["xg"] - XH), -(h["yg"] - YH)), max(h["d"], 0.6) / 2 + 0.5, fc="#2e9a55", ec="none", alpha=0.35, zorder=4))
ax.text(0, 0.5, "PCB utama + komponen (kaki / solder di belakang PCB = titik hijau)", ha="center", va="center", fontsize=11, color="#1e6b3a", zorder=6)
# lubang baut PCB
for mx, my in S["mount_holes"]:
    ax.add_patch(Circle((mx, my), 1.6, fc="none", ec="#1e6b3a", lw=1.0, zorder=5))

# port pada dinding
def port(x0, x1, y0, y1, label, tx, ty, ha="center", va="center", col="#b00020"):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#ffd0d0", ec=col, lw=1.2, zorder=7))
    ax.text(tx, ty, label, color=col, fontsize=10.5, ha=ha, va=va, fontweight="bold", zorder=9,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))

j = S["jack"]; sw = S["switch"]; mi = S["micro"]; us = S["usbc"]; gl = S["gland"]
port(j["x"] - 3.5, j["x"] + 3.5, CY, OY, "", 0, 0)
port(sw["x"] - 7, sw["x"] + 7, CY, OY, "", 0, 0)
port(mi["x"] - 6, mi["x"] + 6, -OY, -CY, "", 0, 0)
port(-OX, -CX, us["y"] - 5.2, us["y"] + 5.2, "", 0, 0)
ax.add_patch(Rectangle((-OX, gl["y"] - gl["hole"] / 2), OX - CX, gl["hole"], fc="#ffd0d0", ec="#b00020", lw=1.2, zorder=7))
ax.text(j["x"], OY + 3.2, "lubang jack AD8232\nx = %.1f" % j["x"], color="#b00020", fontsize=10, ha="center", fontweight="bold")
ax.text(sw["x"] + 3, OY + 3.2, "saklar\nx = %.1f" % sw["x"], color="#b00020", fontsize=10, ha="center", fontweight="bold")
ax.text(mi["x"], -OY - 4.0, "micro-USB ESP32\nx = +%.1f" % mi["x"], color="#b00020", fontsize=10, ha="center", va="top", fontweight="bold")
ax.text(-OX - 1.5, us["y"], "USB-C\npowerbank", color="#b00020", fontsize=10, ha="right", fontweight="bold", va="center")
ax.text(-OX - 1.5, gl["y"], "gland\nkabel", color="#b00020", fontsize=10, ha="right", fontweight="bold", va="center")

# penahan
for k, pcx in enumerate(P["pieces"]):
    x0, x1 = pcx["x"]; y0, y1 = pcx["y"]
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=PC[k], ec="k", lw=1.3, alpha=0.88, zorder=8))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, NAME[k], color="white", fontsize=20, fontweight="bold", ha="center", va="center", zorder=10)
    for fx in pcx["feet"]:
        sy = (pcx["y"][0] + pcx["y"][1]) / 2 + (-0.0)
        sy = 25.25 * pcx["side"]
        ax.add_patch(Circle((fx, sy), 1.6, fc="white", ec="k", lw=1.2, zorder=11))
        ax.plot([fx - 1.6, fx + 1.6], [sy, sy], "k", lw=0.7, zorder=12); ax.plot([fx, fx], [sy - 1.6, sy + 1.6], "k", lw=0.7, zorder=12)
    # dimensi dari ujung dinding
    side = pcx["side"]
    yd = (OY + 1.5 if side > 0 else -OY - 1.5)
    ydim = (y1 + 11.0 if side > 0 else y0 - 11.0)
# dimensi: Atas
def dim(xa, xb, y, txt, col):
    ax.add_patch(FancyArrowPatch((xa, y), (xb, y), arrowstyle="<->", color=col, lw=1.2, mutation_scale=10, zorder=12))
    ax.text((xa + xb) / 2, y, txt, color=col, fontsize=10, ha="center", va="center", fontweight="bold", zorder=13, bbox=dict(fc="white", ec="none", pad=0.8))
dim(-CX, -31.0, 19.0, "18,5", PC[0]); dim(-31, 31, 19.0, "62", PC[0]); dim(31.0, CX, 19.0, "18,5", PC[0])
dim(-CX, -35.0, -19.0, "14,5", PC[1]); dim(-35, -11, -19.0, "24", PC[1]); dim(-11, 18, -19.0, "29", "#555"); dim(18, 28, -19.0, "10", PC[2]); dim(28, CX, -19.0, "21,5", "#555")

# sumbu / arah
ax.text(-OX - 9, -26, "KANAN\n(-X)", fontsize=11, ha="center", va="center", color="#333", fontweight="bold")
ax.text(OX + 9, -26, "KIRI\n(+X)", fontsize=11, ha="center", va="center", color="#333", fontweight="bold")
ax.text(0, OY + 9.5, "ATAS (+Y) : sisi jack AD8232 dan saklar", fontsize=12, ha="center", color="#333", fontweight="bold")
ax.text(0, -OY - 11.0, "BAWAH (-Y) : sisi micro-USB ESP32", fontsize=12, ha="center", color="#333", fontweight="bold")
ax.text(-OX - 1.0, -OY + 1.0, "", fontsize=1)

# keterangan bawah: tabel
rows = [("1", "Strip PANJANG (62 mm)", "dinding ATAS", "x = -31 ... +31", "sekrup 2 buah: x = -23 dan +23 (y = +25,25)", "18,5 mm dari tiap ujung rongga, di tengah"),
        ("2", "Strip SEDANG (24 mm)", "dinding BAWAH, sisi KANAN", "x = -35 ... -11", "sekrup 1 buah: x = -23 (y = -25,25)", "14,5 mm dari ujung kanan rongga"),
        ("3", "Blok KECIL (10 mm)", "dinding BAWAH, sisi KIRI", "x = +18 ... +28", "sekrup 1 buah: x = +23 (y = -25,25)", "tepat di kiri micro-USB, 21,5 mm dari ujung kiri")]
fig.text(0.04, 0.315, "Tabel peletakan (koordinat dari titik tengah 4 baut PCB; X ke KIRI positif)", fontsize=13, fontweight="bold")
y = 0.285
hdr = ("No", "Bagian", "Dinding", "Rentang", "Sekrup di dalam bagian", "Catatan")
cx = [0.04, 0.075, 0.23, 0.39, 0.50, 0.75]
for c, h in zip(cx, hdr): fig.text(c, y, h, fontsize=10.5, fontweight="bold")
for r, col in zip(rows, PC):
    y -= 0.032
    fig.text(cx[0], y, r[0], fontsize=15, fontweight="bold", color=col)
    for c, v in zip(cx[1:], r[1:]): fig.text(c, y, v, fontsize=10.5)

y -= 0.050
fig.text(0.04, y, "Aturan pemasangan", fontsize=13, fontweight="bold")
rules = ["Muka yang ditempel epoxy = muka yang menghadap DINDING (muka rata luar bagian dengan jarak desain 0,3 mm ke dinding). Muka lain tidak boleh kena epoxy.",
         "Kaki penahan (turun sampai plate) masuk ke celah rim plate; batang penahan melintas di atas rim, bukan menumpang di atasnya (celah 0,40 mm).",
         "Strip PANJANG (No. 1) HARUS di sisi jack AD8232 / saklar (+Y). Bila plate terbalik 180 derajat, strip 62 mm menabrak kaki soket ESP32 (x = 15,6) dan tumpukan tidak masuk.",
         "Jarak ke bukaan: jack 7,1 mm, saklar 11,1 mm, micro-USB 8,6 mm, USB-C dan gland lebih dari 15 mm. Tinggi penahan 4,3 mm dari tepi belakang; bukaan paling rendah mulai 7,4 mm: tidak ada yang tertutup.",
         "Ketiga bagian wajib dipakai semua: bagian 2 dan 3 masing-masing satu-satunya jangkar sekrup di dinding Bawah; tanpa salah satunya ada sekrup tanpa pegangan."]
for r in rules:
    y -= 0.026
    fig.text(0.045, y, "-  " + r, fontsize=10.2)

fig.savefig(OUTF, dpi=170)
print("saved", OUTF)
