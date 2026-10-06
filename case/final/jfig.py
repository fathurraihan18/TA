"""Pustaka gambar jurnal: satu gambar per berkas, ukuran akhir nyata (1 kolom 88 mm, 2 kolom 180 mm), huruf Liberation Sans, teks minimal 8 pt pada ukuran akhir.
Sumbu gambar bersatuan mm kertas (x ke kanan, y ke atas). Teks Inggris. Keluaran: PNG 600 dpi + PDF (+ TIFF bila diminta).
"""
import os, json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Ellipse, Polygon
import matplotlib.patheffects as pe
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
                     "axes.linewidth": 0.6, "lines.linewidth": 0.7})
MM = 1 / 25.4
T_MAIN = 9.0          # teks utama (pt)
T_SMALL = 8.0         # teks terkecil yang dipakai (pt)
T_PANEL = 11.0        # huruf panel (a), (b)
INK = "#1a1a1a"
GREY = "#555555"
HALO = [pe.withStroke(linewidth=2.4, foreground="white")]


class Fig:
    def __init__(self, w_mm, h_mm):
        self.w, self.h = w_mm, h_mm
        self.fig = plt.figure(figsize=(w_mm * MM, h_mm * MM))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, w_mm); self.ax.set_ylim(0, h_mm); self.ax.set_aspect("equal"); self.ax.axis("off")

    # ---------------------------------------------------------------- gambar raster
    def image(self, src, box, crop=True, pad=6, bg=None, align="center"):
        """pasang gambar (path atau array RGBA) agar muat di box=(x0,y0,w,h) mm; kembalikan (fungsi px->mm, (x0,y0,w,h) terpakai, skala mm/px, kotak potong)."""
        im = Image.open(src).convert("RGBA") if isinstance(src, str) else Image.fromarray(src)
        cb = (0, 0, im.width, im.height)
        if crop:
            a = np.asarray(im)[..., 3]
            ys, xs = np.where(a > 8)
            cb = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, im.width), min(ys.max() + pad, im.height))
            im = im.crop(cb)
        if bg is not None:
            b = Image.new("RGBA", im.size, bg); b.alpha_composite(im); im = b
        bx, by, bw, bh = box
        k = min(bw / im.width, bh / im.height)
        w, h = im.width * k, im.height * k
        x0 = bx + (bw - w) / 2 if align == "center" else bx
        y0 = by + (bh - h) / 2
        self.ax.imshow(np.asarray(im), extent=(x0, x0 + w, y0, y0 + h), origin="upper", zorder=2, interpolation="lanczos")
        f = lambda px, py: (x0 + (px - cb[0]) * k, y0 + h - (py - cb[1]) * k)
        return f, (x0, y0, w, h), k, cb

    # ---------------------------------------------------------------- teks dan penanda
    def text(self, x, y, s, size=T_MAIN, weight="normal", ha="left", va="center", color=INK, halo=False, **kw):
        t = self.ax.text(x, y, s, fontsize=size, fontweight=weight, ha=ha, va=va, color=color, zorder=kw.pop("zorder", 20), **kw)
        if halo: t.set_path_effects(HALO)
        return t

    def panel(self, x, y, s):
        self.text(x, y, s, size=T_PANEL, weight="bold", ha="left", va="top")

    def balloon(self, xy, n, r=2.9, size=T_MAIN, z=25):
        self.ax.add_patch(Circle(xy, r, fc="white", ec=INK, lw=0.8, zorder=z))
        self.ax.text(xy[0], xy[1] - 0.05, str(n), fontsize=size, fontweight="bold", ha="center", va="center", zorder=z + 1, color=INK)

    def leader(self, p, q, lw=0.6):
        self.ax.plot([p[0], q[0]], [p[1], q[1]], color=INK, lw=lw, zorder=22, solid_capstyle="round")
        self.ax.plot([p[0]], [p[1]], marker="o", ms=2.6, color=INK, zorder=23)

    def callout(self, p, q, s, ha="left", size=T_MAIN, bold=False, color=INK, box=True):
        """garis penunjuk dari titik p ke teks di q."""
        self.leader(p, q)
        t = self.ax.text(q[0] + (0.8 if ha == "left" else -0.8), q[1], s, fontsize=size, ha=ha, va="center", color=color, fontweight="bold" if bold else "normal", zorder=24)
        if box: t.set_bbox(dict(fc="white", ec="none", pad=0.8, alpha=0.88))
        return t

    def numbered_callouts(self, anchors, bbox, numbers, margin=5.5, min_gap=7.4):
        """balon bernomor di kiri/kanan gambar dengan garis lurus ke titik anchor."""
        x0, y0, w, h = bbox
        xc = x0 + w / 2
        sides = {"L": [], "R": []}
        for key, num in numbers:
            if key in anchors:
                p = anchors[key]
                sides["L" if p[0] < xc else "R"].append([key, num, p, p[1]])
        for s, lst in sides.items():
            lst.sort(key=lambda t: t[3])
            for i in range(1, len(lst)):
                if lst[i][3] - lst[i - 1][3] < min_gap: lst[i][3] = lst[i - 1][3] + min_gap
            xb = x0 - margin if s == "L" else x0 + w + margin
            for key, num, p, yb in lst:
                self.ax.plot([p[0], xb], [p[1], yb], color=INK, lw=0.6, zorder=22)
                self.ax.plot([p[0]], [p[1]], marker="o", ms=2.6, color=INK, zorder=23)
                self.balloon((xb, yb), num)

    def legend_list(self, x, y_top, items, pitch=6.8, size=T_MAIN, r=2.7):
        """daftar bernomor: [(nomor, teks)]; y_top = pusat baris pertama."""
        for i, (n, s) in enumerate(items):
            y = y_top - i * pitch
            self.balloon((x + r, y), n, r=r, size=size - 0.5)
            self.ax.text(x + 2 * r + 2.0, y - 0.05, s, fontsize=size, ha="left", va="center", color=INK, zorder=26)

    def swatch(self, x, y, color, s, size=T_MAIN, w=7.0, h=4.6, ec=INK, txtcolor=None):
        self.ax.add_patch(Rectangle((x, y - h / 2), w, h, fc=color, ec=ec, lw=0.6, zorder=20))
        self.ax.text(x + w + 2.2, y, s, fontsize=size, ha="left", va="center", color=INK, zorder=21)

    # ---------------------------------------------------------------- dimensi
    def _arrow(self, p0, p1, style="<|-|>"):
        self.ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle=style, lw=0.6, color=INK, mutation_scale=7, shrinkA=0, shrinkB=0), zorder=22)

    def _line(self, p0, p1, lw=0.5, c=INK, z=21):
        self.ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=c, lw=lw, zorder=z, solid_capstyle="butt")

    def hdim(self, x0, x1, yl, yf0, yf1, text, size=T_MAIN):
        s = 1 if yl > yf0 else -1
        self._line((x0, yf0 + s * 0.8), (x0, yl + s * 1.3)); self._line((x1, yf1 + s * 0.8), (x1, yl + s * 1.3))
        xa, xb = min(x0, x1), max(x0, x1)
        self._arrow((xa, yl), (xb, yl))
        t = self.ax.text((xa + xb) / 2, yl + (0.9 if s > 0 else -0.9), text, fontsize=size, ha="center", va="bottom" if s > 0 else "top", zorder=24, color=INK)
        t.set_bbox(dict(fc="white", ec="none", pad=0.4, alpha=0.85))

    def vdim(self, xl, y0, y1, xf0, xf1, text, side="right", size=T_MAIN):
        s = 1 if xl > xf0 else -1
        self._line((xf0 + s * 0.8, y0), (xl + s * 1.3, y0)); self._line((xf1 + s * 0.8, y1), (xl + s * 1.3, y1))
        ya, yb = min(y0, y1), max(y0, y1)
        self._arrow((xl, ya), (xl, yb))
        t = self.ax.text(xl + (1.0 if side == "right" else -1.0), (ya + yb) / 2, text, fontsize=size, rotation=90, ha="left" if side == "right" else "right", va="center", zorder=24, color=INK)
        t.set_bbox(dict(fc="white", ec="none", pad=0.4, alpha=0.85))

    # ---------------------------------------------------------------- simpan
    def save(self, outdir, name, tiff=False, dpi=600):
        os.makedirs(outdir, exist_ok=True)
        base = os.path.join(outdir, name)
        self.fig.savefig(base + ".pdf")
        self.fig.savefig(base + ".png", dpi=dpi)
        if tiff:
            Image.open(base + ".png").convert("RGB").save(base + ".tif", compression="tiff_lzw", dpi=(dpi, dpi))
        plt.close(self.fig)
        print("saved", name, "%.0f x %.0f mm" % (self.w, self.h))


