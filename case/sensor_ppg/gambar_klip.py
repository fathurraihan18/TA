"""Gambar teknik A3 klip sensor PPG (halaman 1: potongan dan tampak berdimensi; halaman 2: eksplode, BOM, perakitan, gaya pegas).
python gambar_klip.py <folder_klip> <folder_render> <folder_output>
Skala potongan 2 : 1.
"""
import sys, os, json, math
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, PathPatch, Polygon as MPoly
from matplotlib.path import Path
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image

D, REN, OUTD = sys.argv[1:4]
os.makedirs(OUTD, exist_ok=True)
R = os.path.join(D, "_ref")
S = json.load(open(os.path.join(R, "summary.json")))
KIN = json.load(open(os.path.join(R, "kinematika.json")))
M = {k: trimesh.load(os.path.join(R, f"{k}_desain.stl")) for k in "ABC"}
GH = {k: trimesh.load(os.path.join(R, f"ref_{k}.stl")) for k in ("Modul_HW605", "Kabel_4_inti", "Kawat_bundel", "Pegas", "Sekrup_engsel")}
SC = 2.0
FS = 6.0
LW = 0.35
XP, XS, ZP, ZL, ZO, ZT = S["XP"], S["XS"], S["ZP"], S["Z_L"], S["Z_O"], S["Z_T"]
XL, W = S["XL"], S["W"]


def fmt(v, d=1):
    return f"{v:.{d}f}".replace(".", ",")


# ---------------------------------------------------------------- bantu gambar
def new_sheet():
    fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 420); ax.set_ylim(0, 297); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((5, 5), 410, 287, fill=False, lw=1.0, ec="k"))
    return fig, ax


def title_block(ax, page, of, subtitle):
    x0, y0, w, h = 255, 15, 157, 44
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=0.9, ec="k", zorder=5))
    for yy in (y0 + 11, y0 + 22, y0 + 33):
        ax.plot([x0, x0 + w], [yy, yy], lw=0.5, color="k")
    ax.plot([x0 + 98, x0 + 98], [y0, y0 + 22], lw=0.5, color="k")
    ax.text(x0 + 3, y0 + 39, "GAMBAR TEKNIK: KLIP SENSOR PPG MAX30102 (HW-605)", fontsize=9, fontweight="bold", va="center")
    ax.text(x0 + 3, y0 + 27.5, "Tugas Akhir: Implementasi LightGBM ke ESP32 berbasis sinyal ECG dan PPG", fontsize=6.4, va="center")
    ax.text(x0 + 3, y0 + 16.5, subtitle, fontsize=6.4, va="center")
    ax.text(x0 + 3, y0 + 5.5, "Satuan: mm   |   Skala potongan 2 : 1", fontsize=6.4, va="center")
    ax.text(x0 + 101, y0 + 16.5, "Bahan: PLA/PETG (cetak 3D FDM)", fontsize=6.4, va="center")
    ax.text(x0 + 101, y0 + 5.5, f"Halaman {page}/{of}   |   02-10-2026", fontsize=6.4, va="center")
    ax.text(x0 + 3, y0 - 3, "Digambar: ........................   NIM: ........................   Toleransi umum: +-0,2 mm (FDM)", fontsize=5.6, va="center")


def hline(ax, x0, x1, y, **kw):
    ax.plot([x0, x1], [y, y], lw=kw.pop("lw", LW), color=kw.pop("c", "k"), solid_capstyle="butt", zorder=8, **kw)


def vline(ax, x, y0, y1, **kw):
    ax.plot([x, x], [y0, y1], lw=kw.pop("lw", LW), color=kw.pop("c", "k"), solid_capstyle="butt", zorder=8, **kw)


def arrow(ax, p0, p1, style="<|-|>"):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle=style, lw=0.45, color="k", mutation_scale=5, shrinkA=0, shrinkB=0), zorder=9)


def hdim(ax, x0, x1, yl, yf0, yf1, text, small=False, fs=FS):
    s = 1 if yl > yf0 else -1
    vline(ax, x0, yf0 + s * 0.8, yl + s * 1.2); vline(ax, x1, yf1 + s * 0.8, yl + s * 1.2)
    xa, xb = min(x0, x1), max(x0, x1)
    if small or abs(x1 - x0) < 9:
        arrow(ax, (xa - 4, yl), (xa, yl), "-|>"); arrow(ax, (xb + 4, yl), (xb, yl), "-|>")
        hline(ax, xa - 4, xb + 4, yl)
        ax.text(xb + 5, yl + 0.8, text, fontsize=fs, ha="left", va="bottom", zorder=9)
    else:
        arrow(ax, (xa, yl), (xb, yl))
        ax.text((xa + xb) / 2, yl + 0.8, text, fontsize=fs, ha="center", va="bottom", zorder=9)


