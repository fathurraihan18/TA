"""Gambar teknik cover FINAL (v2 + gland + saklar + penahan sekrup kecil): hal. 1 tampak, hal. 2 plate belakang + isometrik + tabel, hal. 3 potongan, hal. 4 penahan sekrup.
Jalankan: python gt_cover.py <folder_case_v2d> <folder_garis_png> <folder_render_cover> <folder_output>
"""
import sys, os, json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as _cm

CASE, LINES, PREV, OUTD = sys.argv[1:5]
os.makedirs(OUTD, exist_ok=True)
S = json.load(open(os.path.join(CASE, "_ref", "summary.json")))

HX = S["outer"][0] / 2                                  # 52.5
YB, HY = S.get("outer_y", [-S["outer"][1] / 2, S["outer"][1] / 2])   # muka luar Bawah / Atas (v2: -31,75 / 31,75; v3: -38,5 / 31,75)
YC = (YB + HY) / 2; HH = (HY - YB) / 2                  # pusat dan setengah tinggi outline sumbu Y
V3 = bool(S.get("battery"))
PX = S["plate"][0] / 2                                  # 66.5
ZB, ZS, ZT = S["z"]["plate_bottom"], S["z"]["split"], S["z"]["top"]   # -3.5, -0.5, 33.9
DEPTH = ZT - ZB
mc, jk, uc, gl, sw = S["micro"], S["jack"], S["usbc"], S["gland"], S["switch"]
belt, win = S["belt"], S["window"]
ZC = (ZB + ZT) / 2                                      # pusat tampak dalam Z (15.2)

FS = 6.6          # ukuran font dimensi (pt)
LW = 0.35


def f1(v): return f"{abs(v):.1f}".replace(".", ",")


def f1h(v):                         # 1-2 desimal (70,25 tidak dibulatkan ke 70,2)
    t = f"{abs(v):.2f}".replace(".", ",")
    return t[:-1] if t.endswith("0") else t


# ---------------------------------------------------------------- tampak
class View:
    def __init__(self, name, cx, cy, win_wh, uvmap, ctr_uv):
        self.name, self.cx, self.cy, self.win, self.uv, self.ctr = name, cx, cy, win_wh, uvmap, ctr_uv

    def uv_(self, X, Y, Z): return self.uv(X, Y, Z)

    def p(self, X, Y, Z):
        u, v = self.uv(X, Y, Z)
        return self.cx + (u - self.ctr[0]), self.cy + (v - self.ctr[1])

    def pu(self, u, v):
        return self.cx + (u - self.ctr[0]), self.cy + (v - self.ctr[1])

    def draw(self, ax):
        img = np.asarray(Image.open(os.path.join(LINES, f"garis_{self.name}.png")).convert("RGB"))
        w, h = self.win
        ax.imshow(img, extent=(self.cx - w / 2, self.cx + w / 2, self.cy - h / 2, self.cy + h / 2), origin="upper",
                  interpolation="lanczos", zorder=1)


def mk_views(cy_front):
    V = {}
    V["depan"] = View("depan", 200, cy_front, (140, 76), lambda X, Y, Z: (X, Y), (0, YC))
    V["atas"] = View("atas", 200, cy_front + HH + 36.25, (140, 48), lambda X, Y, Z: (X, -Z), (0, -ZC))
    V["bawah"] = View("bawah", 200, cy_front - HH - 58.25, (140, 48), lambda X, Y, Z: (X, Z), (0, ZC))
    V["kanan"] = View("kanan", 92, cy_front, (48, 76), lambda X, Y, Z: (Z, Y), (ZC, YC))
    V["kiri"] = View("kiri", 308, cy_front, (48, 76), lambda X, Y, Z: (-Z, Y), (-ZC, YC))
    return V


# ---------------------------------------------------------------- gambar bantu
def hline(ax, x0, x1, y, **kw):
    ax.plot([x0, x1], [y, y], lw=kw.pop("lw", LW), color=kw.pop("c", "k"), solid_capstyle="butt", zorder=5, **kw)


def vline(ax, x, y0, y1, **kw):
    ax.plot([x, x], [y0, y1], lw=kw.pop("lw", LW), color=kw.pop("c", "k"), solid_capstyle="butt", zorder=5, **kw)


