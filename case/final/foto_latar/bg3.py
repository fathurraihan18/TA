"""Komposit akhir: latar polos, benda utuh.
python bg3.py foto1|foto2 [nilai_latar_putih] [nilai_latar_abu]
Keluaran: fotoN_putih.png, fotoN_abu.png (resolusi asli), plus peta bantu fotoN_s.png, fotoN_alpha.png
"""
import cv2, numpy as np, sys

n = sys.argv[1]
BGW = float(sys.argv[2]) if len(sys.argv) > 2 else 246
BGG = float(sys.argv[3]) if len(sys.argv) > 3 else 196
GAMMA = 1.3
DEAD = 0.05

im8 = cv2.imread(n + ".jpg")
H, W = im8.shape[:2]
im = im8.astype(np.float32)
big = (cv2.imread(n + "_big.png", 0) > 0).astype(np.uint8)
R = np.load(n + "_R.npy").astype(np.float32)
ker = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ---------- 1. garis sambungan ubin (dibagi profilnya, jadi kabel yang melintas tetap utuh) ----------
near_big = cv2.dilate(big, ker(14)) > 0
Rs = cv2.GaussianBlur(R, (0, 0), 0.8)
if n == "foto1":
    ax_len, slope, base = H, 0.2014, 925.0          # x = base + slope * y
    pred = lambda tt: base + slope * tt
    sample = lambda tt, o: (int(round(pred(tt) + o)), int(tt))
else:
    ax_len, slope, base = W, -0.0571, 963.0         # y = base + slope * x
    pred = lambda tt: base + slope * tt
    sample = lambda tt, o: (int(tt), int(round(pred(tt) + o)))
ts, offs_found = [], []
for tt in range(0, ax_len, 3):
    vals = []
    for o in range(-6, 7):
        x_, y_ = sample(tt, o)
        if not (0 <= x_ < W and 0 <= y_ < H): vals = None; break
        vals.append(Rs[y_, x_])
    if vals is None: continue
    vals = np.array(vals)
    fl = []
    for o in (-11, -10, 10, 11):
        x_, y_ = sample(tt, o)
        if 0 <= x_ < W and 0 <= y_ < H: fl.append(Rs[y_, x_])
    if len(fl) < 3 or not (0.9 < np.median(fl) < 1.1): continue
    xs_, ys_ = sample(tt, 0)
    if near_big[min(max(ys_, 0), H - 1), min(max(xs_, 0), W - 1)]: continue
    i = int(vals.argmin())
    if vals[i] > 0.88 or i in (0, 12): continue
    # titik terdalam dengan interpolasi parabola
    sub = 0.0
    if 0 < i < 12:
        a_, b_, c_ = vals[i - 1], vals[i], vals[i + 1]
        den_ = a_ - 2 * b_ + c_
        if abs(den_) > 1e-6: sub = 0.5 * (a_ - c_) / den_
    ts.append(tt); offs_found.append(i - 6 + sub)
ts = np.array(ts, np.float32); offs_found = np.array(offs_found, np.float32)
# mediannya digeser menjadi kurva halus (polinom derajat 3, buang pencilan)
keep_ = np.ones(len(ts), bool)
for _ in range(3):
    cf = np.polyfit(ts[keep_], offs_found[keep_], 3)
    res_ = offs_found - np.polyval(cf, ts)
    keep_ = np.abs(res_) < max(1.2, 2.2 * np.std(res_[keep_]))
off_curve = np.polyval(cf, np.arange(ax_len).astype(np.float32)).astype(np.float32)
print(n, "titik sambungan", int(keep_.sum()), "dari", len(ts), "geser rata2", float(off_curve.mean()).__round__(2), "rentang", float(off_curve.min()).__round__(2), float(off_curve.max()).__round__(2))
if n == "foto1":
    d = (xx - (base + slope * yy) - off_curve[np.clip(yy.astype(int), 0, H - 1)]) * np.cos(np.arctan(slope))
    t = yy
else:
    d = (yy - (base + slope * xx) - off_curve[np.clip(xx.astype(int), 0, W - 1)]) * np.cos(np.arctan(slope))
    t = xx