def vdim(ax, xl, y0, y1, xf0, xf1, text, fs=FS, side="left"):
    s = 1 if xl > xf0 else -1
    hline(ax, xf0 + s * 0.8, xl + s * 1.2, y0); hline(ax, xf1 + s * 0.8, xl + s * 1.2, y1)
    ya, yb = min(y0, y1), max(y0, y1)
    if abs(y1 - y0) < 8:
        arrow(ax, (xl, ya - 4), (xl, ya), "-|>"); arrow(ax, (xl, yb + 4), (xl, yb), "-|>")
        vline(ax, xl, ya - 4, yb + 4)
        ax.text(xl + (0.9 if side == "right" else -0.9), yb + 5.5, text, fontsize=fs, rotation=90, ha="left" if side == "right" else "right", va="bottom", zorder=9)
    else:
        arrow(ax, (xl, ya), (xl, yb))
        ax.text(xl + (-0.8 if side == "left" else 0.8), (ya + yb) / 2, text, fontsize=fs, rotation=90, ha="right" if side == "left" else "left", va="center", zorder=9)


def leader(ax, p_from, p_text, text, ha="left", fs=FS):
    ax.plot([p_from[0], p_text[0]], [p_from[1], p_text[1]], lw=0.35, color="k", zorder=8)
    ax.plot([p_from[0]], [p_from[1]], marker="o", ms=1.3, color="k", zorder=9)
    ax.text(p_text[0] + (0.8 if ha == "left" else -0.8), p_text[1], text, fontsize=fs, ha=ha, va="center", zorder=9)


def center_cross(ax, x, y, r=3.5):
    for dx, dy in ((r, 0), (0, r)):
        ax.plot([x - dx, x + dx], [y - dy, y + dy], lw=0.3, color="#c00000", dashes=(6, 1.5, 1, 1.5), zorder=7)


# ---------------------------------------------------------------- potongan
def to2d(plane, c):
    if plane == "XZ":
        return np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, -c], [0, 0, 0, 1]], float)
    if plane == "YZ":
        return np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, -c], [0, 0, 0, 1]], float)
    return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -c], [0, 0, 0, 1]], float)


NORMAL = {"XZ": [0, 1, 0], "YZ": [1, 0, 0], "XY": [0, 0, 1]}


def polys(mesh, plane, c):
    sec = mesh.section(plane_origin=[c if plane == "YZ" else 0, c if plane == "XZ" else 0, c if plane == "XY" else 0], plane_normal=NORMAL[plane])
    if sec is None:
        return []
    p, _ = sec.to_planar(to_2D=to2d(plane, c))
    return list(p.polygons_full)


def draw_poly(ax, poly, org, fc, ec="k", lw=0.5, hatch=None, z=4, alpha=1.0):
    def path_of(pg):
        verts, codes = [], []
        for ring in [pg.exterior] + list(pg.interiors):
            pts = np.asarray(ring.coords)
            xy = np.c_[org[0] + pts[:, 0] * SC, org[1] + pts[:, 1] * SC]
            verts += list(xy); codes += [Path.MOVETO] + [Path.LINETO] * (len(xy) - 2) + [Path.CLOSEPOLY]
        return Path(verts, codes)
    geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
    for g in geoms:
        ax.add_patch(PathPatch(path_of(g), fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=z, alpha=alpha))


def draw_section(ax, plane, c, org, items):
    for key, mesh, fc, hatch, z in items:
        for pg in polys(mesh, plane, c):
            draw_poly(ax, pg, org, fc, hatch=hatch, z=z)


def P(org, u, v):
    return (org[0] + u * SC, org[1] + v * SC)


COLS = dict(A=("#d5d8df", "////"), B=("#ecd9b0", "\\\\\\\\"), C=("#9db6e0", "xxxx"))


def items_all():
    return [("A", M["A"], COLS["A"][0], COLS["A"][1], 4), ("B", M["B"], COLS["B"][0], COLS["B"][1], 4), ("C", M["C"], COLS["C"][0], COLS["C"][1], 4),
            ("board", GH["Modul_HW605"], "#222222", None, 6), ("cable", GH["Kabel_4_inti"], "#d04040", None, 6), ("wire", GH["Kawat_bundel"], "#e0b020", None, 6),
            ("spring", GH["Pegas"], "#aaaaaa", None, 5), ("screw", GH["Sekrup_engsel"], "#101010", None, 6)]