def arrow(ax, p0, p1, style="<|-|>"):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle=style, lw=0.45, color="k", mutation_scale=5, shrinkA=0, shrinkB=0), zorder=6)


def hdim(ax, x0, x1, yl, yf0, yf1, text, tpos="above", small=False):
    """dimensi horizontal: garis ukur di y=yl; garis bantu dari fitur (yf0,yf1)."""
    s = 1 if yl > yf0 else -1
    vline(ax, x0, yf0 + s * 0.8, yl + s * 1.3)
    vline(ax, x1, yf1 + s * 0.8, yl + s * 1.3)
    xa, xb = min(x0, x1), max(x0, x1)
    if small or abs(x1 - x0) < 9:
        arrow(ax, (xa - 5, yl), (xa, yl), "-|>"); arrow(ax, (xb + 5, yl), (xb, yl), "-|>")
        hline(ax, xa - 5, xb + 5, yl)
        ax.text(xb + 6, yl + 0.9, text, fontsize=FS, ha="left", va="bottom", zorder=7)
    else:
        arrow(ax, (xa, yl), (xb, yl))
        ax.text((xa + xb) / 2, yl + (0.9 if tpos == "above" else -0.9), text, fontsize=FS, ha="center",
                va="bottom" if tpos == "above" else "top", zorder=7)


def vdim(ax, xl, y0, y1, xf0, xf1, text, side="left"):
    s = 1 if xl > xf0 else -1
    hline(ax, xf0 + s * 0.8, xl + s * 1.3, y0)
    hline(ax, xf1 + s * 0.8, xl + s * 1.3, y1)
    ya, yb = min(y0, y1), max(y0, y1)
    if abs(y1 - y0) < 9:
        arrow(ax, (xl, ya - 5), (xl, ya), "-|>"); arrow(ax, (xl, yb + 5), (xl, yb), "-|>")
        vline(ax, xl, ya - 5, yb + 5)
        ax.text(xl + (1.0 if side == "right" else -1.0), yb + 6.5, text, fontsize=FS, rotation=90,
                ha="right" if side == "left" else "left", va="bottom", zorder=7)
    else:
        arrow(ax, (xl, ya), (xl, yb))
        ax.text(xl + (-0.9 if side == "left" else 0.9), (ya + yb) / 2, text, fontsize=FS, rotation=90,
                ha="right" if side == "left" else "left", va="center", zorder=7)


def center_cross(ax, x, y, r=4.2):
    for dx, dy in ((r, 0), (0, r)):
        ax.plot([x - dx, x + dx], [y - dy, y + dy], lw=0.3, color="#c00000", dashes=(6, 1.5, 1, 1.5), zorder=4)


def leader(ax, p_from, p_text, text, ha="left", va="center"):
    ax.plot([p_from[0], p_text[0]], [p_from[1], p_text[1]], lw=0.35, color="k", zorder=5)
    ax.plot([p_from[0]], [p_from[1]], marker="o", ms=1.4, color="k", zorder=6)
    ax.text(p_text[0] + (0.8 if ha == "left" else -0.8), p_text[1], text, fontsize=FS, ha=ha, va=va, zorder=7)


def label(ax, x, y, text, size=8.5, weight="bold", ha="center"):
    ax.text(x, y, text, fontsize=size, fontweight=weight, ha=ha, va="center", zorder=7)


def new_sheet():
    fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 420); ax.set_ylim(0, 297); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((5, 5), 410, 287, fill=False, lw=1.0, ec="k"))        # bingkai
    return fig, ax


NPAGE = 4


def title_block(ax, page, of, subtitle):
    _cm.title_block(ax, "GAMBAR TEKNIK: COVER ALAT ECG + PPG", subtitle, page, NPAGE, scale="Skala 1:1   |   Proyeksi sudut ketiga", right_line="Bahan: PETG (cetak 3D FDM)")