band = 12
prof = []
offs = np.arange(-band, band + 1)
for o in offs:
    sel = (np.abs(d - o) < 0.5) & ~near_big
    flank = (np.abs(np.abs(d) - 10.5) < 1.5) & ~near_big
    vals = []
    tb = np.linspace(0, ax_len - 1, 64).astype(int)
    for tc in tb:
        s_ = sel & (np.abs(t - tc) < 6)
        f_ = flank & (np.abs(t - tc) < 6)
        if s_.sum() < 6 or f_.sum() < 12: continue
        fl = np.median(Rs[f_])
        if fl < 0.9 or fl > 1.1: continue
        vals.append(np.median(Rs[s_]) / fl)
    prof.append(np.median(vals) if vals else 1.0)
prof = np.array(prof)
prof = cv2.GaussianBlur(prof.reshape(-1, 1).astype(np.float32), (1, 0), 0.8).ravel()
print(n, "profil sambungan min", prof.min().round(3), "di jarak", offs[prof.argmin()])
shape = np.clip((1 - prof) / max(1 - prof.min(), 1e-3), 0, 1)           # bentuk lintang, puncak = 1
# kedalaman garis berubah sepanjang garis: ukur di tempat yang tidak ada kabel, isi celahnya
amp_t, amp_v = [], []
for tc in range(0, ax_len, 2):
    core = (np.abs(d) < 0.8) & (np.abs(t - tc) < 3) & ~near_big
    fl = (np.abs(np.abs(d) - 10.5) < 1.5) & (np.abs(t - tc) < 5) & ~near_big
    if core.sum() < 4 or fl.sum() < 10: continue
    f_ = np.median(Rs[fl])
    if not (0.9 < f_ < 1.1): continue
    c_ = np.median(Rs[core])
    if c_ < 0.45 or c_ > 0.97: continue
    amp_t.append(tc); amp_v.append(1 - c_ / f_)
