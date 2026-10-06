"""Lembar GAMBAR KOMPONEN A3 (6 halaman): ESP32 DevKit C V4, AD8232, MAX30102 HW-605, elektroda EKG 3 lead, gland PG7 + saklar KCD11, komponen pendukung.
Dimensi dihitung dari geometri model (bbox) dan konstanta model; render dari r_komponen.py / r_elektroda.py (Cycles).
python lembar_komponen.py <folder_render> <folder_keluaran> [berkas_fig_1kolom.png]
"""
import sys, os, json, math, re, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle, Polygon
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import ket

RD, OUTD = sys.argv[1:3]
FIG1 = sys.argv[3] if len(sys.argv) > 3 else None
KR = os.path.join(RD, "komponen"); ER = os.path.join(RD, "elektroda")
os.makedirs(OUTD, exist_ok=True)
S = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v2d_penahan_strip", "_ref", "summary.json")))
NPAGE = 6


class Ort:
    """render ortografis (info per tampak) dengan pemetaan model -> kertas, dapat dipotong ke isi (alfa) tanpa mengubah skala."""
    def __init__(self, png, iv, k=None):
        self.png = png; self.iv = iv
        self.px = iv["px"][0] if isinstance(iv["px"], list) else iv["px"]
        self.py = iv["px"][1] if isinstance(iv["px"], list) else iv["px"]
        self.t = np.array(iv["target"], float); self.r = np.array(iv["right"], float); self.u = np.array(iv["up"], float)
        self.o = iv["ortho"]; self.k = k

    def put(self, ax, X, Y, k, pad=10, z=2):
        """pasang gambar dengan skala k (mm kertas per mm model); pusat isi (alfa) diletakkan di (X, Y) kertas."""
        im = Image.open(self.png).convert("RGBA")
        a = np.asarray(im)[..., 3]
        ys, xs = np.where(a > 6)
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, self.px)
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, self.py)
        self.k = k
        s = k * self.o / self.px                           # mm kertas per piksel
        cxm, cym = (x0 + x1) / 2, (y0 + y1) / 2             # pusat isi (piksel)
        self.cx = X - (cxm - self.px / 2) * s              # pusat gambar penuh di kertas
        self.cy = Y + (cym - self.py / 2) * s
        left = self.cx - self.px / 2 * s; top = self.cy + self.py / 2 * s
        ext = (left + x0 * s, left + x1 * s, top - y1 * s, top - y0 * s)
        ax.imshow(np.asarray(im)[y0:y1, x0:x1], extent=ext, origin="upper", zorder=z, interpolation="lanczos")
        self.ext = ext
        return ext

    def P(self, xyz):
        d = np.array(xyz, float) - self.t
        return self.cx + float(d @ self.r) * self.k, self.cy + float(d @ self.u) * self.k


def fit_img(ax, path, box, pad=8, z=2):
    """pasang gambar (dipotong ke isi) agar muat di kotak (x0,y0,x1,y1) kertas; kembalikan (skala mm kertas per piksel asli, ekstensi)."""
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im)[..., 3]
    ys, xs = np.where(a > 6)
    x0, x1, y0, y1 = max(xs.min() - pad, 0), min(xs.max() + pad, im.size[0]), max(ys.min() - pad, 0), min(ys.max() + pad, im.size[1])
    c = im.crop((x0, y0, x1, y1))
    bw, bh = box[2] - box[0], box[3] - box[1]
    s = min(bw / c.size[0], bh / c.size[1])
    w, h = c.size[0] * s, c.size[1] * s
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    ax.imshow(np.asarray(c), extent=(cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2), origin="upper", zorder=z, interpolation="lanczos")
    return s


def callout(ax, pt, text, dx, dy, ha="left", fs=6.3):
    leader(ax, pt, (pt[0] + dx, pt[1] + dy), text, ha=ha, fs=fs)


def sheet(title, page):
    fig, ax = new_sheet()
    ax.text(210, 286, title, fontsize=11.5, fontweight="bold", ha="center", va="center", zorder=7)
    hline(ax, 8, 412, 280.3, lw=0.4, c="#999999")
    return fig, ax


def head_(ax, x, y, text):
    ax.text(x, y, text, fontsize=7.2, fontweight="bold", va="center")


