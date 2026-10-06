"""Pembantu lembar A3 (matplotlib): bingkai, kolom judul, garis dimensi, penempatan render ortografis dengan pemetaan mm -> kertas."""
import os, json, math, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from PIL import Image

DATE = "05-10-2026"
FS = 6.6
LW = 0.35
plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})


def f1(v, d=1):
    return f"{abs(v):.{d}f}".replace(".", ",")


def new_sheet():
    fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 420); ax.set_ylim(0, 297); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((5, 5), 410, 287, fill=False, lw=1.0, ec="k"))
    return fig, ax


def hline(ax, x0, x1, y, **kw):
    ax.plot([x0, x1], [y, y], lw=kw.pop("lw", LW), color=kw.pop("c", "k"), solid_capstyle="butt", zorder=kw.pop("zorder", 5), **kw)


def vline(ax, x, y0, y1, **kw):
    ax.plot([x, x], [y0, y1], lw=kw.pop("lw", LW), color=kw.pop("c", "k"), solid_capstyle="butt", zorder=kw.pop("zorder", 5), **kw)


def arrow(ax, p0, p1, style="<|-|>"):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle=style, lw=0.45, color="k", mutation_scale=5, shrinkA=0, shrinkB=0), zorder=6)


def hdim(ax, x0, x1, yl, yf0, yf1, text, small=False, fs=None):
    fs = fs or FS
    s = 1 if yl > yf0 else -1
    vline(ax, x0, yf0 + s * 0.8, yl + s * 1.3)
    vline(ax, x1, yf1 + s * 0.8, yl + s * 1.3)
    xa, xb = min(x0, x1), max(x0, x1)
    if small or abs(x1 - x0) < 9:
        arrow(ax, (xa - 5, yl), (xa, yl), "-|>"); arrow(ax, (xb + 5, yl), (xb, yl), "-|>")
        hline(ax, xa - 5, xb + 5, yl)
        ax.text(xb + 6, yl + 0.9, text, fontsize=fs, ha="left", va="bottom", zorder=7)
    else:
        arrow(ax, (xa, yl), (xb, yl))
        ax.text((xa + xb) / 2, yl + 0.9, text, fontsize=fs, ha="center", va="bottom", zorder=7)


def vdim(ax, xl, y0, y1, xf0, xf1, text, side="left", fs=None):
    fs = fs or FS
    s = 1 if xl > xf0 else -1
    hline(ax, xf0 + s * 0.8, xl + s * 1.3, y0)
    hline(ax, xf1 + s * 0.8, xl + s * 1.3, y1)
    ya, yb = min(y0, y1), max(y0, y1)
    if abs(y1 - y0) < 9:
        arrow(ax, (xl, ya - 5), (xl, ya), "-|>"); arrow(ax, (xl, yb + 5), (xl, yb), "-|>")
        vline(ax, xl, ya - 5, yb + 5)
        ax.text(xl + (1.0 if side == "right" else -1.0), yb + 6.5, text, fontsize=fs, rotation=90, ha="right" if side == "left" else "left", va="bottom", zorder=7)
    else:
        arrow(ax, (xl, ya), (xl, yb))
        ax.text(xl + (-0.9 if side == "left" else 0.9), (ya + yb) / 2, text, fontsize=fs, rotation=90, ha="right" if side == "left" else "left", va="center", zorder=7)


def leader(ax, p_from, p_text, text, ha="left", va="center", fs=None):
    fs = fs or FS
    ax.plot([p_from[0], p_text[0]], [p_from[1], p_text[1]], lw=0.35, color="k", zorder=8)
    ax.plot([p_from[0]], [p_from[1]], marker="o", ms=1.4, color="k", zorder=8)
    ax.text(p_text[0] + (0.8 if ha == "left" else -0.8), p_text[1], text, fontsize=fs, ha=ha, va=va, zorder=9,
            bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.85))


def label(ax, x, y, text, size=8.5, weight="bold", ha="center", color="k"):
    ax.text(x, y, text, fontsize=size, fontweight=weight, ha=ha, va="center", zorder=7, color=color)


def title_block(ax, title, subtitle, page, of, scale="Skala: lihat dimensi", right_line="Bahan: sesuai komponen"):
    x0, y0, w, h = 255, 15, 157, 44
    ax.add_patch(Rectangle((x0, y0), w, h, fill=True, fc="white", lw=0.9, ec="k", zorder=11))
    for yy in (y0 + 11, y0 + 22, y0 + 33):
        hline(ax, x0, x0 + w, yy, lw=0.5, zorder=12)
    vline(ax, x0 + 98, y0, y0 + 22, lw=0.5, zorder=12)
    ax.text(x0 + 3, y0 + 39, title, fontsize=9.5, fontweight="bold", va="center", zorder=13)
    ax.text(x0 + 3, y0 + 27.5, "Tugas Akhir: Implementasi LightGBM ke ESP32 berbasis sinyal ECG dan PPG", fontsize=6.6, va="center", zorder=13)
    ax.text(x0 + 3, y0 + 16.5, subtitle, fontsize=6.6, va="center", zorder=13)
    ax.text(x0 + 3, y0 + 5.5, f"Satuan: mm   |   {scale}", fontsize=6.6, va="center", zorder=13)
    ax.text(x0 + 101, y0 + 16.5, right_line, fontsize=6.6, va="center", zorder=13)
    ax.text(x0 + 101, y0 + 5.5, f"Halaman {page}/{of}   |   {DATE}", fontsize=6.6, va="center", zorder=13)
    ax.text(x0 + 3, y0 - 3, "Digambar: ........................   NIM: ........................   Toleransi umum: +-0,2 mm (FDM)", fontsize=5.8, va="center", zorder=13)


def rgba_on_white(path):
    im = Image.open(path).convert("RGBA")
    return im


def crop_alpha(im, pad=6):
    a = np.asarray(im)[..., 3]
    ys, xs = np.where(a > 8)
    if len(xs) == 0: return im, (0, 0, im.size[0], im.size[1])
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, im.size[0]), min(ys.max() + pad, im.size[1]))
    return im.crop(box), box


class Ortho:
    """render ortografis + info (target, right, up, ortho, px) -> pemetaan titik model (mm) ke koordinat kertas."""
    def __init__(self, png, info_view):
        self.png = png; self.iv = info_view
        self.px = info_view["px"][0] if isinstance(info_view["px"], list) else info_view["px"]
        self.t = np.array(info_view["target"]); self.r = np.array(info_view["right"]); self.u = np.array(info_view["up"])
        self.o = info_view["ortho"]

    def place(self, ax, cx, cy, wmm, zorder=2, crop=False):
        """gambar dipasang dengan lebar wmm pada kertas, pusat gambar di (cx, cy). Mengembalikan faktor skala (mm kertas per mm model)."""
        im = Image.open(self.png).convert("RGBA")
        self.k = wmm / self.o * (self.o / self.px) * self.px / self.o * (self.o / self.px)       # = wmm / px * px / o  -> disederhanakan di bawah
        self.k = wmm / self.o                                                                       # lebar gambar = ortho mm model -> wmm kertas
        h = wmm * im.size[1] / im.size[0]
        self.cx, self.cy = cx, cy
        ax.imshow(np.asarray(im), extent=(cx - wmm / 2, cx + wmm / 2, cy - h / 2, cy + h / 2), origin="upper", zorder=zorder, interpolation="lanczos")
        return self.k

    def P(self, xyz):
        d = np.array(xyz, float) - self.t
        return self.cx + float(d @ self.r) * self.k, self.cy + float(d @ self.u) * self.k
