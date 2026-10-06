"""Gambar jurnal satu per satu (bahasa Inggris, teks besar). Keluaran: PNG 600 dpi + PDF per gambar.
python jurnal_gambar.py <FINAL_TA> [nomor gambar ...]
"""
import sys, os, json, math
import numpy as np
from PIL import Image
from jfig import *

F_ = sys.argv[1]
ONLY = [int(a) for a in sys.argv[2:]]
R = os.path.join(F_, "_render")
OUT = os.path.join(F_, "08_Jurnal_Satu_Per_Satu")
KR = os.path.join(R, "komponen"); ER = os.path.join(R, "elektroda"); SR = os.path.join(R, "sistem")
COL = {"RA": "#C62828", "LA": "#F2B705", "RL": "#2E7D32"}
TXT = {"RA": "white", "LA": "black", "RL": "white"}
S = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v2d_penahan_strip", "_ref", "summary.json")))
FIGS = {}


def fig(n):
    def deco(fn):
        FIGS[n] = fn
        return fn
    return deco


def anchors(path, f_, cb=None):
    a = json.load(open(path))
    return {k: f_(v[0], v[1]) for k, v in a.items() if not k.startswith("_")}


# ====================================================================== 1  exploded enclosure
@fig(1)
def fig01():
    F = Fig(180, 132)
    f, bb, k, cb = F.image(os.path.join(SR, "eksplode_a.png"), (14, 4, 100, 124), pad=14)
    A = anchors(os.path.join(SR, "eksplode_a.png.json"), f)
    F.numbered_callouts(A, bb, [("shell", 1), ("saklar", 2), ("gland", 3), ("tft", 4), ("standoff", 5), ("pcb", 6), ("penahan", 7), ("plate", 8), ("sekrup", 9)], margin=6.5, min_gap=8.0)
    items = [(1, "Front shell"), (2, "Rocker switch"), (3, "Cable gland PG7"), (4, "3.5-inch TFT display"), (5, "M3 standoffs (4)"),
             (6, "Main PCB with modules"), (7, "Screw retainers (3)"), (8, "Back plate"), (9, "M3 x 8 screws (4)")]
    F.legend_list(124, 108, items, pitch=9.2)
    return F, "Fig01_Exploded_view_enclosure"


# ====================================================================== 2  exploded electronics
@fig(2)
def fig02():
    F = Fig(180, 104)
    f, bb, k, cb = F.image(os.path.join(SR, "eksplode_b.png"), (12, 2, 98, 100), pad=14)
    A = anchors(os.path.join(SR, "eksplode_b.png.json"), f)
    F.numbered_callouts(A, bb, [("esp32", 1), ("ad8232", 2), ("boost", 3), ("baterai", 4), ("pcb", 5), ("kabel_ppg_dalam", 6)], margin=6.5, min_gap=8.5)
    items = [(1, "ESP32 DevKit C V4"), (2, "AD8232 ECG module"), (3, "Charger and boost module"), (4, "Li-ion battery, 2000 mAh"), (5, "Main PCB with sockets"), (6, "PPG cable connector")]
    F.legend_list(120, 80, items, pitch=9.8, size=T_MAIN)
    return F, "Fig02_Exploded_view_electronics"