def colour_chip(ax, x, y, col, txt, tcol="white", w=22, h=8.0):
    ax.add_patch(Rectangle((x, y - h / 2), w, h, fc=col, ec="k", lw=0.5, zorder=7))
    ax.text(x + w / 2, y, txt, fontsize=7.2, fontweight="bold", color=tcol, ha="center", va="center", zorder=8)


def spec_to_ket(spec):
    """daftar teks spesifikasi ('##judul' = anak bagian; baris berawalan angka = butir bernomor) -> berkas keterangan."""
    buf = []

    def flush():
        if buf:
            ket.items([re.sub(r"^\d+\s+", "", b) for b in buf], numbered=True); buf.clear()
    for ln in spec:
        if ln.startswith("##"):
            flush(); ket.sub(ln[2:].strip())
        elif re.match(r"^\d+\s", ln):
            buf.append(ln)
        else:
            flush(); ket.para(ln)
    flush()


def src_to_ket(src):
    ket.sub("Sumber model dan catatan keakuratan")
    for ln in src[1:]:
        ket.para(ln)


# =============================================================== halaman modul elektronik: iso besar + tampak atas + tampak depan (keterangan di berkas terpisah)
def page_modul(page, title, key, k_top, spec, dims_top, dims_front, calls_top, src, k_front=None, mp_top=None, extra=None, code=None):
    fig, ax = sheet(title, page)
    I = json.load(open(os.path.join(KR, f"{key}_info.json")))
    bmin, bmax = np.array(I["bbox_min"]), np.array(I["bbox_max"])
    head_(ax, 12, 275, "A. Tampak isometrik")
    fit_img(ax, os.path.join(KR, f"{key}_iso.png"), (8, 62, 205, 268), pad=10)
    head_(ax, 215, 275, "B. Tampak atas (mm)")
    T = Ort(os.path.join(KR, f"{key}_top.png"), I["top"])
    wt, ht = bmax[0] - bmin[0], bmax[1] - bmin[1]
    k_top = min(120.0 / wt, 98.0 / ht)
    T.put(ax, 312, 208, k_top)
    head_(ax, 215, 143, "C. Tampak depan (mm)")
    F = Ort(os.path.join(KR, f"{key}_front.png"), I["front"])
    k_front = min(120.0 / wt, 44.0 / (bmax[2] - bmin[2]))
    F.put(ax, 312, 98, k_front)
    for d in dims_top:
        kind = d[0]
        if kind == "h":
            _, x0, x1, yy, off, txt = d
            (xa, ya), (xb, yb) = T.P((x0, yy, 0)), T.P((x1, yy, 0))
            hdim(ax, xa, xb, ya + off, ya, yb, txt)
        else:
            _, y0, y1, xx, off, txt = d
            (xa, ya), (xb, yb) = T.P((xx, y0, 0)), T.P((xx, y1, 0))
            vdim(ax, xa + off, ya, yb, xa, xb, txt, side="right" if off > 0 else "left")
    for d in dims_front:
        kind = d[0]
        if kind == "h":
            _, x0, x1, zz, off, txt = d
            (xa, ya), (xb, yb) = F.P((x0, 0, zz)), F.P((x1, 0, zz))
            hdim(ax, xa, xb, ya + off, ya, yb, txt)
        else:
            _, z0, z1, xx, off, txt = d
            (xa, ya), (xb, yb) = F.P((xx, 0, z0)), F.P((xx, 0, z1))
            vdim(ax, xa + off, ya, yb, xa, xb, txt, side="right" if off > 0 else "left")
    for (X, Y, txt, dx, dy, ha) in calls_top:
        callout(ax, T.P((X, Y, 0)), txt, dx, dy, ha=ha)
    ket.begin(code, title.split("  ", 1)[1])
    spec_to_ket(spec)
    if extra: extra()
    src_to_ket(src)
    title_block(ax, "KOMPONEN: " + title.split("  ", 1)[1].split("(")[0].strip().upper(), "Tampak isometrik, atas, depan", page, NPAGE, scale="Skala: sesuai dimensi", ket=code)
    return fig