# =============================================================== HALAMAN 1
def page1():
    fig, ax = new_sheet()
    V = mk_views(166 if V3 else 168)
    for v in V.values():
        v.draw(ax)
    D, K, A, B, L, R = V["depan"], V["kanan"], V["atas"], V["bawah"], V["kiri"], V["kanan"]

    # ---------- TAMPAK DEPAN (u=X, v=Y)
    f = V["depan"]
    xl, xr = f.p(-HX, 0, 0)[0], f.p(HX, 0, 0)[0]
    xwl, xwr = f.p(-PX, 0, 0)[0], f.p(PX, 0, 0)[0]
    yb = f.p(0, YB, 0)[1]; yt = f.p(0, HY, 0)[1]
    y1, y2 = yb - 5.5, yb - 11.5
    hdim(ax, xwl, xl, y1, yb, yb, f1(PX - HX), small=True)
    hdim(ax, xl, xr, y1, yb, yb, f1(2 * HX))
    hdim(ax, xr, xwr, y1, yb, yb, f1(PX - HX), small=True)
    hdim(ax, xwl, xwr, y2, yb, yb, f1(2 * PX))
    vdim(ax, xwr + 8, yb, yt, xwr, xwr, f1h(2 * HH), side="right")
    # jendela layar
    wx0, wx1 = f.p(win[2] - win[0] / 2, 0, 0)[0], f.p(win[2] + win[0] / 2, 0, 0)[0]
    wy0, wy1 = f.p(0, -win[1] / 2, 0)[1], f.p(0, win[1] / 2, 0)[1]
    yw = f.p(0, 10, 0)[1]
    arrow(ax, (wx0, yw), (wx1, yw)); ax.text((wx0 + wx1) / 2, yw + 0.9, f"{f1(win[0])}", fontsize=FS, ha="center", va="bottom", zorder=7)
    xw = f.p(30, 0, 0)[0]
    arrow(ax, (xw, wy0), (xw, wy1)); ax.text(xw + 0.9, f.p(0, -12, 0)[1], f"{f1(win[1])}", fontsize=FS, rotation=90, ha="left", va="center", zorder=7)
    ax.text((wx0 + wx1) / 2, f.p(0, -3, 0)[1], "JENDELA LAYAR (area aktif 73,44 x 48,96)", fontsize=6, ha="center", va="center", zorder=7)
    ax.text((wx0 + wx1) / 2, f.p(0, -7, 0)[1], f"digeser {f1(abs(win[2]))} ke Kanan dari pusat", fontsize=5.6, ha="center", va="center", zorder=7)
    leader(ax, f.p(HX - 1.4, HY - 1.4, 0), (f.p(HX, HY, 0)[0] - 28, f.p(HX, HY, 0)[1] + 9), f"R{f1(S['out_r'])}  (sudut luar)", ha="right")
    label(ax, 200, yt + 12.5, "TAMPAK DEPAN")

    # ---------- TAMPAK ATAS = muka dinding Atas (u=X, v=-Z)
    a = V["atas"]
    ya_top = a.p(0, 0, ZB)[1]
    ya_bot = a.p(0, 0, ZT)[1]
    xa_r = a.p(PX, 0, 0)[0]; xa_Kiri = a.p(HX, 0, 0)[0]; xa_Kanan = a.p(-HX, 0, 0)[0]
    # tebal total
    vdim(ax, xa_r + 8, ya_bot, ya_top, xa_r, xa_r, f1(DEPTH), side="right")
    # posisi jack dari tepi Kiri casing
    xj, yj = a.p(jk["x"], 0, jk["zc"])
    center_cross(ax, xj, yj)
    yl = ya_top + 7
    hdim(ax, xj, xa_Kiri, yl, ya_top, ya_top, f1(HX - jk["x"]))
    leader(ax, (xj - (jk["d"] + 0.2) / 2, yj), (xj - 9, yj), f"JACK AD8232  Ø{f1(jk['d'] + 0.2)}", ha="right")
    ax.text(xj - 9.8, yj - 3.2, f"(Z={f1(jk['zc'] - ZB)} dari bidang belakang)", fontsize=5.4, ha="right", va="center", zorder=7)
    # saklar
    xs, ys = a.p(sw["x"], 0, sw["zc"])
    center_cross(ax, xs, ys)
    yl2 = ya_top + 13
    hdim(ax, xs, xa_Kiri, yl2, ya_top, ya_top, f1(HX - sw["x"]))
    leader(ax, (xs + (sw["cut_w"] + 0.1) / 2, ys), (xs + 11, ys), f"SAKLAR KCD11  {f1(sw['cut_w'] + 0.1)} x {f1(sw['cut_h'] + 0.1)}")
    ax.text(xs + 11.8, ys - 3.2, f"(Z={f1(sw['zc'] - ZB)} dari bidang belakang)", fontsize=5.4, ha="left", va="center", zorder=7)
    # tonjolan gland di sisi kanan (terlihat dari atas)
    xg0 = a.p(-HX, 0, 0)[0]; xg1 = a.p(-HX - gl["out"], 0, 0)[0]
    yg = a.p(0, 0, gl["zc"])[1]
    arrow(ax, (xg1 - 5, ya_top - 0.0 + 0), (xg1, ya_top - 0.0 + 0), "-|>") if False else None
    hdim(ax, xg1, xg0, a.p(0, 0, 33.9 + 0)[1] - 3.5, a.p(0, 0, gl["zc"] + 11.3)[1], a.p(0, 0, gl["zc"] + 11.3)[1], f1(gl["out"]), small=True)
    ax.text(xa_Kanan - 1, ya_bot - 6.5, "tonjolan gland", fontsize=5.4, ha="right", va="center", zorder=7)
    label(ax, 200, a.p(0, 0, ZB)[1] + 20, "TAMPAK ATAS (muka dinding Atas)")

    # ---------- TAMPAK BAWAH = muka dinding Bawah (u=X, v=Z)
    b = V["bawah"]
    yb_bot = b.p(0, 0, ZB)[1]; yb_top = b.p(0, 0, ZT)[1]
    xb_Kiri = b.p(HX, 0, 0)[0]
    xm, ym = b.p(mc["x"], 0, mc["zc"])
    center_cross(ax, xm, ym)
    hdim(ax, xm, xb_Kiri, yb_bot - 6.5, yb_bot, yb_bot, f1(HX - mc["x"]))
    xb_r = b.p(PX, 0, 0)[0]
    z_lo, z_hi = mc["zc"] - (mc["h"] + 0.2) / 2, mc["zc"] + (mc["h"] + 0.2) / 2
    xv = b.p(mc["x"] + (mc["w"] + 0.2) / 2 + 9, 0, 0)[0]
    vdim(ax, xv, b.p(0, 0, ZB)[1], b.p(0, 0, z_lo)[1], xv - 2.5, xv - 2.5, f1(z_lo - ZB), side="right")
    vdim(ax, xv + 8, b.p(0, 0, z_lo)[1], b.p(0, 0, z_hi)[1], xv - 2.5, xv - 2.5, f1(z_hi - z_lo), side="right")
    leader(ax, (xm - (mc["w"] + 0.2) / 2, ym + (mc["h"] + 0.2) / 2), (xm - 26, ym + 9), f"MICRO-USB ESP32  {f1(mc['w'] + 0.2)} x {f1(mc['h'] + 0.2)}", ha="right")
    label(ax, 200, yb_top + 6.0, "TAMPAK BAWAH (muka dinding Bawah)")

    # ---------- TAMPAK KANAN (u=Z, v=Y) : USB-C + gland PG7
    k = V["kanan"]
    xk0 = k.p(0, 0, ZB)[0]; xk1 = k.p(0, 0, ZT)[0]
    yk_t = k.p(0, HY, 0)[1]; yk_b = k.p(0, YB, 0)[1]
    # USB-C
    xu, yu = k.p(0, uc["y"], uc["zc"])
    center_cross(ax, xu, yu, 3.2)
    vdim(ax, xk0 - 7, yk_t, yu, xk0, xk0, f1(HY - uc["y"]), side="left")
    leader(ax, (xu + (uc["h"] + 0.2) / 2, yu), (xk1 + 9, yu + 4), f"USB-C  {f1(uc['w'] + 0.2)} x {f1(uc['h'] + 0.2)}")
    hdim(ax, k.p(0, 0, ZB)[0], k.p(0, 0, uc["zc"] - (uc["h"] + 0.2) / 2)[0], yk_t + 7, yk_t, yu + (uc["w"] + 0.2) / 2, f1(uc["zc"] - (uc["h"] + 0.2) / 2 - ZB), small=True)
    # gland
    xgl, ygl = k.p(0, gl["y"], gl["zc"])
    center_cross(ax, xgl, ygl, 5.5)
    vdim(ax, xk0 - 7, yk_b, ygl, xk0, xk0, f1(gl["y"] - YB), side="left")
    hdim(ax, k.p(0, 0, ZB)[0], xgl, yk_b - 6.5, yk_b, yk_b, f1(gl["zc"] - ZB))
    leader(ax, (xgl + 4.5, ygl - 4.5), (xk1 + 9, ygl - 12), f"GLAND PG7  Ø{f1(gl['hole'])}")
    ax.text(xk1 + 9.8, ygl - 15.5, f"(kantong mur AF {f1(gl['nut_af'])})", fontsize=5.4, ha="left", va="center", zorder=7)
    hdim(ax, xk0, xk1, yk_b - 12.5, yk_b, yk_b, f1(DEPTH))
    label(ax, 92, yk_t + 12.5, "TAMPAK KANAN")

    # ---------- TAMPAK KIRI (u=-Z, v=Y)
    l = V["kiri"]
    xl0 = l.p(0, 0, ZT)[0]; xl1 = l.p(0, 0, ZB)[0]
    yl_t = l.p(0, HY, 0)[1]; yl_b = l.p(0, YB, 0)[1]
    vdim(ax, xl1 + 8, yl_b, yl_t, xl1, xl1, f1h(2 * HH), side="right")
    hdim(ax, xl0, xl1, yl_b - 6.5, yl_b, yl_b, f1(DEPTH))
    z_split_x = l.p(0, 0, ZS)[0]
    hdim(ax, z_split_x, xl1, yl_b - 12.5, yl_b, yl_b, f1(ZS - ZB), small=True)
    leader(ax, (l.p(0, 0, ZT - 0.5)[0], l.p(0, HY, 0)[1] - 0.3), (l.p(0, 0, ZT)[0] + 4, yl_t + 8), f"chamfer {f1(S['ch'])} x 45°", ha="left")
    ax.text(l.p(0, 0, ZT)[0] + 0.0, yl_t + 12.5, "", fontsize=1)
    label(ax, 308, yk_t + 12.5, "TAMPAK KIRI")

    # ---------- keterangan
    notes = ["KETERANGAN",
             "1. Z diukur dari bidang belakang casing (Z=0).",
             "    Dari ujung ekor baut: Z' = Z - 3,5.",
             "2. Posisi lubang dari Gerber PCB + ukuran yang diukur;",
             "    lubang sudah +0,2 mm (kompensasi cetak).",
             "3. Sisi: Kiri = sisi header TFT, Atas = sisi jack",
             "    AD8232 + saklar, Bawah = micro-USB ESP32,",
             "    Kanan = USB-C powerbank + gland PPG.",
             "4. Dari tepi PCB: jack 61,3 dari Kiri;",
             "    micro-USB 20,7 dari Kiri;",
             "    USB-C 18,1 dari Atas.",
             f"5. Shell {f1(2 * HX)} x {f1h(2 * HH)} x {f1(ZT - ZS)}; dengan back",
             f"    plate + sayap: {f1(2 * PX)} x {f1h(2 * HH)} x {f1(DEPTH)}.",
             f"6. Rongga dalam {f1(S['cavity'][0])} x {f1h(S['cavity'][1])}, dinding 3,0.",
             "7. Plate: 4 sekrup M3x8 flat head dari belakang",
             "    ke 3 penahan sekrup (hal. 4)."] + ([
             f"8. Ruang baterai 10 x 34 x 50: rongga sisi",
             f"    Bawah diperlebar {f1(S['bay'])} (tepi PCB ke dinding",
             f"    {f1(S['cavity_y'][0] - S['pcb']['y0'])}). Penyangga: 3 rusuk + 2 stopper di plate."] if V3 else [])
    for i, t in enumerate(notes):
        ax.text(340, 280 - i * 4.4, t, fontsize=6.3, fontweight="bold" if i == 0 else "normal", va="center", zorder=7)
    title_block(ax, 1, 2, "Tampak depan, atas, bawah, kanan, kiri")
    return fig