# ====================================================================== 3  system overview
@fig(3)
def fig03():
    CROP = (324, 330, 1884, 1390)
    hero = Image.open(os.path.join(SR, "hero.png")).convert("RGB").crop(CROP)
    W = 180.0
    H = W * hero.height / hero.width
    F = Fig(W, H)
    F.ax.imshow(np.asarray(hero), extent=(0, W, 0, H), origin="upper", zorder=1, interpolation="lanczos")
    A = json.load(open(os.path.join(SR, "hero.png.json")))
    A.update({"RA": (1386, 416), "LA": (1506, 702), "RL": (1662, 512), "lead": (1085, 600)})
    sx = W / hero.width
    P = lambda n: ((A[n][0] - CROP[0]) * sx, H - (A[n][1] - CROP[1]) * sx)
    pos = {"RA": ((P("RA")[0] - 7, P("RA")[1] + 6), "right", "RA electrode (red)"),
           "RL": ((W - 2.0, H - 8.5), "right", "RL electrode (green)"),
           "LA": ((P("LA")[0] + 10, P("LA")[1] - 7), "left", "LA electrode (yellow)"),
           "plug": ((P("plug")[0] - 2, P("plug")[1] + 14), "right", "Lead cable with 3.5 mm plug"),
           "tft": ((P("tft")[0] + 3, P("tft")[1] + 12), "left", "TFT display"),
           "gland": ((P("gland")[0] - 4, P("gland")[1] + 12), "right", "Cable gland"),
           "kabel_ppg_luar": ((P("kabel_ppg_luar")[0] - 4, P("kabel_ppg_luar")[1] + 7), "right", "PPG cable"),
           "klip": ((P("klip")[0] + 12, P("klip")[1] - 5), "left", "Finger-clip PPG sensor")}
    for key, (q, ha, s) in pos.items():
        F.callout(P(key), q, s, ha=ha, size=T_MAIN)
    F.callout((P("shell")[0] - 5, P("shell")[1] - 28), (P("shell")[0] - 32, P("shell")[1] - 40), "Enclosure", ha="left") if False else None
    return F, "Fig03_System_overview"


# ====================================================================== 4  electrode placement on the torso
HUM = os.path.join(R, "manusia", "manusia_full.png")


def load_human():
    im = Image.open(HUM).convert("RGBA")
    info = json.load(open(HUM + ".json"))
    W, H = im.size
    zl = info["z_levels"]
    arr = np.asarray(im).astype(np.float32)
    rows = np.arange(H, dtype=np.float32)

    def ramp(y0, y1):
        t = np.clip((rows - y0) / (y1 - y0), 0, 1); return t * t * (3 - 2 * t)
    top = ramp(zl["520"], zl["480"]) if "520" in zl else np.ones(H)
    bot = 1 - ramp(zl["-380"], zl["-440"]) if "-440" in zl else np.ones(H)
    arr[..., 3] *= (top * bot)[:, None]
    return arr.astype(np.uint8), info


@fig(4)
def fig04():
    arr, info = load_human()
    H0, W0 = arr.shape[:2]
    Wm = 88.0
    Hm = Wm * H0 / W0
    F = Fig(Wm, Hm)
    F.ax.imshow(arr, extent=(0, Wm, 0, Hm), origin="upper", zorder=1, interpolation="lanczos")
    P = lambda key: (info[key][0] / W0 * Wm, Hm - info[key][1] / H0 * Hm)
    for lb, dx, dy, c in (("RA", -2.0, 9.0, COL["RA"]), ("LA", 2.0, 9.0, "#8a6a00"), ("RL", -4.0, 9.0, COL["RL"])):
        x, y = P(lb)
        F.text(x + dx, y + dy, lb, size=12, weight="bold", ha="center", color=c, halo=True)
    x, y = P("device")
    F.callout((x + 8, y - 5), (Wm * 0.50, Hm * 0.290), "Wearable device\n(ESP32 + AD8232\n+ TFT)", ha="left", size=T_MAIN)
    x, y = P("clip")
    F.callout((x + 2, y), (Wm * 0.34, Hm * 0.090), "Finger-clip PPG\nsensor (MAX30102)", ha="left", size=T_MAIN)
    F.text(2, Hm - 5, "Patient's\nright", size=T_MAIN, ha="left", va="center", style="italic")
    F.text(Wm - 2, Hm - 5, "Patient's\nleft", size=T_MAIN, ha="right", va="center", style="italic")
    F.text(Wm / 2, Hm - 3.2, "Anterior view", size=T_MAIN, weight="bold", ha="center")
    return F, "Fig04_Electrode_placement_male_torso"