def pg_esp32():
    spec = ["##Spesifikasi",
            "Mikrokontroler dual-core 240 MHz dengan Wi-Fi dan Bluetooth, flash 4 MB. Dipakai untuk akuisisi sinyal ECG/PPG dan inferensi LightGBM.",
            "Papan 54,6 x 28,5 x 1,6 mm; tinggi total 13,7 mm (modul 3,8 mm di atas PCB, pin 8,2 mm di bawah PCB).",
            "Header 2 x 19 pin, pitch 2,54 mm, jarak antarbaris 25,4 mm. Menancap pada 2 soket female PCB utama.",
            "##Posisi pada rakitan",
            "Pusat X = +27,7 mm dari pusat pola baut. PCB ESP32 di Z 15,1 ... 16,7 mm, atas modul di Z = 20,5 mm.",
            "Port micro-USB menghadap sisi Bawah casing (lubang 12,2 x 8,2 mm). Plug beserta overmold harus muat di lubang itu.",
            "##Keterangan bagian",
            "1  ESP32-WROOM-32 (perisai logam + antena PCB)", "2  Tombol EN dan BOOT", "3  Konektor micro-USB", "4  Header pin 2 x 19 (emas)"]
    src = ["SUMBER", "STEP unggahan pengguna (esp32-wroom-30pin-c-type) diadaptasi menjadi DevKit C V4: 19 pin per baris (38 pin), konektor USB-C diganti micro-USB, PCB dinaikkan 2,55 mm.",
           "Ukuran 54,6 x 28,5 mm dan tinggi komponen dihitung langsung dari model. Gambar 3D hanya ilustrasi dan alat bantu cek kecocokan; datasheet resmi tetap acuan."]
    return page_modul(1, "K-1  ESP32 DevKit C V4 (ESP32-WROOM-32, 38 pin)", "esp32", 2.7, spec,
                      dims_top=[("h", -14.25, 14.25, -28.55, -7, "28,5"), ("v", -28.55, 26.0, 14.25, 8, "54,6"), ("h", -12.7, 12.7, 26.0, 7, "25,4")],
                      dims_front=[("v", -9.7, 3.95, 14.25, 9, "13,7"), ("v", -1.5, 0.1, -14.25, -9, "1,6")],
                      calls_top=[(-6.0, 10.0, "1 WROOM-32", -20, 8, "right"),
                                 (-8.0, -22.4, "2 tombol EN/BOOT", -14, 2, "right"), (0, -27.0, "3 micro-USB", 16, -6, "left")],
                      src=src, code="K-1")


def _pin_ket():
    ket.sub("Fungsi pin header 6 pin (pitch 2,54 mm)")
    ket.table(["Pin", "Fungsi"], [["GND", "ground (0 V)"], ["3,3V", "catu daya modul 3,3 V"], ["OUTPUT", "keluaran analog sinyal ECG ke ADC ESP32"],
                                  ["LO-", "deteksi elektroda lepas (-)"], ["LO+", "deteksi elektroda lepas (+)"], ["SDN", "shutdown (aktif rendah)"]], widths=[1.2, 6.0], align=["c", "l"])


def pg_ad8232():
    spec = ["##Spesifikasi",
            "Front-end ECG 1 lead dengan deteksi elektroda lepas (LO+, LO-). Keluaran analog dibaca ADC ESP32.",
            "Papan 35,56 x 27,94 mm; PCB beserta komponen setebal 2,3 mm; jack TRS 3,5 mm menonjol 2,3 mm di tepi Atas.",
            "Header 6 pin (GND, 3,3V, OUTPUT, LO-, LO+, SDN) pitch 2,54 mm. Pin dipendekkan agar masuk header PCB 3,8 mm (Z 6,6 ... 10,4).",
            "##Elektroda (kabel 3 lead, plug 3,5 mm)",
            "Merah = RA (right arm), kuning = LA (left arm), hijau = RL (right leg, referensi). Lihat K-4.",
            "##Posisi pada rakitan",
            "PCB di Z 10,4 ... 12,7 mm; jack pusat di Z = 15,0 mm, 61,3 mm dari tepi Kiri PCB. Hidung jack menembus dinding Atas (lubang 7,2 mm).",
            "##Keterangan bagian",
            "1  Jack TRS 3,5 mm (elektroda)", "2  IC AD8232", "3  Header 6 pin", "4  Lubang baut M3 (4 buah)"]
    src = ["SUMBER", "Model Thingiverse #5330841 (.blend unggahan pengguna). Satuan meter diubah ke mm, pin logam dipotong pada Z = 6,6 mm (kedalaman header PCB). Posisi diselaraskan dengan header dan jack pada Gerber.",
           "Ukuran papan 35,56 x 27,94 mm dihitung dari model. Gambar 3D hanya ilustrasi; datasheet resmi tetap acuan."]
    return page_modul(2, "K-2  Modul AD8232 ECG (SparkFun) + jack 3,5 mm", "ad8232", 3.0, spec,
                      dims_top=[("h", -35.42, 0.14, 0.26, -7, "35,56"), ("v", 0.26, 28.2, 0.14, 8, "27,94")],
                      dims_front=[("v", -5.4, 5.0, 0.14, 9, "10,4")],
                      calls_top=[(-19.0, 29.0, "1 jack 3,5 mm", 14, 8, "left"), (-11.2, 16.5, "2 IC AD8232", 14, -4, "left"), (-17.5, 1.2, "3 header 6 pin", -6, 12, "right")],
                      src=src, extra=_pin_ket, code="K-2")