# =============================================================== HALAMAN 1
def clip_cable():
    cab = GH["Kabel_4_inti"]
    try:
        return cab.slice_plane([XL + 3.0, 0, 0], [-1, 0, 0], cap=True)
    except Exception:
        return cab


GH["Kabel_4_inti"] = clip_cable()


def page1():
    fig, ax = new_sheet()
    # ---- A-A: potongan memanjang y=0
    org = (20, 200)
    xm = lambda x: org[0] + x * SC
    zm = lambda z: org[1] + z * SC
    ax.text(org[0], zm(ZT) + 21, "POTONGAN A-A (y = 0): melalui sensor, engsel, dudukan pegas, dan leher kabel", fontsize=7.4, fontweight="bold")
    draw_section(ax, "XZ", 0.0, org, items_all())
    center_cross(ax, xm(XP), zm(0.0), 3.0)
    yb_ = zm(ZT)
    hdim(ax, xm(0), xm(XL), yb_ + 12, yb_, yb_, fmt(XL))
    hdim(ax, xm(0), xm(XP), yb_ + 6.5, yb_, yb_, fmt(XP) + "  sumbu engsel")
    hdim(ax, xm(0), xm(XS), yb_ + 1.5, yb_, yb_, fmt(XS) + "  pusat sensor", small=False)
    yo = zm(ZO)
    hdim(ax, xm(0), xm(S["X_STOP"][0]), yo - 6, yo, yo, fmt(S["X_STOP"][0]) + "  panjang rahang bebas")
    hdim(ax, xm(S["X_STOP"][0]), xm(S["X_STOP"][1]), yo - 12, yo, yo, fmt(S["X_STOP"][1] - S["X_STOP"][0]), small=True)
    hdim(ax, xm(S["seats_x"][0]), xm(S["seats_x"][1]), yo - 6, yo, yo, fmt(S["seats_ls"][1] - S["seats_ls"][0]), small=True)
    xr = xm(XL)
    vdim(ax, xr + 8, zm(ZO), zm(ZT), xr, xr, fmt(ZT - ZO), side="right")
    vdim(ax, xr + 18, zm(-ZP), zm(ZP), xr, xr, fmt(2 * ZP) + " bantalan", side="right")
    vdim(ax, xr + 28, zm(S["BLK"][0]), zm(S["BLK"][1]), xr, xr, fmt(S["BLK"][1] - S["BLK"][0]) + " ekor", side="right")
    leader(ax, (xm(XS - 2.0), zm(ZL + 6.2)), (xm(XS) - 16, zm(-2.0)), f"jendela sensor {fmt(S['board']['sens_l'] + 1.2)} x {fmt(S['board']['sens_w'] + 1.6)}", ha="right")
    leader(ax, (xm(XS - 3.0), zm(ZL + 1.0)), (xm(XS) - 16, zm(-5.5)), f"modul HW-605 {fmt(S['board']['l'])} x {fmt(S['board']['w'])} x {fmt(S['board']['t'])}", ha="right")
    leader(ax, (xm(XP), zm(1.0)), (xm(XP) + 2, zm(-9.0)), f"lubang engsel {fmt(S['hinge_hole'])}", ha="left")
    leader(ax, (xm(S["seats_x"][1]), zm(S["BLK"][0] + 1.0)), (xm(S["seats_x"][1]) + 6, zm(ZT - 1.0) + 1.0), "pin dudukan pegas", ha="left") if False else leader(ax, (xm(S["seats_x"][1]), zm(S["BLK"][0] + 1.0)), (xm(52.0), zm(-ZP + 3.0)), "pin dudukan pegas", ha="right")
    leader(ax, (xm(65.5), zm(S["z_ax"])), (xm(58.0), zm(ZO) - 19), f"leher kabel {fmt(S['cable_d'] + 0.3)}", ha="right")
    leader(ax, (xm(31.0), zm(-ZP + 2.1)), (xm(31.0) - 2, zm(2.0)), "bahu penahan ujung jari", ha="right")
    ax.text(20, 11, "Hatch: abu = A (rahang bawah), krem = B (rahang atas), biru = C (tutup). Hitam = modul/sekrup, merah = kabel, kuning = kawat, abu muda = pegas.", fontsize=5.0)

    # ---- B-B: potongan y = -8.4
    org2 = (20, 127)
    xm2 = lambda x: org2[0] + x * SC
    zm2 = lambda z: org2[1] + z * SC
    ax.text(org2[0], zm2(ZT) + 5, "POTONGAN B-B (y = -8,4): jalur kawat dan kabel di bawah blok samping", fontsize=7.4, fontweight="bold")
    draw_section(ax, "XZ", S["route"][2][1], org2, items_all())
    vdim(ax, xm2(XL) + 8, zm2(ZL), zm2(S["z_c2"]), xm2(XL), xm2(XL), fmt(S["cab_h"]) + " tinggi", side="right")
    hdim(ax, xm2(37.0), xm2(52.0), zm2(ZO) - 6, zm2(ZO), zm2(ZO), "15,0 lintasan samping")
    hdim(ax, xm2(S["lid"]["x0"]), xm2(S["lid"]["x1"]), zm2(ZO) - 12, zm2(ZO), zm2(ZO), fmt(S["lid"]["x1"] - S["lid"]["x0"]) + " tutup C")
    leader(ax, (xm2(61.0), zm2(ZL + 1.0)), (xm2(61.0) + 3, zm2(-3.5)), "rib penjepit kabel", ha="left")

    # ---- C-C: potongan datar z = Z_L + 0.9
    org3 = (20, 40)
    cz = ZL + 0.9
    xm3 = lambda x: org3[0] + x * SC
    ym3 = lambda y: org3[1] + y * SC
    ax.text(org3[0], ym3(W / 2) + 12, f"POTONGAN C-C (z = {fmt(cz)}): tata letak rongga, dilihat dari atas", fontsize=7.4, fontweight="bold")
    for key, mesh, fc, hatch, z in [("A", M["A"], COLS["A"][0], COLS["A"][1], 4), ("C", M["C"], COLS["C"][0], COLS["C"][1], 3),
                                    ("board", GH["Modul_HW605"], "#222222", None, 6), ("wire", GH["Kawat_bundel"], "#e0b020", None, 6), ("cable", GH["Kabel_4_inti"], "#d04040", None, 6)]:
        for pg in polys(mesh, "XY", cz):
            draw_poly(ax, pg, org3, fc, hatch=hatch, z=z)
    hdim(ax, xm3(XS - 7.0), xm3(XS + 7.0), ym3(W / 2) + 4.5, ym3(W / 2), ym3(W / 2), fmt(S["board"]["l"] + 0.4) + " kantong")
    vdim(ax, xm3(0) - 6, ym3(-9.2), ym3(9.2), xm3(0), xm3(0), fmt(S["board"]["w"] + 0.4), side="left")
    vdim(ax, xm3(XL) + 8, ym3(-W / 2), ym3(W / 2), xm3(XL), xm3(XL), fmt(W), side="right")
    leader(ax, (xm3(44.0), ym3(-8.4)), (xm3(40.0), ym3(-W / 2) - 5), f"lintasan samping, lebar {fmt(S['cab_w'])}", ha="center")
    leader(ax, (xm3(29.0), ym3(0)), (xm3(29.0) + 10, ym3(W / 2) + 4.5), "zona solder 10,4 x 5,1", ha="left")

    # ---- tampak atas B
    org4 = (200, 238)
    xm4 = lambda x: org4[0] + x * SC
    ym4 = lambda y: org4[1] + y * SC
    ax.text(org4[0], ym4(W / 2) + 12, "TAMPAK ATAS (rahang B)", fontsize=7.4, fontweight="bold")
    ax.add_patch(Rectangle((xm4(0), ym4(-W / 2)), XL * SC, W * SC, fc="#f4ecd8", ec="k", lw=0.6, zorder=3))
    center_cross(ax, xm4(XP), ym4(0), 4)
    for xs_ in S["seats_x"]:
        ax.add_patch(Circle((xm4(xs_), ym4(0)), S["pocket_d"] / 2 * SC, fc="none", ec="#555", lw=0.5, ls=(0, (3, 1.5)), zorder=5))
    ax.add_patch(Circle((xm4(XS), ym4(0)), 1.0, fc="#222", ec="none", zorder=6))
    ax.text(xm4(XS) + 2.5, ym4(0) - 1.0, "pusat sensor", fontsize=5.2)
    hdim(ax, xm4(0), xm4(XL), ym4(W / 2) + 4.5, ym4(W / 2), ym4(W / 2), fmt(XL))
    vdim(ax, xm4(0) - 6, ym4(-W / 2), ym4(W / 2), xm4(0), xm4(0), fmt(W), side="left")
    hdim(ax, xm4(XP), xm4(S["seats_x"][0]), ym4(-W / 2) - 5, ym4(-W / 2), ym4(-W / 2), "9,0", small=True)
    hdim(ax, xm4(XP), xm4(S["seats_x"][1]), ym4(-W / 2) - 10, ym4(-W / 2), ym4(-W / 2), "14,0 (dudukan 2)")
    leader(ax, (xm4(S["seats_x"][1]), ym4(0) + 2.5), (xm4(S["seats_x"][1]) - 2, ym4(W / 2) + 12), f"kantong pegas {fmt(S['pocket_d'])} (garis putus)", ha="right", fs=5.4)
    ax.text(xm4(6), ym4(0) + 6.0, "permukaan atas rata, tepi chamfer 1,4 x 45 derajat", fontsize=5.6)

    # ---- potongan melintang 4 buah (2 x 2)
    cells = [(200, 142, 22.0, "D-D  x = 22 (sensor)"), (300, 142, XP, "E-E  x = 46 (engsel)"),
             (200, 72, 57.5, "F-F  x = 57,5 (dudukan pegas)"), (300, 72, 63.0, "G-G  x = 63 (leher kabel)")]
    for ox, oy, xc, ttl in cells:
        orgc = (ox + 36, oy + 13.45 * SC + 0)
        ym = lambda y, o=orgc: o[0] + y * SC
        zm_ = lambda z, o=orgc: o[1] + z * SC
        ax.text(ox + 4, zm_(ZT) + 8.5, ttl, fontsize=6.8, fontweight="bold")
        draw_section(ax, "YZ", xc, orgc, items_all())
        hdim(ax, ym(-W / 2), ym(W / 2), zm_(ZT) + 2.5, zm_(ZT), zm_(ZT), fmt(W))
        vdim(ax, ym(-W / 2) - 5, zm_(ZO), zm_(ZT), ym(-W / 2), ym(-W / 2), fmt(ZT - ZO), side="left")
        if abs(xc - 22.0) < 0.1:
            hdim(ax, ym(-S["cradle"]["hw"]), ym(S["cradle"]["hw"]), zm_(ZO) - 5, zm_(ZO), zm_(ZO), fmt(2 * S["cradle"]["hw"]) + "  lekuk R" + fmt(S["cradle"]["R"]))
    title_block(ax, 1, 2, "Potongan, tampak atas, dimensi utama  [klip v2]")
    return fig


