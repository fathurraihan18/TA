import cv2, numpy as np, sys, re
sys.argv = ["x", sys.argv[1]]
n = sys.argv[1]
src = open("bg3.py").read()
CW = eval(re.search(r"CABLE_W = (\{.*?\n\})", src, re.S).group(1))
o = cv2.imread(n + ".jpg"); big = cv2.imread(n + "_big.png", 0) > 0
R = np.load(n + "_R.npy"); Rs = cv2.GaussianBlur(R, (0, 0), 0.8)
ker = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*r+1, 2*r+1))
for tag, bgv in (("putih", 246), ("abu", 196)):
    out = cv2.imread(f"{n}_{tag}.png"); g = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY).astype(np.float32)
    # 1. benda besar: piksel dalam sama dengan aslinya
    inner = cv2.erode(big.astype(np.uint8), ker(3)) > 0
    diff = np.abs(out.astype(np.float32) - o.astype(np.float32)).max(axis=2)
    print(n, tag, "benda besar: piksel dalam sama persis", f"{(diff[inner] < 1.5).mean()*100:.2f}%", "selisih maks", diff[inner].max())
    # 2. kabel gelap: inti kabel di aslinya (R<0.7) di luar benda besar
    cor = np.zeros(big.shape, np.uint8); cv2.polylines(cor, [np.array(CW[n], np.int32)], False, 255, 26)
    core = (Rs < 0.70) & ~cv2.dilate(big.astype(np.uint8), ker(3)).astype(bool) & ~(cor > 0)
    nl, lb, st, _ = cv2.connectedComponentsWithStats(core.astype(np.uint8), 8)
    tot = 0; kept = 0; lostcomp = []
    for i in range(1, nl):
        if st[i, cv2.CC_STAT_AREA] < 12: continue
        m = lb == i
        ok = (g[m] < bgv * 0.88).mean()
        tot += m.sum(); kept += (g[m] < bgv * 0.88).sum()
        if ok < 0.6: lostcomp.append((int(st[i,0]), int(st[i,1]), int(st[i,4]), round(float(ok),2)))
    print(n, tag, "inti kabel gelap tampak di hasil:", f"{kept/tot*100:.1f}%", "komponen kurang:", lostcomp[:12])
    # 3. kabel putih: titik sepanjang jalur
    pts = np.array(CW[n], np.float32); samp = []
    for a, b in zip(pts[:-1], pts[1:]):
        for t in np.linspace(0, 1, 8, endpoint=False): samp.append(a + (b - a) * t)
    hit = 0
    for (x, y) in samp:
        x, y = int(x), int(y)
        w = g[max(y-8,0):y+9, max(x-8,0):x+9]
        if (bgv - w.min()) > 10: hit += 1
    print(n, tag, "kabel putih: titik jalur yang terlihat", f"{hit}/{len(samp)}")