amp_t = np.array(amp_t, np.float32); amp_v = np.array(amp_v, np.float32)
k_ = 21
med = np.array([np.median(amp_v[max(0, i - k_ // 2):i + k_ // 2 + 1]) for i in range(len(amp_v))], np.float32)
amp_line = np.interp(np.arange(ax_len), amp_t, med).astype(np.float32)
tidx = np.clip((yy if n == "foto1" else xx).astype(int), 0, ax_len - 1)
amp_img = amp_line[tidx]
print(n, "kedalaman garis", float(med.min()).__round__(3), float(np.median(med)).__round__(3), float(med.max()).__round__(3), "sampel", len(med))
pimg = 1 - amp_img * np.interp(d, offs, shape, left=0.0, right=0.0).astype(np.float32) * smooth(band - np.abs(d), 0, 4)
Rc = R / np.maximum(pimg, 0.3)

# garis yang tidak dilewati kabel: isi garis dengan interpolasi linear dari kedua sisinya (menghapus sisa aliasing)
Z, F = 5.5, 8
Rint = Rc.copy()
wz_img = np.zeros((H, W), np.float32)
nvalid = 0
for tt in range(ax_len):
    c0 = pred(tt) + off_curve[tt]
    us = np.arange(int(np.floor(c0 - F - 3)), int(np.ceil(c0 + F + 3)) + 1)
    if n == "foto1":
        if us.min() < 0 or us.max() >= W: continue
        line = Rs[tt, us]; big_l = big[tt, us]
    else:
        if us.min() < 0 or us.max() >= H: continue
        line = Rs[us, tt]; big_l = big[us, tt]
    if big_l.any(): continue
    rel = us - c0
    lo = line[(rel >= -F - 2) & (rel <= -F)]; hi = line[(rel >= F) & (rel <= F + 2)]
    mid = line[np.abs(rel) <= Z]
    if lo.size < 2 or hi.size < 2: continue
    if not (0.9 < lo.mean() < 1.12 and 0.9 < hi.mean() < 1.12): continue
    if abs(lo.mean() - hi.mean()) > 0.10 or mid.min() < 0.40: continue
    if np.sum(line[np.abs(rel) <= F] < 0.88) > 6: continue          # lebih lebar dari garis sambungan: ada kabel
    nvalid += 1
    uu = np.arange(int(np.floor(c0 - Z - 2)), int(np.ceil(c0 + Z + 2)) + 1)
    rr = uu - c0
    lin = np.interp(rr, [-F - 1, F + 1], [lo.mean(), hi.mean()])
    wz = 1 - smooth(np.abs(rr), Z - 1.5, Z + 1.0)
    if n == "foto1":
        base_v = Rc[tt, uu]; Rint[tt, uu] = base_v * (1 - wz) + lin * wz; wz_img[tt, uu] = wz
    else:
        base_v = Rc[uu, tt]; Rint[uu, tt] = base_v * (1 - wz) + lin * wz; wz_img[uu, tt] = wz
print(n, "garis bersih tanpa kabel", nvalid, "dari", ax_len)
Rc = Rint

# ---------- 2. alfa benda besar (hasil GrabCut), dihaluskan dan dikupas satu piksel ----------
a_big = cv2.erode(big, ker(1)).astype(np.float32)
a_big = cv2.GaussianBlur(a_big, (0, 0), 0.9)
a_big = np.clip((a_big - 0.08) / 0.84, 0, 1)

# warna benda: dekontaminasi tepi (ganti warna tepi dengan warna dari dalam benda)
inner = (cv2.erode(big, ker(2)) > 0).astype(np.float32)
num = cv2.GaussianBlur(im * inner[..., None], (0, 0), 2.5)
den = cv2.GaussianBlur(inner, (0, 0), 2.5)[..., None]
inward = num / np.maximum(den, 1e-3)
edge = np.clip(1 - inner, 0, 1)[..., None] * (den > 0.02)
Fbig = np.where(edge > 0, inward, im)

# ---------- 3. kabel putih PPG: alfa dari koridor sepanjang jalurnya ----------
CABLE_W = {
    "foto1": [(500, 425), (470, 410), (430, 398), (390, 390), (340, 385), (290, 388), (240, 395), (200, 408), (160, 430), (125, 462), (95, 500),
              (70, 540), (50, 580), (42, 620), (48, 655), (75, 683), (115, 695), (160, 698), (210, 692), (255, 680), (300, 662), (335, 642), (368, 628)],
    "foto2": [(208, 520), (212, 505), (224, 470), (240, 430), (258, 390), (272, 340), (274, 290), (265, 248), (242, 222), (205, 198), (170, 186),
              (130, 181), (95, 188), (60, 203), (30, 225), (12, 255), (6, 295), (8, 335), (22, 375), (40, 410), (55, 438)],
}
cor = np.zeros((H, W), np.uint8)
cv2.polylines(cor, [np.array(CABLE_W[n], np.int32)], False, 255, 20)
cor = cor > 0
aw_raw = smooth(Rc, 1.06, 1.22) * cor
aw = aw_raw * (1 - a_big)
# warna kabel putih: ambil dari piksel yang pasti kabel, lalu perluas sedikit ke tepi
sure_w = (aw_raw > 0.85).astype(np.float32)
numw = cv2.GaussianBlur(im * sure_w[..., None], (0, 0), 2.0)
denw = cv2.GaussianBlur(sure_w, (0, 0), 2.0)[..., None]
Fw = np.where(denw > 0.03, numw / np.maximum(denw, 1e-3), im)
Fw = np.where(sure_w[..., None] > 0, im, Fw)

# ---------- 4. bayangan dan kabel gelap lewat rasio ----------
s_raw = np.clip(1 - Rc, 0, 1)
s = np.clip((s_raw - DEAD) / (1 - DEAD), 0, 1)
# sisa tipis garis sambungan: dibuang dengan ambang kecil, kabel yang jauh lebih gelap tidak tersentuh
seam_zone = smooth(5.0 - np.abs(d), 0, 2.5)
s = np.clip(s - 0.06 * seam_zone, 0, 1)
# bercak lantai, retakan pendek, dan noda yang berdiri sendiri dibuang;
# kabel dan bayangan benda (inti cukup gelap) tetap utuh bersama tepi lembutnya
s_pre = s.copy()
strong0 = (s > 0.10).astype(np.uint8)
nl, lb, st, _ = cv2.connectedComponentsWithStats(strong0, 8)
mx = np.zeros(nl, np.float32)
np.maximum.at(mx, lb.ravel(), s.ravel())
keepc = (mx >= 0.22) & (st[:, cv2.CC_STAT_AREA] >= 30)
keepc[0] = False
strong = keepc[lb].astype(np.uint8)
dist = cv2.distanceTransform(1 - strong, cv2.DIST_L2, 5)
w = 1 - smooth(dist, 5, 10)
s = s * w
# bayangan lebar milik benda besar: halus dan lembut, jadi dipertahankan utuh (bukan bercak lantai)
cab = ((Rc < 0.74) & (big == 0)).astype(np.uint8)
cab = cv2.morphologyEx(cab, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
cab = cv2.GaussianBlur(cv2.dilate(cab, ker(3)).astype(np.float32), (0, 0), 1.0)      # inti kabel, dikecualikan dari bayangan lebar
s_sm = np.clip(cv2.GaussianBlur(s_raw, (0, 0), 3.0) - 0.02, 0, 1)
near_obj = cv2.GaussianBlur(cv2.dilate(big, ker(45)).astype(np.float32), (0, 0), 6)
s_b = s_sm * near_obj * (1 - np.clip(cab * 1.4, 0, 1))
wk = (s_b > 0.02).astype(np.uint8)
nl2, lb2, st2, _ = cv2.connectedComponentsWithStats(wk, 8)
mx2 = np.zeros(nl2, np.float32)
np.maximum.at(mx2, lb2.ravel(), s_b.ravel())
kp2 = (mx2 >= {"foto1": 0.05, "foto2": 0.10}[n]) & (st2[:, cv2.CC_STAT_AREA] >= 300)
kp2[0] = False
kept2 = cv2.GaussianBlur(cv2.dilate(kp2[lb2].astype(np.uint8), ker(2)).astype(np.float32), (0, 0), 1.5)
s_b = s_b * np.clip(kept2 * 1.5, 0, 1)
# noda lantai yang sudah ada sebelum benda ditaruh (bukan bayangan): dikecualikan dengan elips lembut
STAIN = {"foto1": [(915, 568, 100, 40, -12)], "foto2": []}
exc = np.zeros((H, W), np.uint8)
for (cx_, cy_, ax_, ay_, an_) in STAIN[n]:
    cv2.ellipse(exc, (cx_, cy_), (ax_, ay_), an_, 0, 360, 255, -1)
exc = cv2.GaussianBlur(exc.astype(np.float32) / 255, (0, 0), 6)
s_b = s_b * (1 - np.clip(exc * 1.4, 0, 1))
s = s * (1 - np.clip(exc * 1.4, 0, 1) * (1 - np.clip(cab * 1.4, 0, 1)))
s = np.maximum(s, s_b)
cv2.imwrite(n + "_s.png", np.clip(s * 255, 0, 255).astype(np.uint8))

shade = np.power(1 - s, GAMMA)

# derau mirip foto asli: ukur dari lantai datar
hp = im[..., 1] - cv2.GaussianBlur(im[..., 1], (0, 0), 1.5)
flat = (cv2.dilate(((Rc < 0.9) | (big > 0)).astype(np.uint8), ker(20)) == 0) & (np.abs(Rc - 1) < 0.02)
sig = float(np.std(hp[flat])) if flat.sum() > 500 else 1.0
print(n, "derau lantai", round(sig, 2))
rng = np.random.default_rng(7)
noise = cv2.GaussianBlur(rng.normal(0, 1, (H, W, 3)).astype(np.float32), (0, 0), 0.7)
noise *= sig / max(noise.std(), 1e-3)


def compose(bgval, tag):
    # sedikit gradasi cahaya agar tidak terlalu rata (di bawah 1,5 persen)
    cx, cy = W * 0.5, H * 0.45
    vig = 1 - 0.012 * (((xx - cx) / W) ** 2 + ((yy - cy) / H) ** 2) * 4
    bgl = (bgval * vig)[..., None] * shade[..., None] * np.ones((1, 1, 3), np.float32)
    bgl = bgl + noise * 0.8
    out = bgl * (1 - aw[..., None]) + Fw * aw[..., None]
    out = out * (1 - a_big[..., None]) + Fbig * a_big[..., None]
    out = np.clip(out, 0, 255).astype(np.uint8)
    cv2.imwrite(n + "_" + tag + ".png", out)
    return out


cv2.imwrite(n + "_alpha.png", np.clip(np.maximum(a_big, aw) * 255, 0, 255).astype(np.uint8))
compose(BGW, "putih")
compose(BGG, "abu")