def pg_hw605():
    spec = ["##Spesifikasi",
            "Sensor detak jantung dan SpO2: LED merah dan inframerah, fotodioda, antarmuka I2C (alamat 0x57), catu 3,3 V.",
            "Papan 13,5 x 18,0 x 1,6 mm; tinggi total 3,2 mm; jendela sensor sekitar 5,6 x 3,3 mm di tengah papan.",
            "Pad solder yang dipakai: VIN, SCL, SDA, GND (kabel AWG 4 inti merah/kuning/putih/hitam). INT, IRD, RD tidak dipakai.",
            "##Posisi pada rakitan",
            "Terpasang di klip jari (rahang A/B, tutup C, pegas, baut M3). Jendela sensor menghadap bantalan jari, kabel keluar lewat gland PG7. Lihat gambar teknik klip.",
            "##Keterangan bagian",
            "1  Jendela sensor (LED + fotodioda)", "2  Pad solder (kuning)", "3  Komponen SMD"]
    src = ["SUMBER", "Berkas SENSOR_DE_LA_PULSERA.sldprt (SolidWorks, 'SENSOR-DIBUJO') hanya berisi papan polos hitam dengan empat lubang pojok, tanpa paket sensor. Kemasan MAX30102 dan pad dimodelkan ulang dari foto dan datasheet.",
           "Ketelitian sekitar +-0,3 mm. Ukur papan asli lalu sesuaikan make_hw605.py. Gambar 3D hanya ilustrasi; datasheet resmi tetap acuan."]
    return page_modul(3, "K-3  Sensor PPG MAX30102 - papan HW-605", "hw605", 9.0, spec,
                      dims_top=[("h", -6.75, 6.75, -9.0, -7, "13,5"), ("v", -9.0, 9.0, 7.7, 9, "18,0")],
                      dims_front=[("v", 0.0, 3.2, 7.7, 8, "3,2"), ("v", 0.0, 1.6, -6.75, -8, "1,6")],
                      calls_top=[(0, 0, "1 jendela sensor", -36, 24, "right"), (6.6, 3.81, "2 pad solder", 8, 14, "left")],
                      src=src, code="K-3")