# =============================================================== HALAMAN 2
def page2():
    fig, ax = new_sheet()
    # ---- tampak belakang (back plate)
    bk = View("belakang", 130, 215, (140, 76), lambda X, Y, Z: (-X, Y), (0, YC))
    bk.draw(ax)
    x_l, x_r = bk.p(PX, 0, 0)[0], bk.p(-PX, 0, 0)[0]
    y_b, y_t = bk.p(0, YB, 0)[1], bk.p(0, HY, 0)[1]
    hdim(ax, x_l, x_r, y_b - 6.5, y_b, y_b, f1(2 * PX))
    vdim(ax, x_r + 8, y_b, y_t, x_r, x_r, f1h(2 * HH), side="right")
    # slot sabuk (kanan di gambar = Kanan casing karena u=-X)
    for sgn in (1, -1):
        cx_, cy_ = bk.p(sgn * belt["slot_cx"], YC, 0)
        center_cross(ax, cx_, cy_, 3.5)
    sxL = bk.p(belt["slot_cx"], 0, 0)[0]   # u negatif -> sisi kiri gambar (= Kiri casing? u=-X: X=+59 -> u=-59)
    sxR = bk.p(-belt["slot_cx"], 0, 0)[0]
    s_hw = belt["slot_w"] / 2
    hdim(ax, sxR - s_hw, sxR + s_hw, y_t + 6.5, y_t, y_t, f1(belt["slot_w"]), small=True)
    vdim(ax, sxR + s_hw + 8, bk.p(0, YC - belt["slot_l"] / 2, 0)[1], bk.p(0, YC + belt["slot_l"] / 2, 0)[1], sxR + s_hw, sxR + s_hw, f1(belt["slot_l"]), side="right")
    hdim(ax, x_r, sxR + s_hw, y_b - 12.5, y_b, y_b, f1(PX - belt["slot_cx"] - s_hw), small=True)
    hdim(ax, sxR - s_hw, bk.p(-HX, 0, 0)[0], y_b - 18.5, y_b, y_b, f1(belt["slot_cx"] - s_hw - HX), small=True)
    ax.text(sxR - 6, bk.p(0, YC, 0)[1] + 12, "slot sabuk: lebar sabuk <= 40, tebal <= 4,5", fontsize=5.4, ha="right", va="center", zorder=7)
    # dinding shell (garis putus) dan lubang sekrup
    sh_x0, sh_x1 = bk.p(HX, 0, 0)[0], bk.p(-HX, 0, 0)[0]
    ax.add_patch(Rectangle((sh_x0, y_b + 0.0), sh_x1 - sh_x0, y_t - y_b, fill=False, lw=0.4, ec="k", ls=(0, (6, 2)), zorder=5))
    ax.text(bk.p(0, 0, 0)[0], bk.p(0, YC, 0)[1], "siluet shell (garis putus)", fontsize=5.6, ha="center", va="center", zorder=7)
    pts = S["screws"]
    xs_ = sorted({p[0] for p in pts}); ys_ = sorted({p[1] for p in pts})
    xa_, xb_ = bk.p(xs_[1], 0, 0)[0], bk.p(xs_[0], 0, 0)[0]
    ya_, yb_ = bk.p(0, ys_[0], 0)[1], bk.p(0, ys_[1], 0)[1]
    hdim(ax, xa_, xb_, y_t + 13, yb_, yb_, f1(xs_[1] - xs_[0]))
    vdim(ax, x_l - 8, ya_, yb_, xa_, xa_, f1h(ys_[1] - ys_[0]), side="left")
    leader(ax, (xb_ + 2.4, ya_ + 2.4), (xb_ + 14, ya_ + 12), "4x lubang M3, countersink Ø6,6 (sekrup M3x8 flat head)")
    ax.text(130, y_t + 22, "TAMPAK BELAKANG (back plate + sayap)", fontsize=8.5, fontweight="bold", ha="center", va="center")

    # ---- gambar isometrik (render Cycles, PETG putih)
    for fn, (cx_, cy_, w_) in (("cover_iso_depan.png", (330, 244, 108)), ("cover_iso_belakang.png", (330, 168, 108))):
        p = os.path.join(PREV, fn)
        if os.path.exists(p):
            im = Image.open(p).convert("RGBA")
            a_ = np.asarray(im)[..., 3]; ys_, xs_ = np.where(a_ > 6)
            im = im.crop((max(xs_.min() - 8, 0), max(ys_.min() - 8, 0), min(xs_.max() + 8, im.size[0]), min(ys_.max() + 8, im.size[1])))
            hh_mm = w_ * im.size[1] / im.size[0]
            if hh_mm > 70: w_ = w_ * 70 / hh_mm; hh_mm = 70
            ax.imshow(np.asarray(im), extent=(cx_ - w_ / 2, cx_ + w_ / 2, cy_ - hh_mm / 2, cy_ + hh_mm / 2), zorder=1, interpolation="lanczos")
    ax.text(330, 288.5, "ISOMETRIK: depan (kanan-atas) dan belakang", fontsize=8.5, fontweight="bold", ha="center", va="center")

    # ---- skema pemakaian sabuk (penampang X-Z di Y=0)
    ox, oy, sc = 130, 118, 1.0     # titik asal skema di kertas
    ax.text(ox, 156, "SKEMA SABUK (potongan melintang, sabuk lewat 2 slot)", fontsize=8.5, fontweight="bold", ha="center", va="center")

    def P(x, z): return ox + x * 0.9, oy + z * 0.9
    # plate dengan slot
    for (xa, xb) in ((-PX, -belt["slot_cx"] - s_hw), (-belt["slot_cx"] + s_hw, belt["slot_cx"] - s_hw), (belt["slot_cx"] + s_hw, PX)):
        x0, z0 = P(xa, ZB); x1, z1 = P(xb, ZS)
        ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, fc="#9ab0d0", ec="k", lw=0.5, zorder=3))
    sx0, sz0 = P(-HX, ZS); sx1, sz1 = P(HX, ZT)
    ax.add_patch(Rectangle((sx0, sz0), sx1 - sx0, sz1 - sz0, fc="#e8e8ee", ec="k", lw=0.5, zorder=3))
    ax.text(*P(0, 15), "SHELL + TUMPUKAN PCB", fontsize=6.5, ha="center", va="center", zorder=7)
    # sabuk
    zt, zb_ = ZS + 2.5, ZB - 2.5
    path = [(-PX - 10, zt), (-belt["slot_cx"], zt), (-belt["slot_cx"], zb_), (belt["slot_cx"], zb_), (belt["slot_cx"], zt), (PX + 10, zt)]
    xs_p, zs_p = zip(*[P(x, z) for x, z in path])
    ax.plot(xs_p, zs_p, lw=2.6, color="#d9731a", solid_joinstyle="miter", zorder=6)
    ax.text(*P(0, zb_ - 5), "badan pengguna", fontsize=6.3, ha="center", va="center", zorder=7)
    xb0, zb0 = P(-PX - 8, zb_ - 8); xb1, _ = P(PX + 8, zb_ - 8)
    hline(ax, xb0, xb1, zb0 + 0.0, lw=0.6)
    for t in range(0, int(xb1 - xb0), 4):
        ax.plot([xb0 + t, xb0 + t - 2.5], [zb0, zb0 - 2.5], lw=0.3, color="k")
    ax.text(*P(0, zb_ - 15), "Sabuk turun lewat slot sayap, melintas di belakang back plate, lalu naik lewat slot lain.", fontsize=6.0, ha="center", va="center", zorder=7)
    ax.text(*P(0, zb_ - 19), "Untuk bahu: sabuk/tali yang sama dipasang melintang lewat kedua slot.", fontsize=6.0, ha="center", va="center", zorder=7)

    # ---- tabel spesifikasi lubang
    tx, ty = 262, 103
    ax.text(tx, ty + 24, "TABEL POSISI & UKURAN LUBANG (dari tepi casing, mm)", fontsize=7.2, fontweight="bold", va="center")
    rows = [("Sisi", "Fitur", "Posisi", "Ukuran lubang"),
            ("Bawah", "micro-USB ESP32", f"{f1(HX - mc['x'])} dari Kiri; Z {f1(mc['zc'] - (mc['h'] + .2) / 2 - ZB)}-{f1(mc['zc'] + (mc['h'] + .2) / 2 - ZB)}", f"{f1(mc['w'] + .2)} x {f1(mc['h'] + .2)}"),
            ("Atas", "jack AD8232", f"{f1(HX - jk['x'])} dari Kiri; Z {f1(jk['zc'] - ZB)}", f"Ø{f1(jk['d'] + .2)}"),
            ("Atas", "saklar KCD11", f"{f1(HX - sw['x'])} dari Kiri; Z {f1(sw['zc'] - ZB)}", f"{f1(sw['cut_w'] + .1)} x {f1(sw['cut_h'] + .1)}"),
            ("Kanan", "USB-C powerbank", f"{f1(HY - uc['y'])} dari Atas; Z {f1(uc['zc'] - (uc['h'] + .2) / 2 - ZB)}-{f1(uc['zc'] + (uc['h'] + .2) / 2 - ZB)}", f"{f1(uc['w'] + .2)} x {f1(uc['h'] + .2)}"),
            ("Kanan", "gland PG7 (PPG)", f"{f1(gl['y'] - YB)} dari Bawah; Z {f1(gl['zc'] - ZB)}", f"Ø{f1(gl['hole'])} + mur AF {f1(gl['nut_af'])}"),
            ("Depan", "jendela layar", f"pusat, geser {f1(abs(win[2]))} ke Kanan", f"{f1(win[0])} x {f1(win[1])}"),
            ("Belakang", "slot sabuk 2x", f"X = +-{f1(belt['slot_cx'])} dari pusat", f"{f1(belt['slot_w'])} x {f1(belt['slot_l'])}")] + (
            [("Dalam", "ruang baterai (v3)", f"Y {S['battery']['y0']:.1f} s.d. {S['battery']['y1']:.1f} dari pusat pola baut".replace(".", ",").replace("s,d,", "s.d."), "10 x 34 x 50 + celah")] if V3 else [])
    cw = [17, 36, 62, 33]
    for r, row in enumerate(rows):
        yy = ty + 17 - r * 5.2
        xx = tx
        for c, cell in enumerate(row):
            ax.text(xx + 1, yy, cell, fontsize=5.7, fontweight="bold" if r == 0 else "normal", va="center", zorder=7)
            xx += cw[c]
        hline(ax, tx, tx + sum(cw), yy - 2.6, lw=0.3)
    ax.add_patch(Rectangle((tx, ty + 17 - len(rows) * 5.2 + 2.6 - 0.0), sum(cw), len(rows) * 5.2, fill=False, lw=0.5, ec="k"))
    ax.text(tx, ty - 28.5, "Z diukur dari bidang belakang casing. Posisi dari Gerber PCB; uji ulang dengan jangka sorong.", fontsize=5.2, va="center")

    # ---- BOM
    bx, by = 40, 66
    ax.text(bx, by, "DAFTAR KOMPONEN PENDUKUNG", fontsize=7.2, fontweight="bold", va="center")
    bom = ["1x  Shell depan (PETG)             - file 1_Shell_Depan_siap_cetak.stl",
           "1x  Back plate + sayap (PETG)       - file 2_BackPlate_siap_cetak.stl",
           "1x  Penahan sekrup, 3 bagian (PETG) - file 3_Penahan_Sekrup_siap_cetak.stl",
           "4x  Sekrup M3 x 8 flat head (penutup)",
           "1x  Cable gland PG7 + mur (kabel 3-6,5 mm)",
           "1x  Saklar rocker KCD11 mini 10 x 15 mm, snap-in",
           "4x  Standoff M3 20 mm + baut (sudah ada pada tumpukan)"]
    for i, t in enumerate(bom):
        ax.text(bx, by - 5 - i * 4.0, t, fontsize=5.9, va="center")
    title_block(ax, 2, 2, "Back plate, isometrik, skema sabuk, tabel lubang")
    return fig


if __name__ == "__main__":
    pages = [page1(), page2()]
    try:
        import gt_extra
        pages += gt_extra.make(CASE, S, OUTD, PREV)
    except ImportError as e:
        print("hal. 3-4 tidak ada:", e)
    with PdfPages(os.path.join(OUTD, "Gambar_Teknik_Cover_ECG_PPG_A3.pdf")) as pdf:
        for f in pages: pdf.savefig(f, dpi=250)
    for i, f in enumerate(pages, 1):
        f.savefig(os.path.join(OUTD, f"Gambar_Teknik_Cover_Hal{i}_A3.png"), dpi=200)
    print("OK", len(pages), "halaman")
