"""Halaman 3 (potongan) dan 4 (penahan sekrup) gambar teknik cover FINAL. Dipanggil dari gt_cover.py: gt_extra.make(CASE, S, OUTD, PREV)."""
import os, sys, json, glob, math, textwrap
import numpy as np
import trimesh
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MPoly, Circle
from shapely.geometry import Polygon as SPoly
from shapely.ops import unary_union
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import ket
from common import hline, vline, hdim, vdim, leader, f1, new_sheet

HERE = os.path.dirname(os.path.abspath(__file__))
NPAGE = 4


def sg(v):
    return ("+" if v > 0 else "-") + f1(v)


def load(p):
    m = trimesh.load(p); m.merge_vertices(); return m


def section_polys(m, origin, normal, ax_idx):
    """irisan mesh dengan bidang -> (daftar poligon shapely terisi, daftar polyline) pada koordinat bidang (sumbu ax_idx)."""
    try:
        sec = m.section(plane_origin=origin, plane_normal=normal)
    except Exception:
        return [], []
    if sec is None: return [], []
    loops = [np.asarray(l)[:, list(ax_idx)] for l in sec.discrete]
    polys = []
    if m.is_watertight:
        acc = None
        for lp in loops:
            if len(lp) < 4: continue
            pg = SPoly(lp)
            pg = pg if pg.is_valid else pg.buffer(0)
            acc = pg if acc is None else acc.symmetric_difference(pg)
        if acc is not None and not acc.is_empty:
            polys = list(acc.geoms) if hasattr(acc, "geoms") else [acc]
    return polys, loops


class Panel:
    def __init__(self, ax, ox, oy, u0, v0, k, win=None):
        self.ax, self.ox, self.oy, self.u0, self.v0, self.k = ax, ox, oy, u0, v0, k
        self.win = win                      # (u_min, u_max, v_min, v_max): jendela potongan (di luar jendela dipotong)

    def clip(self, art):
        if self.win:
            a, b, c, d = self.win
            x0, y0 = self.P(a, c)
            r = Rectangle((x0, y0), (b - a) * self.k, (d - c) * self.k, transform=self.ax.transData)
            art.set_clip_path(r)
        return art

    def P(self, u, v): return self.ox + (u - self.u0) * self.k, self.oy + (v - self.v0) * self.k

    def poly(self, pg, fc, ec="k", lw=0.5, hatch=None, z=3, alpha=1.0):
        for g in ([pg] if pg.geom_type == "Polygon" else list(pg.geoms)):
            if g.is_empty: continue
            ext = [self.P(u, v) for u, v in g.exterior.coords]
            self.clip(self.ax.add_patch(MPoly(ext, closed=True, fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=z, alpha=alpha)))
            for h in g.interiors:
                self.clip(self.ax.add_patch(MPoly([self.P(u, v) for u, v in h.coords], closed=True, fc="white", ec=ec, lw=lw, zorder=z + 0.1)))

    def line(self, pts, col="k", lw=0.6, z=3, ls="-"):
        xy = np.array([self.P(u, v) for u, v in pts])
        for l_ in self.ax.plot(xy[:, 0], xy[:, 1], color=col, lw=lw, zorder=z, ls=ls): self.clip(l_)