class Ort:
    """render ortografis dengan info (target, right, up, ortho, px): pemetaan titik model (mm) -> mm kertas pada gambar yang dipasang dengan skala k (mm kertas per mm model)."""
    def __init__(self, png, iv):
        self.png = png
        self.px = iv["px"][0] if isinstance(iv["px"], list) else iv["px"]
        self.py = iv["px"][1] if isinstance(iv["px"], list) else iv["px"]
        self.t = np.array(iv["target"], float); self.r = np.array(iv["right"], float); self.u = np.array(iv["up"], float)
        self.o = iv["ortho"]

    def put(self, F, X, Y, k, pad=10):
        """pusat isi (alfa) di (X, Y) mm; skala k mm kertas per mm model."""
        im = Image.open(self.png).convert("RGBA")
        a = np.asarray(im)[..., 3]
        ys, xs = np.where(a > 6)
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, self.px)
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, self.py)
        self.k = k
        s = k * self.o / self.px
        cxm, cym = (x0 + x1) / 2, (y0 + y1) / 2
        self.cx = X - (cxm - self.px / 2) * s
        self.cy = Y + (cym - self.py / 2) * s
        left = self.cx - self.px / 2 * s; top = self.cy + self.py / 2 * s
        ext = (left + x0 * s, left + x1 * s, top - y1 * s, top - y0 * s)
        F.ax.imshow(np.asarray(im)[y0:y1, x0:x1], extent=ext, origin="upper", zorder=2, interpolation="lanczos")
        self.ext = ext
        return ext

    def P(self, xyz):
        d = np.array(xyz, float) - self.t
        return self.cx + float(d @ self.r) * self.k, self.cy + float(d @ self.u) * self.k


def fmt(v, d=1):
    return f"{abs(v):.{d}f}"
