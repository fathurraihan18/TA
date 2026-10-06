"""Tekstur tampilan LCD 3,5" (480 x 320) sesuai foto layar alat pengguna ("ARMOR - Aritmia Monitoring v1.0"):
judul, badge ECG OK / PPG OK, panel ECG (grid merah halus + sinyal hijau P-QRS-T), panel PPG (biru muda, puncak sistolik + takik dikrotik),
baris status RR / SDNN / Kondisi, serta tiga kotak: DETAK JANTUNG, SpO2 + PR NADI, STATUS IRAMA.
Sinyal digambar bersih (bukan salinan derau foto): HR 74 bpm, RR 811 ms, SpO2 97 %, PR 76 bpm.
python layar_ui.py <berkas_png> [skala_keluaran=4]
"""
import sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "layar_ui.png"
KO = int(sys.argv[2]) if len(sys.argv) > 2 else 4            # skala keluaran (piksel per piksel layar)
SS = 2                                                      # supersampling untuk anti-alias
K = KO * SS
W, H = 480 * K, 320 * K

GREEN = (125, 245, 30)
CYAN = (70, 205, 245)
YELLOW = (252, 228, 55)
SUB = (190, 200, 238)
WHITE = (238, 238, 238)
RED = (240, 60, 70)
GRID_MAJ = (92, 22, 28)
GRID_MIN = (46, 12, 16)
BG = (2, 4, 8)

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
im = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(im)


def font(sz, bold=True):
    return ImageFont.truetype(FB if bold else FR, int(sz * K))


def text(x, y, s, col, sz, bold=True, anchor="lt"):
    d.text((x * K, y * K), s, font=font(sz, bold), fill=col, anchor=anchor)


def rbox(x0, y0, x1, y1, col, r=7, w=2, fill=None):
    d.rounded_rectangle((x0 * K, y0 * K, x1 * K, y1 * K), radius=r * K, outline=col, width=int(w * K), fill=fill)


def gauss(t, mu, sg):
    return np.exp(-0.5 * ((t - mu) / sg) ** 2)


# ---------------------------------------------------------------- baris atas
text(14, 17, "ARMOR", CYAN, 15)
text(66, 21, "Aritmia Monitoring v1.0", WHITE, 8.5, False)
rbox(305, 3, 371, 23, GREEN, 5, 2); text(338, 13, "ECG OK", GREEN, 10, anchor="mm")
rbox(377, 3, 446, 23, CYAN, 5, 2); text(411.5, 13, "PPG OK", CYAN, 10, anchor="mm")

# ---------------------------------------------------------------- panel ECG (grid halus + major)
gx0, gy0, gx1, gy1 = 8, 33, 292, 180
maj_x, maj_y = 37.0, 26.0
x = gx0
while x <= gx1 + 0.01:
    d.line((x * K, gy0 * K, x * K, gy1 * K), fill=GRID_MIN, width=max(1, int(0.5 * K))); x += maj_x / 5
y = gy0
while y <= gy1 + 0.01:
    d.line((gx0 * K, y * K, gx1 * K, y * K), fill=GRID_MIN, width=max(1, int(0.5 * K))); y += maj_y / 5
x = gx0
while x <= gx1 + 0.01:
    d.line((x * K, gy0 * K, x * K, gy1 * K), fill=GRID_MAJ, width=max(1, int(0.9 * K))); x += maj_x
y = gy0
while y <= gy1 + 0.01:
    d.line((gx0 * K, y * K, gx1 * K, y * K), fill=GRID_MAJ, width=max(1, int(0.9 * K))); y += maj_y

HR = 74.0
RR = 60.0 / HR                                              # 0,811 s
PX_PER_S = 44.0                                             # kecepatan sapuan layar (piksel layar per detik)
xs = np.arange(gx0 + 2, gx1 - 1, 0.25)
ts = (xs - xs[0]) / PX_PER_S
base = 126.0; amp = 62.0                                    # baseline dan tinggi gelombang R (piksel layar)
rng = np.random.default_rng(3)
sig = np.zeros_like(ts)
beats = np.arange(0.20, ts[-1] + RR, RR)
for i, b in enumerate(beats):
    a = 1.0 + 0.02 * math.sin(i * 1.7)
    sig += 0.13 * gauss(ts, b - 0.165, 0.034)               # P
    sig += -0.10 * gauss(ts, b - 0.030, 0.0095)             # Q
    sig += 1.00 * a * gauss(ts, b, 0.0105)                  # R
    sig += -0.22 * gauss(ts, b + 0.028, 0.0125)             # S
    sig += 0.30 * gauss(ts, b + 0.255, 0.052)               # T
    sig += 0.015 * gauss(ts, b + 0.43, 0.04)                # U kecil