# ====================================================================== 5  electrode details (3D top/side)
@fig(5)
def fig05():
    F = Fig(88, 120)
    Ti = Ort(os.path.join(ER, "elektroda_top.png"), dict(px=1400, ortho=64.0, target=[0, 0, 0], right=[1, 0, 0], up=[0, 1, 0]))
    Ti.put(F, 40, 88, 1.30)
    F.panel(1, 119, "(a)")
    PADR = 22.5
    (xa, ya), (xb, yb) = Ti.P((-PADR, -PADR, 0)), Ti.P((PADR, -PADR, 0))
    F.hdim(xa, xb, ya - 5.5, ya, yb, "\u00d845 mm")
    F.callout(Ti.P((-1.5, -10.0, 0)), (21, 64), "Hydrogel", ha="right", size=T_MAIN)
    ang = math.radians(35)
    F.callout(Ti.P((9.5 + 17.0 * math.cos(ang), 6.5 + 17.0 * math.sin(ang), 0)), (47, 112), "Connector", ha="left", size=T_MAIN)
    F.callout(Ti.P((-19.0, 12.0, 0)), (21, 100), "Foam pad", ha="right", size=T_MAIN)
    Sd = Ort(os.path.join(ER, "elektroda_side.png"), dict(px=[1800, 700], ortho=64.0, target=[6.0, 0, 4.5], right=[1, 0, 0], up=[0, 0, 1]))
    Sd.put(F, 34, 20, 1.30)
    F.panel(1, 42, "(b)")
    zt = 8.75
    (xa, ya), (xb, yb) = Sd.P((-22.5, 0, 0)), Sd.P((22.5, 0, 0))
    F.hdim(xa, xb, ya - 5.5, ya, yb, "45 mm")
    (x0, y0), (x1, y1) = Sd.P((34.0, 0, 0)), Sd.P((34.0, 0, zt))
    F.vdim(x0 + 3, y0, y1, x0, x1, "8.8 mm", side="right")
    F.callout(Sd.P((13.0, 0, 7.0)), (36, 36), "Connector", ha="left", size=T_MAIN)
    return F, "Fig05_Electrode_details"


# ====================================================================== 6  lead cable and plug
@fig(6)
def fig06():
    F = Fig(180, 104)
    f, bb, k, cb = F.image(os.path.join(ER, "elektroda_set.png"), (4, 44, 172, 58), pad=10)
    F.panel(1, 103, "(a)")
    F.text(bb[0] + 3, bb[1] + bb[3] * 0.43, "3.5 mm TRS plug", size=T_MAIN, ha="left", halo=True)
    F.text(129.6, 99.0, "RA (red)", size=T_MAIN, ha="left", color=COL["RA"], weight="bold", halo=True)
    F.text(148.5, 80.0, "RL (green)", size=T_MAIN, ha="left", color=COL["RL"], weight="bold", halo=True)
    F.text(140.5, 54.0, "LA (yellow)", size=T_MAIN, ha="left", color="#8a6a00", weight="bold", halo=True)
    Pl = Ort(os.path.join(ER, "plug_side.png"), dict(px=[1800, 700], ortho=56.0, target=[18.0, 0, 0], right=[1, 0, 0], up=[0, 0, 1]))
    Pl.put(F, 90, 20, 2.35)
    F.panel(1, 42, "(b)")
    for (a, b, t) in ((0, 14.0, "14"), (14.0, 24.3, "10.3"), (24.3, 35.3, "11")):
        (xa, ya), (xb, yb) = Pl.P((a, 0, -3.25)), Pl.P((b, 0, -3.25))
        F.hdim(xa, xb, ya - 5, ya, yb, t)
    (x0, y0), (x1, y1) = Pl.P((35.3, 0, -3.25)), Pl.P((35.3, 0, 3.25))
    F.vdim(x0 + 4, y0, y1, x0, x1, "Ø6.5", side="right")
    F.callout(Pl.P((6.0, 0, 1.75)), (Pl.P((6, 0, 0))[0] - 6, 36), "Ø3.5 mm barrel", ha="left", size=T_MAIN)
    F.text(172, 5, "Dimensions in mm", size=T_SMALL, ha="right", color=GREY, style="italic")
    return F, "Fig06_Lead_cable_and_plug"