# =============================================================== K-4 elektroda
def pg_elektroda():
    fig, ax = sheet("K-4  Elektroda EKG 3 lead (merah RA, kuning LA, hijau RL) + kabel dan plug 3,5 mm", 4)
    RED, YEL, GRN = (0.78, 0.05, 0.04), (0.95, 0.72, 0.04), (0.02, 0.38, 0.22)
    head_(ax, 12, 275, "A. Set kabel 3 lead dengan plug TRS 3,5 mm")
    fit_img(ax, os.path.join(ER, "elektroda_set.png"), (12, 150, 240, 270), pad=10)
    head_(ax, 250, 275, "B. Tampak atas (mm)")
    Ti = Ort(os.path.join(ER, "elektroda_top.png"), dict(px=1400, ortho=64.0, target=[0, 0, 0], right=[1, 0, 0], up=[0, 1, 0]))
    kt = 2.35
    Ti.put(ax, 330, 207, kt, pad=10)
    PADR = 22.5
    ax.add_patch(Circle(Ti.P((0, 0, 0)), PADR * Ti.k, fill=False, lw=0.6, ec="k", zorder=6))
    ax.add_patch(Circle(Ti.P((-1.5, -2.0, 0)), 17.0 * Ti.k, fill=False, lw=0.4, ec="#2c6f95", ls=(0, (4, 2)), zorder=6))
    (xa, ya), (xb, yb) = Ti.P((-PADR, -PADR, 0)), Ti.P((PADR, -PADR, 0))
    hdim(ax, xa, xb, ya - 5, ya, yb, "Ø45")
    callout(ax, Ti.P((-1.5, -12.0, 0)), "gel Ø34", -10, -16, ha="right")
    ang = math.radians(35)
    callout(ax, Ti.P((9.5 + 17.0 * math.cos(ang), 6.5 + 17.0 * math.sin(ang), 0)), "konektor", 4, 10)
    callout(ax, Ti.P((9.5, 6.5, 0)), "snap", 24, -26)
    head_(ax, 250, 143, "C. Tampak samping (mm)")
    Sd = Ort(os.path.join(ER, "elektroda_side.png"), dict(px=[1800, 700], ortho=64.0, target=[6.0, 0, 4.5], right=[1, 0, 0], up=[0, 0, 1]))
    ks = 2.0
    Sd.put(ax, 330, 112, ks, pad=10)
    zt = 8.75
    (xa, ya), (xb, yb) = Sd.P((-22.5, 0, 0)), Sd.P((22.5, 0, 0))
    hdim(ax, xa, xb, ya - 5, ya, yb, "45")
    (x0, y0), (x1, y1) = Sd.P((34.0, 0, 0)), Sd.P((34.0, 0, zt))
    vdim(ax, x0 + 5, y0, y1, x0, x1, f1(zt), side="right")
    callout(ax, Sd.P((-12.0, 0, 0.6)), "pad busa + gel", -2, -16, ha="right")
    callout(ax, Sd.P((13.0, 0, 7.0)), "konektor", -2, 14)
    head_(ax, 12, 146, "D. Plug TRS 3,5 mm")
    Pl = Ort(os.path.join(ER, "plug_side.png"), dict(px=[1800, 700], ortho=56.0, target=[18.0, 0, 0], right=[1, 0, 0], up=[0, 0, 1]))
    kp = 5.2
    Pl.put(ax, 120, 122, kp, pad=8)
    (xa, ya), (xb, yb) = Pl.P((0, 0, -3.25)), Pl.P((14.0, 0, -3.25))
    hdim(ax, xa, xb, ya - 6, ya, yb, "14")
    (xa, ya), (xb, yb) = Pl.P((14.0, 0, -3.25)), Pl.P((24.3, 0, -3.25))
    hdim(ax, xa, xb, ya - 6, ya, yb, "10,3")
    (xa, ya), (xb, yb) = Pl.P((24.3, 0, -3.25)), Pl.P((35.3, 0, -3.25))
    hdim(ax, xa, xb, ya - 6, ya, yb, "11")
    (x0, y0), (x1, y1) = Pl.P((35.3, 0, -3.25)), Pl.P((35.3, 0, 3.25))
    vdim(ax, x0 + 8, y0, y1, x0, x1, "Ø6,5", side="right")
    callout(ax, Pl.P((6.0, 0, 1.75)), "barel Ø3,5", 24, 12)
    # kode warna lead
    tx, ty = 12, 84
    head_(ax, tx, ty + 8, "E. Kode warna lead")
    rows = [("RA", "merah", "bawah klavikula kanan", RED, "white"), ("LA", "kuning", "bawah klavikula kiri", YEL, "black"), ("RL", "hijau", "perut kanan bawah", GRN, "white")]
    for i, (lb, cn, loc, col, tc) in enumerate(rows):
        yy = ty - 4 - i * 11
        colour_chip(ax, tx, yy, col, lb, tc)
        ax.text(tx + 28, yy, f"{cn}: {loc}", fontsize=7.2, va="center")
    ket.begin("K-4", "Elektroda EKG 3 lead + kabel dan plug 3,5 mm")
    ket.sub("Kode warna, label, dan posisi pada tubuh")
    ket.table(["Lead", "Warna", "Fungsi", "Posisi pada tubuh"],
              [["RA", "Merah", "Right Arm (lengan kanan)", "Di bawah klavikula kanan"], ["LA", "Kuning", "Left Arm (lengan kiri)", "Di bawah klavikula kiri"],
               ["RL", "Hijau", "Right Leg (referensi)", "Perut kanan bawah, dekat krista iliaka"]], widths=[0.9, 1.2, 3.4, 4.2], align=["c", "c", "l", "l"])
    ket.sub("Bagian elektroda")
    ket.items(["Pad busa putih Ø45 mm, tebal 1,2 mm.", "Gel hidrogel biru Ø34 mm (lobus Ø19 mm di sekitar snap), tebal 0,25 mm.",
               "Konektor snap berkode warna dengan relief tarik, tinggi 6,4 mm; tinggi total elektroda 8,8 mm. Kawat abu-abu.",
               "Plug TRS 3,5 mm: barel logam 14 mm dengan 2 cincin isolator, badan 10,3 mm, relief 11 mm, diameter 6,5 mm."], numbered=True)
    ket.sub("Sumber model dan catatan keakuratan")
    ket.para("Bentuk elektroda mengacu pada model Sketchfab \"ECG Electrode Dot (single, sticky, wire)\" oleh RescueFit VLE (pad busa putih tipis, gel biru, snap krom) dan foto kabel lead yang dipakai "
             "(konektor snap berkode warna dengan relief tarik, kawat abu-abu). Geometri dibuat ulang untuk gambar ini.")
    ket.para("Ukuran pad Ø45 mm, tinggi konektor 8,8 mm, dan plug 3,5 mm adalah ukuran model. Ukur elektroda asli dengan jangka sorong. "
             "Warna kabel 3 lead AD8232: merah RA, kuning LA, hijau RL. Cocokkan dengan tulisan spidol pada konektor.")
    title_block(ax, "KOMPONEN: ELEKTRODA EKG", "Set 3 lead, tampak atas, samping, plug", 4, NPAGE, scale="Skala: sesuai dimensi", ket="K-4")
    return fig