# =============================================================== HALAMAN 2
BOM = [
    (1, "A  Rahang bawah (cetak)", 1, "PLA/PETG. Lekuk jari R15,6; jendela sensor; kantong modul; terowongan kawat/kabel; leher kabel; lug engsel; 2 pin dudukan pegas."),
    (2, "B  Rahang atas (cetak)", 1, "PLA/PETG. Tab engsel tengah; lekuk jari; dinding penahan ujung jari; 2 kantong pegas; permukaan atas rata."),
    (3, "C  Tutup bawah (cetak)", 1, "Menutup modul dan kabel dari bawah (tekan, 8 rusuk gesek); 2 rib penjepit kabel; tahan dengan tekanan, mudah dicungkil di takik depan."),
    (4, "D  Ring shim 1 mm (cetak)", 4, "Dipasang di bawah pegas (di atas pin) untuk menambah gaya jepit. Tiap shim menambah sekitar 0,3 N (dudukan 1) atau 0,6 N (dudukan 2) untuk pegas 1 N/mm."),
    (5, "Modul MAX30102 HW-605", 1, "PCB 18,0 x 13,5 mm. Kawat disolder pada 4 pad tepi belakang sebelum modul dipasang dari bawah."),
    (6, "Kabel 4 inti AWG", 1, "Diameter luar 4,0 mm (ubah CABLE_D di make_clip.py bila berbeda). Dijepit tutup C + jalur berkelok."),
    (7, "Pegas tekan baja", 1, "OD 4,2 / kawat 0,45 / panjang bebas 12 mm (perkiraan dari foto). Dipasang di dudukan 1 atau 2."),
    (8, "Sekrup engsel M3 x 14", 1, "Mengulir sendiri di lug (pilot 2,6 mm); kepala di sisi +Y. Pakai sekrup yang Anda punya (3 mm)."),
    (9, "Busa/double tape 1 mm", 1, "Opsional: bantalan di rahang B dan 0,5 mm di bawah modul untuk menaikkan sensor."),
]