# ====================================================================== 7  lead convention table
@fig(7)
def fig07():
    F = Fig(180, 52)
    cols = [4, 30, 62, 100]
    F.text(cols[0], 47, "Lead", size=T_MAIN + 0.5, weight="bold")
    F.text(cols[1], 47, "Colour", size=T_MAIN + 0.5, weight="bold")
    F.text(cols[2], 47, "Function", size=T_MAIN + 0.5, weight="bold")
    F.text(cols[3], 47, "Electrode position", size=T_MAIN + 0.5, weight="bold")
    F.ax.plot([2, 178], [43, 43], color=INK, lw=0.8)
    rows = [("RA", "Red", "Right arm", "Right infraclavicular fossa"), ("LA", "Yellow", "Left arm", "Left infraclavicular fossa"), ("RL", "Green", "Right leg (reference)", "Right lower abdomen")]
    for i, (lb, cn, fn, loc) in enumerate(rows):
        y = 35 - i * 10
        F.ax.add_patch(Ellipse((cols[0] + 6, y), 12.5, 7.4, fc=COL[lb], ec=INK, lw=0.7, zorder=20))
        F.text(cols[0] + 6, y, lb, size=T_MAIN, weight="bold", ha="center", color=TXT[lb], zorder=22)
        F.text(cols[1], y, cn, size=T_MAIN)
        F.text(cols[2], y, fn, size=T_MAIN)
        F.text(cols[3], y, loc, size=T_MAIN)
    F.ax.plot([2, 178], [5.5, 5.5], color=INK, lw=0.8)
    return F, "Fig07_Lead_colour_code"


# ====================================================================== 8, 9, 10  component figures
def comp_fig(key, title_dims, name, label_iso=None):
    F = Fig(180, 104)
    I = json.load(open(os.path.join(KR, f"{key}_info.json")))
    bmin, bmax = np.array(I["bbox_min"]), np.array(I["bbox_max"])
    f, bb, k, cb = F.image(os.path.join(KR, f"{key}_iso.png"), (3, 8, 88, 90), pad=10)
    F.panel(1, 103, "(a)")
    wt, ht = bmax[0] - bmin[0], bmax[1] - bmin[1]
    T = Ort(os.path.join(KR, f"{key}_top.png"), I["top"])
    kt = min(62.0 / (wt + 6), 62.0 / (ht + 4))
    cxT, cyT = 137, 70
    T.put(F, cxT, cyT, kt)
    F.panel(96, 103, "(b)")
    for d in title_dims["top"]:
        if d[0] == "h":
            _, x0, x1, yy, off, txt = d
            (xa, ya), (xb, yb) = T.P((x0, yy, 0)), T.P((x1, yy, 0))
            F.hdim(xa, xb, ya + off, ya, yb, txt)
        else:
            _, y0, y1, xx, off, txt = d
            (xa, ya), (xb, yb) = T.P((xx, y0, 0)), T.P((xx, y1, 0))
            F.vdim(xa + off, ya, yb, xa, xb, txt, side="right" if off > 0 else "left")
    for (X, Y, txt, dx, dy, ha) in title_dims["calls"]:
        F.callout(T.P((X, Y, 0)), (T.P((X, Y, 0))[0] + dx, T.P((X, Y, 0))[1] + dy), txt, ha=ha, size=T_MAIN)
    Fr = Ort(os.path.join(KR, f"{key}_front.png"), I["front"])
    kf = min(70.0 / (wt + 4), 22.0 / (bmax[2] - bmin[2] + 2))
    Fr.put(F, cxT, 15, kf)
    F.panel(96, 33, "(c)")
    for d in title_dims["front"]:
        if d[0] == "h":
            _, x0, x1, zz, off, txt = d
            (xa, ya), (xb, yb) = Fr.P((x0, 0, zz)), Fr.P((x1, 0, zz))
            F.hdim(xa, xb, ya + off, ya, yb, txt)
        else:
            _, z0, z1, xx, off, txt = d
            (xa, ya), (xb, yb) = Fr.P((xx, 0, z0)), Fr.P((xx, 0, z1))
            F.vdim(xa + off, ya, yb, xa, xb, txt, side="right" if off > 0 else "left")
    F.text(176, 3, "Dimensions in mm", size=T_SMALL, ha="right", color=GREY, style="italic")
    return F, name