def make(CASE, S, OUTD, PREV):
    R = os.path.join(CASE, "_ref"); ASM = os.path.join(R, "asm")
    BAG = os.path.join(os.path.dirname(PREV.rstrip("/")), "bagian") if PREV else None
    BAG = os.path.join(CASE, "..", "FINAL_TA", "_render", "bagian")
    shell, plate, pen = load(os.path.join(R, "shell_design.stl")), load(os.path.join(R, "plate_design.stl")), load(os.path.join(R, "penahan_design.stl"))
    scr = load(os.path.join(R, "ref_Sekrup_M3x8.stl"))
    comps = []                                                     # (nama, mesh, warna isi, warna garis)
    for f in sorted(glob.glob(os.path.join(ASM, "*.stl"))):
        n = os.path.basename(f)[:-4]; g = n.split("__")[0]
        if g in ("baterai", "kabel_el", "ppg", "sekrup", "saklar", "gland", "boost"): continue
        comps.append((n, load(f), g))
    sw = S["switch"]; gl = S["gland"]; jk = S["jack"]; HY = S["outer_y"][1]; YB = S["outer_y"][0]
    parts = {os.path.basename(f)[:-4]: load(f) for f in glob.glob(os.path.join(BAG, "*.stl"))}
    ZB, ZS, ZT = S["z"]["plate_bottom"], S["z"]["split"], S["z"]["top"]

    COL = dict(pcb="#2e9a55", tft_pcb="#c53030", tft_glass="#15151c", standoff="#d8b24a", esp32="#444444", ad8232="#c53030", boost="#3b63c9")

    def draw_section(P, origin, normal, axi, show_screws=True):
        for m, fc, hatch in ((shell, "#f1e2c8", "////"), (plate, "#b8c6de", "\\\\\\\\"), (pen, "#e8a0d0", "xxxx")):
            polys, loops = section_polys(m, origin, normal, axi)
            for pg in polys: P.poly(pg, fc, hatch=hatch, lw=0.6, z=3)
        if show_screws:
            polys, loops = section_polys(scr, origin, normal, axi)
            for pg in polys: P.poly(pg, "#9aa0a8", lw=0.5, z=5)
        for n, m, g in comps:
            col = {"tft": COL["tft_glass"] if "glass" in n else COL["tft_pcb"], "pcb": COL["pcb"], "standoff": COL["standoff"], "esp32": COL["esp32"], "ad8232": COL["ad8232"]}.get(g, "#888888")
            polys, loops = section_polys(m, origin, normal, axi)
            if polys and g in ("tft", "pcb", "standoff"):
                for pg in polys: P.poly(pg, col, lw=0.4, z=4)
            else:
                for lp in loops:
                    if len(lp) > 1: P.line(lp, col=col, lw=0.45, z=4)

    def draw_parts(P, origin, normal, axi, names, cols):
        for n, c in zip(names, cols):
            if n not in parts: continue
            polys, loops = section_polys(parts[n], origin, normal, axi)
            for pg in polys: P.poly(pg, c, lw=0.5, z=6)

    # =================================================================== HALAMAN 3: potongan
    fig, ax = new_sheet()
    k = 2.1
    # --- A-A: x = jack
    pA = Panel(ax, 100, 225, 0, 15, k, win=(-34, 34, ZB - 1, ZT + 1))
    ax.text(100, 281, "POTONGAN A-A  (x = %s)" % ("%.1f" % jk["x"]).replace(".", ","), fontsize=6.6, fontweight="bold", ha="center")
    draw_section(pA, (jk["x"], 0, 0), (1, 0, 0), (1, 2))
    # --- B-B: x = switch
    pB = Panel(ax, 310, 225, 0, 15, k, win=(-34, 34, ZB - 1, ZT + 1))
    ax.text(310, 281, "POTONGAN B-B  (x = +%s)" % f1(sw["x"]), fontsize=6.6, fontweight="bold", ha="center")
    draw_section(pB, (sw["x"], 0, 0), (1, 0, 0), (1, 2))
    draw_parts(pB, (sw["x"], 0, 0), (1, 0, 0), (1, 2), ["sw_badan", "sw_bezel", "sw_rocker", "sw_kaki0", "sw_kaki1"], ["#222222", "#3a3a3a", "#c62828", "#cccccc", "#cccccc"])
    # --- C-C: y = gland
    pC = Panel(ax, 100, 112, -52, 15, k, win=(-82, -32, ZB - 1, ZT + 1))
    ax.text(100, 166, "POTONGAN C-C  (y = %s)" % ("%.1f" % gl["y"]).replace(".", ","), fontsize=6.6, fontweight="bold", ha="center")
    draw_section(pC, (0, gl["y"], 0), (0, 1, 0), (0, 2))
    draw_parts(pC, (0, gl["y"], 0), (0, 1, 0), (0, 2), ["gl_ulir", "gl_mur", "gl_seal", "gl_kepala", "gl_tutup"], ["#f4f4f0", "#f4f4f0", "#222222", "#f4f4f0", "#f4f4f0"])
    # --- D-D: x = 23 (sekrup + penahan)
    pD = Panel(ax, 310, 112, 0, 15, k, win=(-34, 34, ZB - 1, ZT + 1))
    ax.text(310, 166, "POTONGAN D-D  (x = +23)", fontsize=6.6, fontweight="bold", ha="center")
    draw_section(pD, (23.0, 0, 0), (1, 0, 0), (1, 2))

    # ---------- dimensi A-A
    def Z(Pn, v): return Pn.P(0, v)[1]
    yw0, yw1 = S["cavity_y"][1], S["outer_y"][1]
    xa, _ = pA.P(yw0, 0); xb, _ = pA.P(yw1, 0)
    hdim(ax, xa, xb, Z(pA, ZT) + 8, Z(pA, ZT), Z(pA, ZT), "3,0", small=True)
    vdim(ax, pA.P(-31.75, 0)[0] - 8, Z(pA, ZB), Z(pA, ZT), pA.P(-31.75, 0)[0], pA.P(-31.75, 0)[0], f1(ZT - ZB), side="left")
    vdim(ax, pA.P(31.75, 0)[0] + 8, Z(pA, jk["zc"] - 3.6), Z(pA, jk["zc"] + 3.6), pA.P(31.75, 0)[0], pA.P(31.75, 0)[0], "Ø7,2", side="right")
    vdim(ax, pA.P(31.75, 0)[0] + 20, Z(pA, ZB), Z(pA, jk["zc"]), pA.P(31.75, 0)[0], pA.P(31.75, 0)[0], f1(jk["zc"] - ZB), side="right")
    leader(ax, pA.P(0, S["z"]["pcb"][1]), (pA.P(-10, 0)[0], Z(pA, 40)), "PCB utama", ha="left")
    leader(ax, pA.P(-10, 27.4), (pA.P(-30, 0)[0], Z(pA, 36)), "PCB layar + kaca", ha="left")
    leader(ax, pA.P(26.0, 3.2), (pA.P(14, 0)[0], Z(pA, -6.6)), "penahan Atas", ha="right")
    leader(ax, pA.P(0, -2), (pA.P(-14, 0)[0], Z(pA, -6.6)), "back plate 3,0", ha="right")
    # ---------- dimensi B-B
    hdim(ax, pB.P(HY - sw["panel"], 0)[0], pB.P(HY, 0)[0], Z(pB, ZT) + 8, Z(pB, ZT), Z(pB, ZT), "1,6", small=True)
    vdim(ax, pB.P(31.75, 0)[0] + 8, Z(pB, sw["zc"] - 4.55), Z(pB, sw["zc"] + 4.55), pB.P(31.75, 0)[0], pB.P(31.75, 0)[0], "9,1", side="right")
    hdim(ax, pB.P(HY - sw["panel"] - sw["depth"], 0)[0], pB.P(HY - sw["panel"], 0)[0], Z(pB, sw["zc"] - 4.5) - 10, Z(pB, sw["zc"] - 4.5), Z(pB, sw["zc"] - 4.5), "12,5")
    leader(ax, pB.P(HY + 3.0, sw["zc"]), (pB.P(HY + 8, 0)[0], Z(pB, 34)), "rocker", ha="left")
    # ---------- dimensi C-C
    xo, xi = -S["outer"][0] / 2, -S["cavity"][0] / 2
    hdim(ax, pC.P(xo, 0)[0], pC.P(xi, 0)[0], Z(pC, ZT) + 8, Z(pC, ZT), Z(pC, ZT), "3,0", small=True)
    hdim(ax, pC.P(xo - gl["out"], 0)[0], pC.P(xo, 0)[0], Z(pC, ZB) - 8, Z(pC, ZB), Z(pC, ZB), "4,8", small=True)
    vdim(ax, pC.P(-34, 0)[0] + 6, Z(pC, gl["zc"] - gl["hole"] / 2), Z(pC, gl["zc"] + gl["hole"] / 2), pC.P(-34, 0)[0], pC.P(-34, 0)[0], "Ø12,8", side="right")
    leader(ax, pC.P(xo - 6.0, gl["zc"] + 6.5), (pC.P(xo - 10, 0)[0], Z(pC, 36)), "tutup", ha="right")
    leader(ax, pC.P(xo + 2.0, gl["zc"] + 6.5), (pC.P(xo + 6, 0)[0], Z(pC, 37)), "mur", ha="left")
    # ---------- dimensi D-D
    scr_y = 25.25
    leader(ax, pD.P(scr_y, -1.0), (pD.P(8, 0)[0], Z(pD, -9)), "sekrup M3 x 8", ha="right")
    leader(ax, pD.P(26.0, 3.2), (pD.P(20, 0)[0], Z(pD, 38)), "penahan", ha="right")
    vdim(ax, pD.P(-31.75, 0)[0] - 8, Z(pD, ZB), Z(pD, ZS), pD.P(-31.75, 0)[0], pD.P(-31.75, 0)[0], "3,0", side="left")
    leader(ax, pD.P(26.0, S["z"]["pcb"][0] - 0.35), (pD.P(40, 0)[0] - 40, Z(pD, 1.5)), "celah 0,7 ke PCB", ha="left") if False else None
    zg0, zg1 = Z(pD, S["z"]["pcb"][0] - 0.7), Z(pD, S["z"]["pcb"][0])
    xg = pD.P(14.0, 0)[0]
    arrow_ = dict(arrowstyle="<|-|>", lw=0.45, color="k", mutation_scale=5, shrinkA=0, shrinkB=0)
    ax.annotate("", xy=(xg, zg1), xytext=(xg, zg0), arrowprops=arrow_, zorder=8)
    ax.text(xg - 1.2, (zg0 + zg1) / 2, "celah 0,7", fontsize=6.0, ha="right", va="center", zorder=9, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
    # kunci warna potongan (pendek); penjelasan lengkap di berkas keterangan
    for k_, (col, nm_, hat_) in enumerate((("#f1e2c8", "shell", "////"), ("#b8c6de", "back plate", "\\\\\\\\"), ("#e8a0d0", "penahan", "xxxx"), ("#2e9a55", "PCB utama", None),
                                          ("#c53030", "PCB TFT", None), ("#15151c", "kaca", None))):
        xk = 14 + k_ * 40
        ax.add_patch(Rectangle((xk, 28), 9, 6, fc=col, ec="k", lw=0.5, hatch=hat_, zorder=7))
        ax.text(xk + 11.5, 31, nm_, fontsize=6.4, va="center", zorder=7)
    ket.begin("T-3", "Gambar teknik cover: potongan A-A, B-B, C-C, D-D (skala 2,1 : 1)")
    ket.items(["A-A (x = %s mm): melalui jack AD8232 dan penahan Atas." % ("%.1f" % jk["x"]).replace(".", ","),
               "B-B (x = %s mm): melalui saklar KCD11." % f1(sw["x"]),
               "C-C (y = %s mm): melalui gland PG7 beserta mur di kantongnya." % ("%.1f" % gl["y"]).replace(".", ","),
               "D-D (x = +23 mm): melalui sekrup M3 x 8, penahan, dan plate. Celah ujung sekrup dan puncak penahan ke PCB utama 0,7 mm."], numbered=False)
    ket.sub("Warna hatch")
    ket.para("Abu-krem = shell, biru = back plate, merah muda = penahan, hijau = PCB utama, merah = PCB TFT, hitam = kaca. Garis tanpa isi = selubung ESP32 dan AD8232. "
             "Baterai tidak digambar pada potongan.")
    C.title_block(ax, "GAMBAR TEKNIK: COVER ALAT ECG + PPG", "Potongan A-A, B-B, C-C, D-D", 3, NPAGE, scale="Skala 2,1 : 1", right_line="Bahan: PETG (cetak 3D FDM)", ket="T-3")
    fig3 = fig

    # =================================================================== HALAMAN 4: penahan sekrup
    fig, ax = new_sheet()
    Pn = S["penahan"]
    cx_, cy_ = 134.0, 214.0
    k = 1.75
    ax.text(134, 287, "DENAH PENAHAN SEKRUP (tampak depan)", fontsize=6.6, fontweight="bold", ha="center")
    HXc, HYc = S["cavity"][0] / 2, S["cavity"][1] / 2
    Pd = Panel(ax, cx_, cy_, 0, 0, k)
    # rongga dan PCB (garis tipis)
    ax.add_patch(Rectangle(Pd.P(-HXc, -HYc), 2 * HXc * k, 2 * HYc * k, fc="white", ec="k", lw=1.0, zorder=2))
    pc = S["pcb"]
    ax.add_patch(Rectangle(Pd.P(pc["x0"], pc["y0"]), (pc["x1"] - pc["x0"]) * k, (pc["y1"] - pc["y0"]) * k, fc="#2e9a55", alpha=0.10, ec="#2e9a55", lw=0.6, ls="--", zorder=2))
    # lubang/port pada dinding
    ports = [("jack AD8232", jk["x"] - 3.5, jk["x"] + 3.5, HYc, HYc + 3, "#c62828"), ("saklar", sw["x"] - 7, sw["x"] + 7, HYc, HYc + 3, "#c62828"),
             ("micro-USB", S["micro"]["x"] - 6, S["micro"]["x"] + 6, -HYc - 3, -HYc, "#c62828")]
    for nm, x0, x1, y0, y1, col in ports:
        ax.add_patch(Rectangle(Pd.P(x0, y0), (x1 - x0) * k, (y1 - y0) * k, fc="#ffd0d0", ec=col, lw=0.8, zorder=3))
    uc = S["usbc"]
    ax.add_patch(Rectangle(Pd.P(-HXc - 3, uc["y"] - 5.2), 3 * k, 10.4 * k, fc="#ffd0d0", ec="#c62828", lw=0.8, zorder=3))
    ax.add_patch(Rectangle(Pd.P(-HXc - 3, gl["y"] - 6.4), 3 * k, 12.8 * k, fc="#ffd0d0", ec="#c62828", lw=0.8, zorder=3))
    ax.text(Pd.P(jk["x"], HYc + 6)[0], Pd.P(jk["x"], HYc + 6)[1], "jack AD8232", fontsize=6.0, ha="center", color="#c62828")
    ax.text(Pd.P(sw["x"] + 6, HYc + 6)[0], Pd.P(sw["x"] + 6, HYc + 6)[1], "saklar", fontsize=6.0, ha="center", color="#c62828")
    ax.text(Pd.P(S["micro"]["x"], -HYc - 7)[0], Pd.P(S["micro"]["x"], -HYc - 7)[1], "micro-USB", fontsize=6.0, ha="center", va="top", color="#c62828")
    ax.text(Pd.P(-HXc - 5, uc["y"])[0], Pd.P(-HXc - 5, uc["y"])[1], "USB-C", fontsize=6.0, ha="right", va="center", color="#c62828")
    ax.text(Pd.P(-HXc - 5, gl["y"])[0], Pd.P(-HXc - 5, gl["y"])[1], "gland PG7", fontsize=6.0, ha="right", va="center", color="#c62828")
    PC = ["#e91e8c", "#f28c0f", "#14aacc"]
    for i, pcx in enumerate(Pn["pieces"]):
        x0, x1 = pcx["x"]; y0, y1 = pcx["y"]
        ax.add_patch(Rectangle(Pd.P(x0, y0), (x1 - x0) * k, (y1 - y0) * k, fc=PC[i], ec="k", lw=0.9, alpha=0.88, zorder=5))
        ax.text(Pd.P((x0 + x1) / 2, (y0 + y1) / 2 + (0 if i == 0 else 0))[0], Pd.P(0, (y0 + y1) / 2)[1], str(i + 1), fontsize=12, fontweight="bold", color="white", ha="center", va="center", zorder=8)
        for fx in pcx["feet"]:
            sy = 25.25 * pcx["side"]
            ax.add_patch(Circle(Pd.P(fx, sy), 1.6 * k, fc="white", ec="k", lw=0.8, zorder=9))
            ax.plot([Pd.P(fx - 1.6, sy)[0], Pd.P(fx + 1.6, sy)[0]], [Pd.P(fx, sy)[1]] * 2, color="k", lw=0.4, zorder=10)
            ax.plot([Pd.P(fx, sy)[0]] * 2, [Pd.P(fx, sy - 1.6)[1], Pd.P(fx, sy + 1.6)[1]], color="k", lw=0.4, zorder=10)
    # dimensi denah
    y_top = Pd.P(0, HYc)[1]; y_bot = Pd.P(0, -HYc)[1]
    p1, p2, p3 = Pn["pieces"]
    hdim(ax, Pd.P(-HXc, 0)[0], Pd.P(p1["x"][0], 0)[0], Pd.P(0, 19.0)[1], Pd.P(0, 19.0)[1], Pd.P(0, 19.0)[1], f1(p1["x"][0] + HXc), small=False)
    hdim(ax, Pd.P(p1["x"][0], 0)[0], Pd.P(p1["x"][1], 0)[0], Pd.P(0, 19.0)[1], Pd.P(0, 19.0)[1], Pd.P(0, 19.0)[1], f1(p1["x"][1] - p1["x"][0]))
    hdim(ax, Pd.P(p1["x"][1], 0)[0], Pd.P(HXc, 0)[0], Pd.P(0, 19.0)[1], Pd.P(0, 19.0)[1], Pd.P(0, 19.0)[1], f1(HXc - p1["x"][1]))
    yb_ = Pd.P(0, -19.0)[1]
    for a, b in ((-HXc, p2["x"][0]), (p2["x"][0], p2["x"][1]), (p2["x"][1], p3["x"][0]), (p3["x"][0], p3["x"][1]), (p3["x"][1], HXc)):
        hdim(ax, Pd.P(a, 0)[0], Pd.P(b, 0)[0], yb_, yb_, yb_, f1(b - a))
    vdim(ax, Pd.P(HXc, 0)[0] + 10, Pd.P(0, p1["y"][0])[1], Pd.P(0, p1["y"][1])[1], Pd.P(HXc, 0)[0], Pd.P(HXc, 0)[0], f1(p1["y"][1] - p1["y"][0]), side="right")
    # --------- tampak samping (x-z) penahan 1 dan 2
    ax.text(318, 284, "TAMPAK SAMPING PENAHAN 1 (x-z)", fontsize=6.6, fontweight="bold", ha="center")
    ks = 2.6
    Ps = Panel(ax, 318, 252, 0, 2, ks)
    x0, x1 = p1["x"]; zb0, zb1 = p1["zbar"]
    ax.add_patch(Rectangle(Ps.P(x0, zb0), (x1 - x0) * ks, (zb1 - zb0) * ks, fc=PC[0], ec="k", lw=0.8, zorder=5, alpha=0.9))
    for fx in p1["feet"]:
        ax.add_patch(Rectangle(Ps.P(fx - Pn["w"] / 2, ZS), Pn["w"] * ks, (zb1 - ZS) * ks, fc=PC[0], ec="k", lw=0.8, zorder=5, alpha=0.9))
        ax.plot([Ps.P(fx, 0)[0]] * 2, [Ps.P(0, ZS - 1.5)[1], Ps.P(0, zb1 + 1.5)[1]], color="#c00000", lw=0.4, ls=(0, (6, 1.5, 1, 1.5)), zorder=7)
    hdim(ax, Ps.P(x0, 0)[0], Ps.P(x1, 0)[0], Ps.P(0, zb1)[1] + 10, Ps.P(0, zb1)[1], Ps.P(0, zb1)[1], f1(x1 - x0))
    vdim(ax, Ps.P(x1, 0)[0] + 8, Ps.P(0, ZS)[1], Ps.P(0, zb1)[1], Ps.P(x1, 0)[0], Ps.P(x1, 0)[0], f1(zb1 - ZS) + "", side="right")
    vdim(ax, Ps.P(x0, 0)[0] - 8, Ps.P(0, zb0)[1], Ps.P(0, zb1)[1], Ps.P(x0, 0)[0], Ps.P(x0, 0)[0], f1(zb1 - zb0) + "", side="left")
    f0 = p1["feet"][0]
    hdim(ax, Ps.P(f0 - 5, 0)[0], Ps.P(f0 + 5, 0)[0], Ps.P(0, ZS)[1] - 7, Ps.P(0, ZS)[1], Ps.P(0, ZS)[1], f1(Pn["w"]) + "", small=False)
    hdim(ax, Ps.P(p1["feet"][1], 0)[0], Ps.P(p1["feet"][0], 0)[0], Ps.P(0, ZS)[1] - 14, Ps.P(0, ZS)[1], Ps.P(0, ZS)[1], f1(p1["feet"][0] - p1["feet"][1]) + "")
    # --------- tampak depan (y-z) kaki
    ax.text(318, 198, "TAMPAK DEPAN KAKI (y-z) DAN RIM PLATE", fontsize=6.6, fontweight="bold", ha="center")
    Pf = Panel(ax, 318, 172, 25.25, 2, ks)
    y0_, y1_ = p1["y"]
    ax.add_patch(Rectangle(Pf.P(y0_, ZS), (y1_ - y0_) * ks, (zb1 - ZS) * ks, fc=PC[0], ec="k", lw=0.8, zorder=5, alpha=0.9))
    ax.add_patch(Rectangle(Pf.P(y0_ - 6, ZB), (y1_ - y0_ + 12) * ks, (ZS - ZB) * ks, fc="#b8c6de", ec="k", lw=0.8, zorder=4))
    ax.add_patch(Circle(Pf.P(25.25, ZB + 1.0), 0.01, fc="k"))
    vline(ax, Pf.P(25.25, 0)[0], Pf.P(0, ZB - 1.5)[1], Pf.P(0, zb1 + 1.5)[1], c="#c00000", lw=0.4, ls=(0, (6, 1.5, 1, 1.5)), zorder=7)
    hdim(ax, Pf.P(y0_, 0)[0], Pf.P(y1_, 0)[0], Pf.P(0, zb1)[1] + 8, Pf.P(0, zb1)[1], Pf.P(0, zb1)[1], f1(y1_ - y0_) + "")
    ax.text(Pf.P(25.25, ZB - 4.5)[0], Pf.P(25.25, ZB - 4.5)[1], "plate 3,0", fontsize=6.0, ha="center")
    # --------- tabel dan keterangan -> berkas keterangan
    ket.begin("T-4", "Gambar teknik cover: penahan sekrup (3 bagian)")
    ket.table(["No", "Bagian", "Dinding", "Rentang x (mm)", "Panjang (mm)", "Sekrup (x)"],
              [["1", "strip panjang", "Atas (+Y)", f"{sg(p1['x'][0])} ... {sg(p1['x'][1])}", f1(p1["x"][1] - p1["x"][0]), "-23 dan +23"],
               ["2", "strip sedang", "Bawah (-Y), sisi Kanan", f"{sg(p2['x'][0])} ... {sg(p2['x'][1])}", f1(p2["x"][1] - p2["x"][0]), "-23"],
               ["3", "blok kecil", "Bawah (-Y), sisi Kiri", f"{sg(p3['x'][0])} ... {sg(p3['x'][1])}", f1(p3["x"][1] - p3["x"][0]), "+23"]],
              widths=[0.6, 1.8, 3.0, 2.8, 1.8, 1.8], align=["c", "l", "l", "l", "c", "c"])
    ket.items(["Urutan lapisan dari belakang: sekrup M3 x 8, back plate (lubang countersink), penahan, dinding. Sekrup menggigit ulir pilot Ø2,7 mm pada penahan sedalam 5,0 mm.",
               "Tinggi penahan 4,3 mm dari tepi belakang casing. Batang strip melintas 0,4 mm di atas rim plate, puncak penahan 0,7 mm di bawah PCB utama.",
               "Jarak ke bukaan: jack AD8232 7,1 mm, saklar 11,1 mm, micro-USB 8,6 mm, USB-C dan gland lebih dari 15 mm. Tidak ada bukaan yang tertutup.",
               "Strip panjang (No. 1) berada di dinding yang berlubang jack AD8232 dan berjendela saklar.",
               "Cetak dengan puncak penahan di meja, tanpa support. Ketiga bagian ada dalam satu berkas STL.",
               "Denah: angka pada bagian = nomor penahan, lingkaran bersilang = sumbu sekrup M3 (x = +-23 mm, y = +-25,25 mm); dimensi dalam mm dari ujung rongga. Kanan casing berada di kiri gambar.",
               "Gambar bawah: plate dan 3 penahan dilihat dari sisi depan plate (sisi yang menghadap tumpukan). Kanan (-X) di kiri gambar, Kiri (+X) di kanan gambar, Atas (+Y) = sisi jack AD8232 dan saklar."], numbered=True)
    # --------- render 3D penahan di plate (v2d), tanpa teks bawaan gambar
    img_p = os.path.join(CASE, "Peletakan_Penahan_3D.png")
    if os.path.exists(img_p):
        im = Image.open(img_p).convert("RGB"); im = im.crop((0, 78, im.size[0], im.size[1]))
        w_ = 190; h_ = w_ * im.size[1] / im.size[0]
        x0_, y0_ = 22, 40
        ax.imshow(np.asarray(im), extent=(x0_, x0_ + w_, y0_, y0_ + h_), zorder=2, interpolation="lanczos")
        ax.text(x0_ + w_ / 2, y0_ + h_ + 5, "Plate dan 3 penahan, tampak dari depan plate", fontsize=7.2, fontweight="bold", ha="center", va="center")
        ax.text(x0_ - 1, y0_ + h_ / 2, "KANAN", fontsize=6.6, fontweight="bold", rotation=90, ha="right", va="center")
        ax.text(x0_ + w_ + 1, y0_ + h_ / 2, "KIRI", fontsize=6.6, fontweight="bold", rotation=270, ha="left", va="center")
    C.title_block(ax, "GAMBAR TEKNIK: COVER ALAT ECG + PPG", "Penahan sekrup (3 bagian)", 4, NPAGE, scale="Skala: lihat dimensi", right_line="Bahan: PETG (cetak 3D FDM)", ket="T-4")
    return [fig3, fig]