sig += 0.012 * np.sin(2 * math.pi * 0.25 * ts)              # pergeseran garis dasar halus
sig += rng.normal(0, 0.004, len(ts))
yy = base - sig * amp
pts = list(zip(xs * K, yy * K))
d.line(pts, fill=(50, 120, 15), width=int(3.4 * K), joint="curve")        # halo
d.line(pts, fill=GREEN, width=int(1.9 * K), joint="curve")
text(12, 38, "ECG", (80, 160, 40), 7)

# ---------------------------------------------------------------- panel PPG
px0, px1, ptop, pbot = 10, 290, 192, 285
for gyv in np.linspace(ptop, pbot, 5):
    d.line((px0 * K, gyv * K, px1 * K, gyv * K), fill=(10, 20, 44), width=max(1, int(0.6 * K)))
xs2 = np.arange(px0, px1, 0.25)
ts2 = (xs2 - xs2[0]) / PX_PER_S
ppg = np.zeros_like(ts2)
ptt = 0.21
for i, b in enumerate(np.arange(0.20 + ptt - RR, ts2[-1] + RR, RR)):
    sys_ = 1.00 * gauss(ts2, b + 0.10, 0.075)               # puncak sistolik
    dia = 0.36 * gauss(ts2, b + 0.34, 0.095)                # gelombang diastolik (setelah takik dikrotik)
    rise = 0.0
    ppg += sys_ + dia
ppg = ppg / ppg.max()
ppg += rng.normal(0, 0.003, len(ppg))
y2 = pbot - (0.07 + 0.88 * ppg) * (pbot - ptop)
pts2 = list(zip(xs2 * K, y2 * K))
d.line(pts2, fill=(25, 85, 120), width=int(3.4 * K), joint="curve")
d.line(pts2, fill=CYAN, width=int(1.9 * K), joint="curve")
text(12, 190, "PPG", (40, 130, 170), 7)

# ---------------------------------------------------------------- baris status bawah
text(8, 298, "RR: 811 ms  |  SDNN: 14.4 ms  |  Kondisi: Irama Teratur  |  ARMOR Monitoring", GREEN, 7.6, anchor="lm")

# ---------------------------------------------------------------- kotak DETAK JANTUNG
rbox(294, 26, 452, 97, GREEN, 7, 2)
text(300, 31, "DETAK JANTUNG", GREEN, 8)
hx, hy = 437, 38
heart = [((hx - 6.5) * K, (hy - 0.5) * K), ((hx - 5) * K, (hy - 4) * K), ((hx - 2) * K, (hy - 5.5) * K), (hx * K, (hy - 2.5) * K),
         ((hx + 2) * K, (hy - 5.5) * K), ((hx + 5) * K, (hy - 4) * K), ((hx + 6.5) * K, (hy - 0.5) * K), (hx * K, (hy + 7) * K), ((hx - 6.5) * K, (hy - 0.5) * K)]
d.line(heart, fill=RED, width=int(1.6 * K), joint="curve")
text(312, 43, "74", GREEN, 28)
text(372, 66, "BPM", GREEN, 12, anchor="mm")
text(300, 80, "Normal (60-100)", WHITE, 8.5, False)

# ---------------------------------------------------------------- kotak SpO2 + PR NADI
rbox(294, 100, 452, 164, CYAN, 7, 2)
text(303, 105, "SpO2", CYAN, 8)
text(308, 119, "97", CYAN, 27)
text(354, 138, "%", CYAN, 11, anchor="mm")
text(380, 105, "PR NADI", YELLOW, 8)
text(386, 119, "76", YELLOW, 27)
text(430, 131, "bpm", YELLOW, 8)
text(303, 152, "Saturasi O2", SUB, 8.5, False)
text(380, 152, "Denyut Nadi", SUB, 8.5, False)

# ---------------------------------------------------------------- kotak STATUS IRAMA
rbox(294, 170, 456, 290, CYAN, 7, 2)
text(302, 176, "STATUS IRAMA", GREEN, 8)
rbox(302, 188, 449, 228, (90, 215, 70), 6, 1.5, fill=(52, 150, 40))
text(375.5, 208.5, "NORMAL", (205, 255, 170), 27, anchor="mm")
text(375, 246, "Irama Teratur", WHITE, 11, anchor="mm")
text(375, 264, "Normal (60-100 BPM)", SUB, 8, False, anchor="mm")

im = im.resize((480 * KO, 320 * KO), Image.LANCZOS)
im.save(OUT)
print("saved", OUT, im.size)