@fig(8)
def fig08():
    return comp_fig("esp32", dict(
        top=[("h", -14.25, 14.25, -28.55, -8, "28.5"), ("v", -28.55, 26.0, 14.25, 8, "54.6")],
        front=[("v", -9.7, 3.95, 14.25, 8, "13.7")],
        calls=[(-6.0, 10.0, "WROOM-32 module", -12, 8, "right"), (-8.0, -22.4, "EN / BOOT", -10, 0, "right"), (0, -27.0, "micro-USB", 14, -6, "left")]), "Fig08_ESP32_DevKit_C_V4")


@fig(9)
def fig09():
    return comp_fig("ad8232", dict(
        top=[("h", -35.42, 0.14, 0.26, -8, "35.56"), ("v", 0.26, 28.2, 0.14, 8, "27.94")],
        front=[("v", -5.4, 5.0, 0.14, 8, "10.4")],
        calls=[(-19.0, 29.0, "3.5 mm jack", 8, 8, "left"), (-11.2, 16.5, "AD8232 IC", -2, 12, "left")]), "Fig09_AD8232_ECG_module")


@fig(10)
def fig10():
    return comp_fig("hw605", dict(
        top=[("h", -6.75, 6.75, -9.0, -8, "13.5"), ("v", -9.0, 9.0, 7.7, 8, "18.0")],
        front=[("v", 0.0, 3.2, 7.7, 8, "3.2")],
        calls=[(0, 0, "Sensor window", -12, 14, "right"), (6.6, 3.81, "Solder pads", 3, 19, "right")]), "Fig10_MAX30102_HW605_module")


# ====================================================================== 11  cable gland and switch
@fig(11)
def fig11():
    F = Fig(180, 124)
    gl, sw = S["gland"], S["switch"]
    HY = S["outer_y"][1]; swc = sw["x"]
    F.image(os.path.join(KR, "gland_iso.png"), (2, 74, 86, 48), pad=10)
    F.panel(1, 123, "(a)")
    Ig = json.load(open(os.path.join(KR, "gland_info.json")))
    Fg = Ort(os.path.join(KR, "gland_front.png"), Ig["front"])
    zc = gl["zc"]
    Fg.put(F, 45, 34, 2.3)
    F.panel(1, 68, "(b)")
    (xa, ya), (xb, yb) = Fg.P((-74.3, 0, zc - 8.7)), Fg.P((-49.3, 0, zc - 8.7))
    F.hdim(xa, xb, ya - 5, ya, yb, "25.0")
    (x0, y0), (x1, y1) = Fg.P((-49.3, 0, zc - 6.25)), Fg.P((-49.3, 0, zc + 6.25))
    F.vdim(x0 + 3.5, y0, y1, x0, x1, "\u00d812.5", side="right")
    for (pt, txt, dx, dy, ha) in (((-60.0, 0, zc + 8.0), "Hex head", 6, 6, "left"), ((-68.0, 0, zc + 5.5), "Cap", -2, 6, "right"), ((-52.5, 0, zc + 6.0), "Nut", 8, 7, "left")):
        q = Fg.P(pt)
        F.callout(q, (q[0] + dx, q[1] + dy), txt, ha=ha, size=T_MAIN)
    F.image(os.path.join(KR, "saklar_iso.png"), (94, 74, 84, 48), pad=10)
    F.panel(93, 123, "(c)")
    Is = json.load(open(os.path.join(KR, "saklar_info.json")))
    St = Ort(os.path.join(KR, "saklar_top.png"), Is["top"])
    St.put(F, 134, 34, 1.65)
    F.panel(93, 68, "(d)")
    ytop, ybot = HY + 4.6, HY - sw["panel"] - sw["depth"] - 5.0
    (xa, ya), (xb, yb) = St.P((swc - 7.4, ytop, 0)), St.P((swc + 7.4, ytop, 0))
    F.hdim(xa, xb, ya + 4, ya, yb, "14.8")
    (x0, y0), (x1, y1) = St.P((swc + 7.4, ytop, 0)), St.P((swc + 7.4, ybot, 0))
    F.vdim(x0 + 4, y0, y1, x0, x1, fmt(ytop - ybot), side="right")
    F.text(176, 3, "Dimensions in mm", size=T_SMALL, ha="right", color=GREY, style="italic")
    return F, "Fig11_Cable_gland_and_rocker_switch"