def page2():
    fig, ax = new_sheet()
    ax.text(210, 287.5, "Klip sensor PPG MAX30102: tampak eksplode, perakitan, dan gaya jepit", fontsize=12, fontweight="bold", ha="center", va="center")
    # render eksplode
    p = os.path.join(REN, "klip_meledak.png")
    im = Image.open(p).convert("RGBA")
    arr = np.asarray(im)
    a = arr[..., 3]
    ys, xs = np.where(a > 8)
    box = (max(xs.min() - 12, 0), max(ys.min() - 12, 0), min(xs.max() + 12, im.width), min(ys.max() + 12, im.height))
    crop = im.crop(box)
    rx, ry, rw, rh = 8, 108, 250, 172
    sc_ = min(rw / crop.width, rh / crop.height)
    wmm, hmm = crop.width * sc_, crop.height * sc_
    x0, y0 = rx + (rw - wmm) / 2, ry + (rh - hmm) / 2
    ax.imshow(np.asarray(crop), extent=(x0, x0 + wmm, y0, y0 + hmm), origin="upper", zorder=2, interpolation="lanczos")
    anc = json.load(open(os.path.join(REN, "anchors_meledak.json")))
    W_, H_ = im.size
    pt = lambda n: (x0 + (anc[n][0] * W_ - box[0]) * sc_, y0 + hmm - ((1 - anc[n][1]) * H_ - box[1]) * sc_)
    order = [("A", 1), ("B", 2), ("C", 3), ("D", 4), ("board", 5), ("cable", 6), ("spring", 7), ("screw", 8), ("foam", 9)]
    cx, cy = x0 + wmm / 2, y0 + hmm / 2
    placed = []
    for key, num in order:
        a_ = np.array(pt(key)); v = a_ - np.array([cx, cy]); n_ = np.linalg.norm(v); v = v / n_ if n_ > 1e-6 else np.array([0, 1.0])
        b_ = a_ + v * 17
        for q in placed:
            while np.linalg.norm(b_ - q) < 9.5:
                b_ = b_ + np.array([-v[1], v[0]]) * 2.0
        b_[0] = min(max(b_[0], rx + 5), rx + rw - 5); b_[1] = min(max(b_[1], ry + 5), ry + rh - 5)
        placed.append(b_)
        ax.plot([a_[0], b_[0]], [a_[1], b_[1]], lw=0.5, color="k", zorder=6)
        ax.plot([a_[0]], [a_[1]], marker="o", ms=2.2, color="k", zorder=7)
        ax.add_patch(Circle(b_, 3.7, fc="white", ec="k", lw=0.8, zorder=8))
        ax.text(b_[0], b_[1], str(num), fontsize=8, ha="center", va="center", fontweight="bold", zorder=9)
    ax.text(rx + 2, ry + rh + 1.5, "A. TAMPAK EKSPLODE (urutan perakitan: C dan modul dari bawah, pegas dan B dari atas)", fontsize=7.4, fontweight="bold")

    # tabel BOM
    bx, by = 8, 100
    ax.text(bx, by + 2.5, "DAFTAR KOMPONEN", fontsize=7.6, fontweight="bold")
    cw = [10, 52, 8, 180]
    ax.add_patch(Rectangle((bx, by - 5.2 * (len(BOM) + 1) + 0), sum(cw), 5.2 * (len(BOM) + 1), fill=False, lw=0.6, ec="k"))
    hdr = ("ITEM", "NAMA", "JML", "KETERANGAN")
    xx = bx
    for c_, t_ in zip(cw, hdr):
        ax.text(xx + 1, by - 2.6, t_, fontsize=5.8, fontweight="bold", va="center"); xx += c_
    ax.plot([bx, bx + sum(cw)], [by - 5.2, by - 5.2], lw=0.5, color="k")
    for i, row in enumerate(BOM):
        yy = by - 5.2 * (i + 1) - 2.6
        xx = bx
        for c_, t_ in zip(cw, (str(row[0]), row[1], str(row[2]), row[3])):
            ax.text(xx + 1, yy, t_, fontsize=5.3 if c_ > 100 else 5.8, va="center"); xx += c_
        ax.plot([bx, bx + sum(cw)], [yy - 2.6, yy - 2.6], lw=0.3, color="k")
    xx = bx
    for c_ in cw[:-1]:
        xx += c_
        ax.plot([xx, xx], [by - 5.2 * (len(BOM) + 1), by], lw=0.3, color="k")

    # verifikasi dan data yang perlu diukur (kiri bawah)
    ax.add_patch(Rectangle((8, 8), 250, 38, fill=False, lw=0.6, ec="k", zorder=2))
    ax.text(11, 42.5, "H. HASIL VERIFIKASI OTOMATIS (verify_clip.py: SEMUA LOLOS)", fontsize=7.0, fontweight="bold")
    ver = [
        "Mesh A, B, C, D rapat (watertight), satu badan; tanpa fitur < 0,9 mm. Rahang A dan B tidak saling menembus pada posisi nominal (0 mm3).",
        f"Gerak engsel tanpa tabrakan dari theta = {KIN['free_close'] + 1:.0f} s.d. +{KIN['free_open'] - 1:.0f} derajat (jarak bantalan sekitar 12 s.d. 22 mm). Modul, kawat, kabel 4,0 mm, sekrup muat tanpa tabrakan.",
        "Tutup C hanya menekan lewat 8 rusuk gesek (7,9 mm3); rib penjepit menekan jaket kabel 0,3 mm. Pegas tetap tertekan pada seluruh rentang gerak.",
    ]
    for i, t in enumerate(ver):
        ax.text(11, 38.0 - i * 4.0, t, fontsize=5.3, va="center")
    ax.text(11, 25.0, "I. UKUR DAN KIRIM UNTUK PENYESUAIAN AKHIR (parameter di make_clip.py)", fontsize=7.0, fontweight="bold")
    need = [
        "Pegas: diameter luar, diameter kawat, panjang bebas, jumlah lilitan aktif (atau kekakuan k bila tahu). Sekrup engsel: diameter ulir dan panjang.",
        "Kabel 4 inti: diameter luar jaket (ubah CABLE_D). Modul HW-605: panjang x lebar x tebal PCB dan posisi sensor dari tepi (jangka sorong).",
    ]
    for i, t in enumerate(need):
        ax.text(11, 20.5 - i * 4.0, t, fontsize=5.3, va="center")

    # langkah perakitan (kanan)
    px, py = 268, 281
    ax.add_patch(Rectangle((px - 3, 117), 149, 168, fill=False, lw=0.6, ec="k", zorder=2))
    ax.text(px, py - 2, "B. LANGKAH PERAKITAN (kabel tidak lepas, modul tetap bisa disolder)", fontsize=7.4, fontweight="bold")
    steps = [
        "1. Cetak A, B, C, D sesuai orientasi pada file *_siap_cetak.stl (A: sisi bawah di meja; B: sisi atas di meja; C dan D: rata).",
        "2. Lewatkan kabel 4 inti dari BELAKANG melalui leher A (lubang 4,3 mm) sampai keluar di lubang dasar. Kupas jaket 28 mm.",
        "3. Solder 4 kawat ke pad modul (pitch 2,54) dari sisi komponen, tinggi solder maks. 1,5 mm. Isolasi dengan heat-shrink kecil.",
        "4. Rekatkan double tape 0,5 mm di PCB bagian bawah (sensor jadi hampir rata dengan bantalan), lalu masukkan modul dari bawah ke",
        "    kantong, sensor menghadap jendela. Jaket kabel diletakkan di lintasan samping (berkelok), jangan menarik kawat.",
        "5. Pasang tutup C dari bawah (tekan sampai rata). Dua rib di tutup menjepit jaket kabel; leher sempit 4,3 mm mencegah tercabut.",
        "6. Pasang pegas pada pin dudukan 1 (lembut) atau 2 (kuat); tambah ring shim D bila perlu.",
        "7. Letakkan B di atas A (tab B di antara 2 lug), masukkan sekrup M3 dari sisi +Y; jangan terlalu kencang agar engsel berputar bebas.",
        "8. Tempel busa 1 mm di lekuk B. Uji: jari 14 mm harus menyentuh sensor dengan gaya sekitar 2 s.d. 3 N tanpa memucatkan ujung jari.",
    ]
    for i, t in enumerate(steps):
        ax.text(px, py - 9 - i * 4.7, t, fontsize=5.5, va="center")
    # gaya pegas
    ax.text(px, 218, "C. GAYA JEPIT PADA JARI (N), kondisi nominal: jari 14 mm + busa 1 mm", fontsize=7.0, fontweight="bold")
    ft = KIN["force_table"]
    ax.text(px, 213, f"Hitungan memakai panjang bebas pegas {fmt(KIN['L0'])} mm. Ukur pegas Anda (kekakuan k) lalu cocokkan baris tabel.", fontsize=5.4)
    cols_x = [px, px + 22, px + 52, px + 82]
    hdrs = ["k (N/mm)", "dud.1: 0 / 1 / 2 shim", "dud.2: 0 / 1 / 2 shim", "saran"]
    for cxx, h_ in zip(cols_x, hdrs):
        ax.text(cxx, 207.5, h_, fontsize=5.8, fontweight="bold")
    ax.plot([px, px + 140], [205.5, 205.5], lw=0.4, color="k")
    adv = {"0.4": "dud.2 + 2 shim", "0.7": "dud.2 + 1 shim", "1.0": "dud.1 + 2 shim / dud.2", "1.3": "dud.1 + 1 shim", "1.6": "dud.1 tanpa shim", "2.0": "dud.1 tanpa shim (kuat)"}
    for i, (k_, v) in enumerate(ft.items()):
        yy = 201.5 - i * 4.4
        ax.text(cols_x[0], yy, f"{float(k_):.1f}", fontsize=5.8)
        ax.text(cols_x[1], yy, "  /  ".join(f"{x:.1f}" for x in v[0]), fontsize=5.8)
        ax.text(cols_x[2], yy, "  /  ".join(f"{x:.1f}" for x in v[1]), fontsize=5.8)
        ax.text(cols_x[3], yy, adv.get(k_, ""), fontsize=5.4)
    ax.text(px, 201.5 - len(ft) * 4.4 - 1.5, "Sasaran nyaman untuk PPG ujung jari: 1,5 s.d. 3 N. Terlalu kuat memucatkan jari dan melemahkan sinyal AC.", fontsize=5.4)
    # cetak
    ax.text(px, 168, "D. PENGATURAN CETAK", fontsize=7.0, fontweight="bold")
    prt = [
        "Bahan PLA atau PETG (hitam atau abu gelap lebih baik untuk menahan cahaya sekitar). Layer 0,2 mm, 3 perimeter, infill 25 %.",
        "A: sisi bawah (alur tutup) di meja. Tanpa support; langit-langit rongga dijembatani (maks. bentang 14 mm). B: sisi atas di meja, tanpa support.",
        "C dan D: rata. Toleransi lubang sudah dikompensasi. Jika tutup C terlalu ketat, amplas rusuk gesek di sisi C; jika longgar, tambah selotip tipis.",
        f"Gerak engsel tervalidasi {KIN['free_close'] + 1:.0f} s.d. +{KIN['free_open'] - 1:.0f} derajat (jarak bantalan sekitar 12 s.d. 22 mm). Pegas tetap tertekan di seluruh rentang.",
    ]
    for i, t in enumerate(prt):
        ax.text(px, 163 - i * 4.7, t, fontsize=5.4, va="center")
    ax.text(px, 140, "E. PERBAIKAN DIBANDING KLIP LAMA", fontsize=7.0, fontweight="bold")
    fix = [
        "- Kabel: terowongan tertutup + leher sempit + jalur S + rib penjepit di tutup (tarikan ke belakang bertumpu pada rumah, bukan pada solder).",
        "- Modul: dipasang dari bawah, permukaan jari halus dan tertutup (tanpa PCB terbuka); sensor di jendela 0,3 s.d. 0,8 mm dari permukaan.",
        "- Penjepit: dudukan pegas (pin + kantong) mencegah pegas miring; dua posisi dudukan + shim untuk atur gaya sampai 3x.",
        "- Nyaman: lekuk jari R15,6, mulut dan tepi membulat, bahu penahan ujung jari, bantalan busa; permukaan atas rata.",
    ]
    for i, t in enumerate(fix):
        ax.text(px, 135 - i * 4.7, t, fontsize=5.4, va="center")
    # gambar tambahan: klip dipakai di jari, dan tampak bawah tanpa tutup
    for fn, (xx, yy, ww, ttl) in (("klip_pakai.png", (268, 15, 70, "F. KLIP DIPASANG PADA JARI"), ),
                                  ("klip_bawah.png", (342, 15, 70, "G. TAMPAK BAWAH TANPA TUTUP"))):
        p = os.path.join(REN, fn)
        if not os.path.exists(p):
            continue
        im2 = Image.open(p).convert("RGBA"); arr2 = np.asarray(im2); a2 = arr2[..., 3]
        yy2, xx2 = np.where(a2 > 8)
        c2 = im2.crop((max(xx2.min() - 8, 0), max(yy2.min() - 8, 0), min(xx2.max() + 8, im2.width), min(yy2.max() + 8, im2.height)))
        hh = ww * c2.height / c2.width
        ax.imshow(np.asarray(c2), extent=(xx, xx + ww, 70 - hh / 2 + 0, 70 + hh / 2), zorder=2)
        ax.text(xx, 70 + hh / 2 + 3, ttl, fontsize=6.4, fontweight="bold")
    return fig


if __name__ == "__main__":
    f1 = page1()
    f2 = page2()
    with PdfPages(os.path.join(OUTD, "Gambar_Teknik_Klip_PPG_A3.pdf")) as pdf:
        pdf.savefig(f1, dpi=300); pdf.savefig(f2, dpi=300)
    f1.savefig(os.path.join(OUTD, "Gambar_Teknik_Klip_Hal1_A3.png"), dpi=200)
    f2.savefig(os.path.join(OUTD, "Gambar_Teknik_Klip_Hal2_A3.png"), dpi=200)
    print("OK")