# =============================================================== K-5 gland + saklar
def pg_gland_saklar():
    fig, ax = sheet("K-5  Cable gland PG7 (putih) dan saklar rocker KCD11", 5)
    gl, sw = S["gland"], S["switch"]
    HY = S["outer_y"][1]; swc, swz = sw["x"], sw["zc"]
    head_(ax, 12, 275, "A. Cable gland PG7 + mur")
    fit_img(ax, os.path.join(KR, "gland_iso.png"), (8, 150, 205, 270), pad=10)
    head_(ax, 12, 143, "B. Tampak samping (mm)")
    I = json.load(open(os.path.join(KR, "gland_info.json")))
    Fg = Ort(os.path.join(KR, "gland_front.png"), I["front"])
    zc = gl["zc"]
    Fg.put(ax, 108, 88, 4.6, pad=10)
    (xa, ya), (xb, yb) = Fg.P((-74.3, 0, zc - 8.7)), Fg.P((-49.3, 0, zc - 8.7))
    hdim(ax, xa, xb, ya - 6, ya, yb, "25,0")
    (xa, ya), (xb, yb) = Fg.P((-74.3, 0, zc - 8.7)), Fg.P((-62.3, 0, zc - 8.7))
    hdim(ax, xa, xb, ya - 15, ya, yb, "12,0")
    (xa, ya), (xb, yb) = Fg.P((-57.3, 0, zc - 8.7)), Fg.P((-49.3, 0, zc - 8.7))
    hdim(ax, xa, xb, ya - 15, ya, yb, "8,0")
    (x0, y0), (x1, y1) = Fg.P((-49.3, 0, zc - 6.25)), Fg.P((-49.3, 0, zc + 6.25))
    vdim(ax, x0 + 7, y0, y1, x0, x1, "Ø12,5", side="right")
    callout(ax, Fg.P((-60.0, 0, zc + 8.0)), "kepala AF 15", 4, 14)
    callout(ax, Fg.P((-68.0, 0, zc + 5.5)), "tutup", -4, 12, ha="right")
    callout(ax, Fg.P((-57.7, 0, zc - 7.0)), "seal", -10, -22, ha="right")
    callout(ax, Fg.P((-52.5, 0, zc + 6.0)), "mur", 12, 10)
    head_(ax, 215, 275, "C. Saklar rocker KCD11")
    fit_img(ax, os.path.join(KR, "saklar_iso.png"), (215, 150, 412, 270), pad=10)
    Is = json.load(open(os.path.join(KR, "saklar_info.json")))
    head_(ax, 215, 143, "D. Tampak atas (mm)")
    St = Ort(os.path.join(KR, "saklar_top.png"), Is["top"])
    St.put(ax, 312, 100, 2.6, pad=10)
    ytop, ybot = HY + 4.6, HY - sw["panel"] - sw["depth"] - 5.0
    (xa, ya), (xb, yb) = St.P((swc - 7.4, ytop, 0)), St.P((swc + 7.4, ytop, 0))
    hdim(ax, xa, xb, ya + 5, ya, yb, "14,8")
    (x0, y0), (x1, y1) = St.P((swc + 7.4, ytop, 0)), St.P((swc + 7.4, ybot, 0))
    vdim(ax, x0 + 8, y0, y1, x0, x1, f1(ytop - ybot), side="right")
    (xa, ya), (xb, yb) = St.P((swc - 6.9, ybot, 0)), St.P((swc + 6.9, ybot, 0))
    hdim(ax, xa, xb, ya - 5, ya, yb, "13,8")
    ket.begin("K-5", "Cable gland PG7 dan saklar rocker KCD11")
    ket.sub("Cable gland PG7")
    ket.items(["Ulir PG7 Ø12,5 mm, panjang ulir 8 mm; untuk kabel Ø3 - 6,5 mm (kabel PPG 4 inti Ø4,0 mm).",
               "Mur segi enam AF %s mm, tebal %s mm, ditanam di kantong dinding Kanan. Nilai ini bawaan, ukur mur yang dipakai." % (f1(gl["nut_af"]), f1(gl["nut_h"])),
               "Lubang casing Ø%s mm, tonjolan luar %s mm; pusat %s mm dari tepi Bawah casing dan Z = %s mm dari bidang belakang." % (f1(gl["hole"]), f1(gl["out"]), f1(gl["y"] - S["outer_y"][0]), f1(gl["zc"] + 3.5)),
               "Bagian: kepala segi enam AF 15,0 (tebal 5,0), tutup bergalur 12,0 mm, cincin seal, mur AF %s x %s." % (f1(gl["nut_af"] - 0.4), f1(gl["nut_h"]))], numbered=True)
    ket.sub("Saklar rocker KCD11")
    ket.items(["Rocker mini 10 x 15 mm, 2 kaki, 3 A 250 VAC / 6 A 125 VAC (tertera pada badan), snap-in dari dalam.",
               "Lubang panel %s x %s mm. Dinding Atas dipertipis menjadi %s mm dari dalam; badan butuh ruang 14 x 9 x 12,5 mm." % (f1(sw["cut_w"] + 0.1), f1(sw["cut_h"] + 0.1), f1(sw["panel"])),
               "Pusat %s mm dari tepi Kiri casing, Z = %s mm. Rocker merah bergerak miring." % (f1(52.5 - sw["x"]), f1(sw["zc"] + 3.5)),
               "Bezel 14,8 mm, badan 13,8 mm, panjang total %s mm." % f1(ytop - ybot)], numbered=True)
    ket.sub("Letak pada casing")
    ket.para("Saklar di dinding Atas (jack AD8232 di x = -12,3 mm dan saklar di x = +3,0 mm dari pusat pola baut). Gland di dinding Kanan, di bawah lubang USB-C. "
             "Kabel PPG 4 inti masuk lewat gland ke konektor 4 pin di PCB. Kabel elektroda masuk lewat jack AD8232 di sisi Atas.")
    ket.sub("Sumber model dan catatan keakuratan")
    ket.para("Gland dan saklar dimodelkan dari spesifikasi PG7 dan KCD11 serta foto komponen yang dipakai (gland putih, saklar hitam dengan rocker merah). "
             "Ukuran mur gland dan tonjolan rocker adalah perkiraan, ukur komponen asli dengan jangka sorong.")
    ket.para("Parameter casing (lubang, kantong mur, ruang saklar) diambil dari make_case.py (cover v2 final) sehingga sama dengan gambar teknik.")
    title_block(ax, "KOMPONEN: GLAND PG7 DAN SAKLAR KCD11", "Gland PG7 dan saklar rocker", 5, NPAGE, scale="Skala: sesuai dimensi", ket="K-5")
    return fig