# ====================================================================== 12  enclosure renders
@fig(12)
def fig12():
    F = Fig(180, 82)
    for i, (fn, x0, tag) in enumerate((("cover_iso_depan.png", 0, "(a)"), ("cover_iso_belakang.png", 90, "(b)"))):
        f, bb, k, cb = F.image(os.path.join(R, "cover", fn), (x0 + 1, 2, 88, 70), pad=8)
        F.panel(x0 + 1, 81, tag)
    # etiket langsung (titik diambil dari tampilan, posisi relatif pada panel)
    F.text(45, 78, "Front view", size=T_MAIN, weight="bold", ha="center", va="center")
    F.text(135, 78, "Rear view", size=T_MAIN, weight="bold", ha="center", va="center")
    return F, "Fig12_Enclosure_front_and_rear"


# ====================================================================== 13  enclosure orthographic views with dimensions
@fig(13)
def fig13():
    HX = S["outer"][0] / 2; PX = S["plate"][0] / 2
    YB, HY = S["outer_y"]; YC = (YB + HY) / 2; HH = (HY - YB) / 2
    ZB, ZS, ZT = S["z"]["plate_bottom"], S["z"]["split"], S["z"]["top"]
    ZC = (ZB + ZT) / 2
    win = S["window"]
    F = Fig(180, 98)
    k = 0.92
    # tampak depan: jendela gambar 140 x 76 mm model (1:1), pusat model (0, YC)
    cx, cy = 66, 56
    im = Image.open(os.path.join(R, "garis", "garis_depan.png")).convert("RGB")
    F.ax.imshow(np.asarray(im), extent=(cx - 70 * k, cx + 70 * k, cy - 38 * k, cy + 38 * k), origin="upper", interpolation="lanczos", zorder=1)
    pf = lambda X, Y: (cx + X * k, cy + (Y - YC) * k)
    F.panel(1, 97, "(a)")
    F.hdim(pf(-PX, 0)[0], pf(PX, 0)[0], pf(0, YB)[1] - 7, pf(0, YB)[1], pf(0, YB)[1], "133.0")
    F.hdim(pf(-HX, 0)[0], pf(HX, 0)[0], pf(0, YB)[1] - 17, pf(0, YB)[1], pf(0, YB)[1], "105.0")
    F.vdim(pf(PX, 0)[0] + 7, pf(0, YB)[1], pf(0, HY)[1], pf(PX, 0)[0], pf(PX, 0)[0], "63.5", side="right")
    wx0, wx1 = pf(win[2] - win[0] / 2, 0)[0], pf(win[2] + win[0] / 2, 0)[0]
    F.hdim(wx0, wx1, pf(0, 12)[1], pf(0, 12)[1], pf(0, 12)[1], "79.0")
    F.vdim(pf(win[2] + win[0] / 2, 0)[0] + 5.5, pf(0, -win[1] / 2)[1], pf(0, win[1] / 2)[1], pf(win[2] + win[0] / 2, 0)[0], pf(win[2] + win[0] / 2, 0)[0], "52.0", side="right") if False else None
    # tampak kanan (u = Z, v = Y), jendela 48 x 76
    cx2 = 160
    im2 = Image.open(os.path.join(R, "garis", "garis_kanan.png")).convert("RGB")
    F.ax.imshow(np.asarray(im2), extent=(cx2 - 24 * k, cx2 + 24 * k, cy - 38 * k, cy + 38 * k), origin="upper", interpolation="lanczos", zorder=1)
    pk = lambda Z, Y: (cx2 + (Z - ZC) * k, cy + (Y - YC) * k)
    F.panel(144, 97, "(b)")
    F.hdim(pk(ZB, 0)[0], pk(ZT, 0)[0], pk(0, YB)[1] - 7, pk(0, YB)[1], pk(0, YB)[1], "37.4")
    F.text(66, 91.5, "Front view", size=T_MAIN, weight="bold", ha="center")
    F.text(160, 91.5, "Side view", size=T_MAIN, weight="bold", ha="center")
    F.text(176, 3, "Dimensions in mm", size=T_SMALL, ha="right", color=GREY, style="italic")
    return F, "Fig13_Enclosure_dimensions"


