import cv2, numpy as np, sys, json

def floor_model(L_or_bgr, k=31, sig=9):
    """lantai tanpa benda tipis: closing menghapus kabel gelap, opening menghapus kabel putih dan bintik pantulan; lalu dihaluskan."""
    out = []
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    img = L_or_bgr
    ch = [img] if img.ndim == 2 else cv2.split(img)
    for c in ch:
        c = cv2.morphologyEx(c, cv2.MORPH_CLOSE, ker)
        c = cv2.morphologyEx(c, cv2.MORPH_OPEN, ker)
        c = cv2.GaussianBlur(c.astype(np.float32), (0, 0), sig)
        out.append(c)
    return out[0] if img.ndim == 2 else cv2.merge(out)

if __name__ == "__main__":
    n = sys.argv[1]
    im = cv2.imread(n + ".jpg")
    B = floor_model(im)
    cv2.imwrite(n + "_B.png", np.clip(B, 0, 255).astype(np.uint8))
    L = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
    BL = cv2.cvtColor(np.clip(B, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    R = L / np.maximum(BL, 1)
    vis = np.clip((R - 0.5) / 1.0 * 255, 0, 255).astype(np.uint8)
    cv2.imwrite(n + "_R.png", vis)
    print(n, "R pct", np.percentile(R, [1, 5, 50, 95, 99]).round(2))