# =============================================================== K-6 komponen pendukung
def pg_pendukung():
    fig, ax = sheet("K-6  Komponen pendukung: layar TFT, PCB utama, modul powerbank, baterai", 6)
    cards = [
        ("1. Layar TFT 3,5\" ILI9488", "tft", (12, 150, 207, 270),
         ["480 x 320 piksel, antarmuka SPI + touch. Modul 98,0 x 56,34 mm, area aktif 73,44 x 48,96 mm, kaca touch 85 x 55 x 3 mm.",
          "Tampilan pada gambar mengikuti foto layar alat (ARMOR - Aritmia Monitoring v1.0): ECG, PPG, detak jantung, SpO2, status irama."]),
        ("2. PCB utama (custom)", "pcb", (212, 150, 407, 270),
         ["98,03 x 56,16 mm, 4 lubang baut M3. Soket female ESP32 2 x 19 pin (jarak baris 25,4 mm), header AD8232 6 pin, konektor JST saklar 2 pin, konektor 4 pin PPG.",
          "Model disederhanakan dari Gerber (outline, lubang bor, soket, header)."]),
        ("3. Modul powerbank 5 V", "powerbank", (12, 62, 207, 142),
         ["Pengisian baterai dan keluaran 5 V. Port USB-C menghadap dinding Kanan (pusat 18,1 mm dari tepi Atas PCB).",
          "Modul sekitar 26,1 x 20,4 mm, tinggi komponen 12,6 mm (kapasitor tertinggi). Model dari foto dan Gerber (perkiraan)."]),
        ("4. Baterai Li-ion PALO 103450", "baterai", (212, 62, 407, 142),
         ["3,7 V 2000 mAh, 10 x 34 x 50 mm, konektor JST 2 pin (kabel merah dan hitam). Diletakkan rebah di sisi Bawah PCB.",
          "Baterai 34 mm, sedangkan ruang kosong sisi Bawah v2 hanya 27,8 mm. Lihat catatan penempatan di keterangan perakitan P-1."]),
    ]
    ket.begin("K-6", "Komponen pendukung: layar TFT, PCB utama, powerbank, baterai")
    for (nm, key, box, lines) in cards:
        x0, y0, x1, y1 = box
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=0.5, ec="#999999", zorder=1))
        ax.text(x0 + 3, y1 - 5, nm, fontsize=7.6, fontweight="bold", va="center")
        fit_img(ax, os.path.join(KR, f"{key}_iso.png"), (x0 + 2, y0 + 14, x0 + 112, y1 - 11), pad=8)
        fit_img(ax, os.path.join(KR, f"{key}_top.png"), (x0 + 113, y0 + 14, x1 - 2, y1 - 11), pad=8)
        I = json.load(open(os.path.join(KR, f"{key}_info.json")))
        bmin, bmax = I["bbox_min"], I["bbox_max"]
        dims = "%s x %s x %s mm" % (f1(bmax[0] - bmin[0], 1), f1(bmax[1] - bmin[1], 1), f1(bmax[2] - bmin[2], 1))
        ax.text(x0 + 3, y0 + 7, dims, fontsize=7.0, fontweight="bold", va="center")
        ket.sub(nm)
        ket.para("Selubung model: %s x %s x %s mm." % (f1(bmax[0] - bmin[0], 2), f1(bmax[1] - bmin[1], 2), f1(bmax[2] - bmin[2], 2)))
        ket.items(lines)
    ket.sub("Sumber model dan catatan keakuratan")
    ket.para("TFT, PCB utama, powerbank, dan baterai adalah model sederhana untuk cek kecocokan (bentuk dasar dan komponen terbesar). Ukuran luar diambil dari lembar data, Gerber, dan hasil ukur fisik.")
    ket.para("Detail kecil (konektor, kapasitor) hanya ilustrasi. Datasheet resmi tetap acuan.")
    title_block(ax, "KOMPONEN: PENDUKUNG", "TFT, PCB utama, powerbank, baterai", 6, NPAGE, scale="Skala: sesuai dimensi", ket="K-6")
    return fig


if __name__ == "__main__":
    pages = [pg_esp32(), pg_ad8232(), pg_hw605(), pg_elektroda(), pg_gland_saklar(), pg_pendukung()]
    names = ["K1_ESP32_DevKitC_V4", "K2_AD8232", "K3_MAX30102_HW605", "K4_Elektroda_EKG", "K5_Gland_PG7_Saklar_KCD11", "K6_Komponen_Pendukung"]
    ket.save(os.path.join(OUTD, "ket_komponen.json"))
    with PdfPages(os.path.join(OUTD, "Gambar_Komponen_A3.pdf")) as pdf:
        for f in pages:
            pdf.savefig(f, dpi=250)
    for f, n in zip(pages, names):
        f.savefig(os.path.join(OUTD, f"Gambar_Komponen_{n}_A3.png"), dpi=200)
        plt.close(f)
    print("OK")