# ====================================================================== 14  exploded clip
@fig(14)
def fig14():
    F = Fig(180, 126)
    f, bb, k, cb = F.image(os.path.join(R, "klip", "klip_meledak.png"), (14, 2, 110, 122), pad=12)
    a = json.load(open(os.path.join(R, "klip", "anchors_meledak.json")))
    W_, H_ = 1600, 1472
    A = {n: f(v[0] * W_, (1 - v[1]) * H_) for n, v in a.items()}
    F.numbered_callouts(A, bb, [("A", 1), ("B", 2), ("C", 3), ("D", 4), ("board", 5), ("cable", 6), ("spring", 7), ("screw", 8), ("foam", 9)], margin=6.5, min_gap=9.0)
    items = [(1, "Lower jaw"), (2, "Upper jaw"), (3, "Bottom cover"), (4, "Shim ring, 1 mm"), (5, "HW-605 sensor module"), (6, "4-core cable"), (7, "Compression spring"), (8, "M3 hinge screw"), (9, "Foam pad, 1 mm")]
    F.legend_list(132, 106, items, pitch=9.8, size=T_SMALL + 0.5)
    return F, "Fig14_Exploded_view_finger_clip"


# ====================================================================== 15  clip in use
@fig(15)
def fig15():
    F = Fig(180, 84)
    f, bb, k, cb = F.image(os.path.join(R, "klip", "klip_pakai.png"), (2, 2, 88, 70), pad=8)
    F.panel(1, 83, "(a)")
    F.text(45, 77, "Clip on the fingertip", size=T_MAIN, weight="bold", ha="center")
    f2, bb2, k2, cb2 = F.image(os.path.join(R, "klip", "klip_bawah.png"), (92, 2, 86, 70), pad=8)
    F.panel(91, 83, "(b)")
    F.text(135, 77, "Bottom cover removed", size=T_MAIN, weight="bold", ha="center")
    return F, "Fig15_Finger_clip_in_use"


# ====================================================================== 16  user interface
@fig(16)
def fig16():
    F = Fig(180, 140)
    im = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "layar_ui.png")).convert("RGBA")
    bw = 140.0
    bh = bw * im.height / im.width
    x0, y0 = 20, 140 - bh - 4
    F.ax.imshow(np.asarray(im), extent=(x0, x0 + bw, y0, y0 + bh), origin="upper", zorder=2, interpolation="lanczos")
    F.ax.add_patch(Rectangle((x0, y0), bw, bh, fill=False, ec=INK, lw=1.0, zorder=3))
    P = lambda px, py: (x0 + px / 480 * bw, y0 + bh - py / 320 * bh)
    # penanda di luar layar, garis lurus ke elemen yang dimaksud
    marks = [(1, P(12, 112), (10, P(0, 112)[1])), (2, P(12, 240), (10, P(0, 240)[1])), (6, P(4, 312), (10, P(0, 312)[1])),
             (3, P(450, 62), (170, P(0, 62)[1])), (4, P(450, 135), (170, P(0, 135)[1])), (5, P(454, 228), (170, P(0, 228)[1]))]
    for n, p, q in marks:
        F.ax.plot([p[0], q[0]], [p[1], q[1]], color="white", lw=1.0, zorder=22, solid_capstyle="round")
        F.ax.plot([p[0]], [p[1]], marker="o", ms=4.0, mfc="white", mec=INK, mew=0.8, zorder=23)
        F.balloon(q, n, r=3.1, z=30)
    items = [(1, "ECG trace"), (2, "PPG trace"), (3, "Heart rate (BPM)"), (4, "SpO2 and pulse rate"), (5, "Rhythm status"), (6, "RR interval and SDNN")]
    F.legend_list(14, y0 - 12, items[:3], pitch=9.0, size=T_MAIN)
    F.legend_list(98, y0 - 12, items[3:], pitch=9.0, size=T_MAIN)
    return F, "Fig16_Display_user_interface"


if __name__ == "__main__":
    for n in sorted(FIGS):
        if ONLY and n not in ONLY: continue
        F, name = FIGS[n]()
        F.save(OUT, name)
