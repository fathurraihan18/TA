"""Ganti latar foto menjadi polos tanpa menghapus benda: matte benda besar (GrabCut), kabel dan bayangan lewat rasio terhadap model lantai.
python bg2.py foto1|foto2
"""
import cv2, numpy as np, sys, json
from bg1 import floor_model

n = sys.argv[1]
im = cv2.imread(n + ".jpg")
H, W = im.shape[:2]
lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)


def rough_mask(spec):
    m = np.zeros((H, W), np.uint8)
    for s in spec:
        k = s[0]
        if k == "r": cv2.rectangle(m, (s[1], s[2]), (s[3], s[4]), 255, -1)
        elif k == "e": cv2.ellipse(m, (s[1], s[2]), (s[3], s[4]), s[5] if len(s) > 5 else 0, 0, 360, 255, -1)
        elif k == "l": cv2.line(m, (s[1], s[2]), (s[3], s[4]), 255, s[5])
        elif k == "p": cv2.fillPoly(m, [np.array(s[1], np.int32)], 255)
    return m


SPEC = {
    "foto1": [("r", 530, 312, 800, 490), ("r", 518, 355, 832, 492), ("r", 498, 402, 546, 462),               # perangkat
              ("r", 366, 560, 556, 652),                                                                        # klip
              ("e", 958, 482, 74, 68), ("l", 908, 422, 968, 480, 30),                                           # elektroda merah
              ("e", 1073, 418, 74, 54, -8), ("l", 1060, 350, 1076, 418, 26),                                    # hijau
              ("e", 1152, 346, 78, 56, -12), ("l", 1092, 316, 1172, 340, 30)],                                  # kuning
    "foto2": [("r", 165, 538, 300, 768), ("r", 170, 760, 297, 797), ("r", 193, 517, 226, 548), ("r", 298, 596, 327, 648), ("r", 297, 646, 308, 678),
              ("r", 28, 438, 92, 580),
              ("e", 177, 898, 64, 62), ("l", 160, 905, 234, 862, 30),
              ("e", 232, 1002, 60, 60), ("l", 218, 1002, 296, 1000, 24),
              ("e", 306, 1088, 56, 64), ("l", 303, 1086, 336, 1040, 26)],
}

rough = rough_mask(SPEC[n])
# B awal untuk prior (benda terang atau berwarna dibanding lantai)
B0 = floor_model(im)
B0lab = cv2.cvtColor(np.clip(B0, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
dL = lab[..., 0] - B0lab[..., 0]
dC = np.hypot(lab[..., 1] - B0lab[..., 1], lab[..., 2] - B0lab[..., 2])
prior_fg = (dL > 12) | (dC > 14)

ker = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
sure = cv2.erode(rough, ker(9))
near = cv2.dilate(rough, ker(14))
gc = np.full((H, W), cv2.GC_BGD, np.uint8)
band = (near > 0)
gc[band] = cv2.GC_PR_BGD
gc[band & (rough > 0) & prior_fg] = cv2.GC_PR_FGD
gc[(rough > 0) & ~prior_fg] = cv2.GC_PR_FGD
gc[sure > 0] = cv2.GC_FGD
bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(im, gc, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
big = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8) * 255
# bersihkan: ambil komponen yang menyentuh kerangka kasar, isi lubang kecil
nl, lb, st, _ = cv2.connectedComponentsWithStats(big, 8)
keep = np.zeros_like(big)
for i in range(1, nl):
    if st[i, cv2.CC_STAT_AREA] >= 120: keep[lb == i] = 255
big = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, ker(2))
cv2.imwrite(n + "_big.png", big)
ov = im.copy(); ov[big > 0] = (0.5 * ov[big > 0] + 0.5 * np.array([0, 0, 255])).astype(np.uint8)
cv2.imwrite(n + "_bigov.png", ov)
print(n, "big area", int((big > 0).sum()))
