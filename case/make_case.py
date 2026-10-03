"""
Cover alat ECG + PPG (ESP32 + TFT ILI9488 3.5" + PCB custom)  -  generator Blender (bpy)   [v2 + varian v3 --bay]

Jalankan:   python make_case.py -- <folder_output> [--bay]     (--bay = v3: ruang baterai tanpa menumpuk)
Satuan  :   1 unit Blender = 1 mm

SISTEM KOORDINAT MODEL (dilihat dari DEPAN / sisi layar):
    +X = arah KIRI   (kanan di foto 1)      -X = KANAN
    +Y = arah ATAS                          -Y = BAWAH
    +Z = arah DEPAN (layar)                  Z=0 = ujung ekor baut belakang (bidang paling belakang tumpukan)
Titik (0,0) = pusat pola 4 lubang baut M3 (dari Gerber).

Konversi Gerber -> model:  X = -(Xg - 56.007)   Y = -(Yg - 33.655)
(PCB di Gerber ternyata terpasang diputar 180 derajat terhadap tampilan atas Gerber;
 terbukti dari posisi konektor PPG, port USB-C, header TFT dan micro-USB ESP32 pada foto.)

Perubahan v2: gland PG7 (tonjolan kecil), saklar KCD11 datar tanpa pod, sayap slot sabuk di back plate,
chamfer/rounding ergonomis, boss sekrup diperkuat.
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else (sys.argv[1] if len(sys.argv) > 1 else ".")
os.makedirs(OUT, exist_ok=True)
BAY_ON = "--bay" in sys.argv          # v3: rongga sisi BAWAH diperlebar supaya baterai 10x34x50 muat tanpa menumpuk modul
RAKIT_ON = "--rakit" in sys.argv      # dapat dirakit: tumpukan TFT+PCB masuk LURUS dari belakang (tanpa boss di dinding),
                                      # plate dikunci 4 sekrup SAMPING ke lug di plate, alur di dinding untuk konektor yang menjorok

# =============================================================== PARAMETER ==
# ---- dari Gerber ----------------------------------------------------------
HOLES_G = [(10.160, 9.017), (10.160, 58.293), (101.854, 9.017), (101.854, 58.293)]  # lubang M3 (NPTH 3.0)
XH = sum(h[0] for h in HOLES_G) / 4          # 56.007
YH = sum(h[1] for h in HOLES_G) / 4          # 33.655
PCB_G = dict(x0=7.00023, x1=105.029, y0=5.842, y1=61.99886)   # outline PCB hijau (garis tengah GKO)


def mx(xg): return -(xg - XH)
def my(yg): return -(yg - YH)


MOUNT = [(mx(x), my(y)) for x, y in HOLES_G]                   # (+-45.85, +-24.64)
PCB = dict(x0=mx(PCB_G["x1"]), x1=mx(PCB_G["x0"]), y0=my(PCB_G["y1"]), y1=my(PCB_G["y0"]))
TFT_W, TFT_H = 98.00, 56.34                                    # PCB modul TFT (datasheet)
GLASS_W, GLASS_H, GLASS_CX = 85.0, 55.0, -0.5                  # kaca touch (ukuran Anda); sedikit bergeser ke Kanan
AA_W, AA_H = 73.44, 48.96                                      # area aktif (datasheet)

# ---- tumpukan Z (dari ujung ekor baut = 0) --------------------------------
TAIL = 5.0                    # panjang ekor baut bawah (termasuk mur)
PCB_T = 1.6
SPACER = 20.0
GLASS_T = 3.0                 # kaca touch + kepala baut atas = 3 mm
Z_PCB0, Z_PCB1 = TAIL, TAIL + PCB_T                 # 5.0 .. 6.6
Z_TFT0 = Z_PCB1 + SPACER                            # 26.6
Z_TFT1 = Z_TFT0 + PCB_T                             # 28.2
Z_FRONT = Z_TFT1 + GLASS_T                          # 31.2  (permukaan kaca)

# ---- rumah ---------------------------------------------------------------
WALL = 3.0
CAV_HX, CAV_HY = 49.5, 28.75                        # rongga 99.0 x 57.5 (celah >= 0.4 mm tiap sisi)
CAV_R, OUT_R = 0.5, 5.0                             # sudut luar R5 (nyaman di badan)
CH = 1.2                                            # chamfer 45 derajat sisi depan shell & sisi belakang plate
Z_SPLIT = -0.5                                      # lantai rongga / bidang belah shell-plate
FRONT_GAP = 0.3
Z_CAV_TOP = Z_FRONT + FRONT_GAP                     # 31.5
FRONT_T = 2.4
Z_TOP = Z_CAV_TOP + FRONT_T                         # 33.9
PLATE_T = 3.0
Z_PLATE0 = Z_SPLIT - PLATE_T                        # -3.5
OUT_HX, OUT_HY = CAV_HX + WALL, CAV_HY + WALL       # 52.5 x 31.75  (OUT_HY / CAV_HY = dinding ATAS)

# ---- v3: ruang baterai di sisi BAWAH ----------------------------------------
# Baterai PALO 103450 (10 x 34 x 50 mm) rebah di atas PCB. Sisi 34 mm sejajar Atas-Bawah, tepi Atas baterai berhenti 0.6 mm
# sebelum tepi Bawah modul AD8232/powerbank (Y = -0.5), sisanya menjorok keluar tepi Bawah PCB; rongga Bawah diperlebar.
BAT = dict(x0=-41.5, x1=8.5, w=34.0, t=10.0, gap_mod=0.6, gap_wall=0.4, y_mod_edge=-0.5)
BAT["y1"] = BAT["y_mod_edge"] - BAT["gap_mod"]                      # -1.1
BAT["y0"] = BAT["y1"] - BAT["w"]                                    # -35.1
BAT["z0"], BAT["z1"] = Z_PCB1, Z_PCB1 + BAT["t"]                    # 6.6 .. 16.6
BAY = (-(BAT["y0"] - BAT["gap_wall"]) - CAV_HY) if BAY_ON else 0.0  # tambahan rongga di sisi Bawah (6.75 mm)
CAV_YT, CAV_YB = CAV_HY, -(CAV_HY + BAY)                            # dinding dalam Atas / Bawah
OUT_YT, OUT_YB = CAV_YT + WALL, CAV_YB - WALL
CAV_CY, CAV_HYH = (CAV_YT + CAV_YB) / 2, (CAV_YT - CAV_YB) / 2     # pusat & setengah tinggi rongga
OUT_CY, OUT_HYH = (OUT_YT + OUT_YB) / 2, (OUT_YT - OUT_YB) / 2


def wall_y(side): return CAV_YT if side > 0 else CAV_YB             # muka dalam dinding Atas (+1) / Bawah (-1)


HOLE_TOL = 0.2                                     # kompensasi cetak (lubang jadi lebih kecil di printer)

WIN_W, WIN_H, WIN_CX, WIN_CY, WIN_R = 79.0, 52.0, GLASS_CX, 0.0, 2.0

# ---- lubang tetap (posisi dari Gerber + ukuran Anda) -----------------------
MICRO = dict(x=mx(27.686), zc=17.0, w=12.0, h=8.0)            # BAWAH: dinding Y-  (13..21 mm dari belakang)
JACK = dict(x=mx(68.326), zc=15.0, d=7.0)                      # ATAS : dinding Y+  (kabel jack 5-6 mm)
USBC = dict(y=my(23.936), zc=9.65, w=10.4, h=4.6)             # KANAN: dinding X-  (port 8.0 .. 11.3 mm dari belakang)
# gland PG7: ulir 12.5 mm, panjang ulir 8 mm, kabel 3-6.5 mm.  nut_af/nut_h = UKUR mur gland Anda (default PG7 umum)
GLAND = dict(y=my(45.85), zc=13.2, hole=12.8, nut_af=15.4, nut_h=4.4, pocket=5.2, plate=2.6)
GLAND["out"] = GLAND["pocket"] + GLAND["plate"] - WALL        # tonjolan ke luar dinding (4.8 mm)
# saklar KCD11 mini 10x15 mm: lubang panel 14 x 9, badan 12.5 mm di belakang panel, tonjolan rocker ~4 mm
SWITCH = dict(x=3.0, zc=21.0, cut_w=14.0, cut_h=9.0, rec_w=16.6, rec_h=11.2, panel=1.6, depth=12.5)

# ---- baut penutup plate (M3 x 8 flat head, ke boss di dinding panjang) ------
SCREW_X = [23.0, -23.0]
BOSS_W, BOSS_IN, BOSS_TOP = 10.0, 6.0, 4.3
PILOT_D, CLEAR_D, CSK_D, CSK_DEPTH, SCREW_LEN = 2.7, 3.4, 6.4, 1.6, 8.0

# ---- varian --rakit: sekrup samping ------------------------------------------------------------------------
# Boss sekrup di dinding (BOSS_*) menghalangi PCB/TFT (lebar 56 mm vs celah 45 mm di antara boss) sehingga tumpukan tidak bisa
# dimasukkan dari belakang. Di varian ini boss dipindah ke back plate (LUG) dan plate dikunci dengan 4 sekrup M3 dari SAMPING
# (menembus dinding Atas/Bawah, masuk ke lug). Kepala sekrup bulat (pan/button) duduk di permukaan dinding (tanpa countersink).
RAKIT = dict(z=2.0, clear_d=3.4, pilot_d=2.6, lug_w=9.0, lug_in=6.4, lug_top=4.4, lug_gap=0.25, pilot_depth=5.2,
             screw_len=8.0, head_d=5.6, head_h=2.3, groove_clear=0.25, groove_side=0.3)
# posisi 4 sekrup samping (x, sisi). Atas (+Y): x = +-23. Bawah (-Y): x = +-23 (v3, rongga Bawah lebar, tanpa alur) atau x = +-9
# (v2: alur micro-USB di x = 24.1 ... 32.5 terlalu dekat ke x = 23; x = +-9 juga bebas dari kaki soket ESP32 di x = 15.6 dan
# dari rusuk/stopper penyangga baterai v3 tidak relevan karena v3 memakai +-23).
RAKIT_POS = [(23.0, +1), (-23.0, +1)] + ([(23.0, -1), (-23.0, -1)] if BAY_ON else [(9.0, -1), (-9.0, -1)])

# ---- tiang penyangga PCB di back plate ------------------------------------
POST_OD, POST_ID = 10.0, 7.2

# ---- sayap slot sabuk (back plate) -------------------------------------------
WING = 14.0                         # panjang sayap tiap ujung
BELT_SLOT_W, BELT_SLOT_L = 6.0, 44.0   # slot: sabuk tebal <= 4.5 mm, lebar <= 40 mm
BELT_SLOT_OFF = 3.5                 # jarak tepi dalam slot dari dinding shell

# ============================================================ HELPER BLENDER ==
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 0.001
scene.unit_settings.length_unit = "MILLIMETERS"
COL_MAIN = bpy.data.collections.new("Rumah")
COL_GHOST = bpy.data.collections.new("Referensi_Komponen")
scene.collection.children.link(COL_MAIN)
scene.collection.children.link(COL_GHOST)


def _obj(name, bm, coll):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _map(axis, p, q, a):
    if axis == "Z": return (p, q, a)
    if axis == "Y": return (p, a, q)
    if axis == "X": return (a, p, q)


def prism(name, pts, a0, a1, axis="Z", coll=None):
    """poligon (p,q) di-ekstrusi sepanjang `axis` dari a0 ke a1."""
    coll = coll or COL_MAIN
    bm = bmesh.new()
    lo = [bm.verts.new(_map(axis, p, q, a0)) for p, q in pts]
    hi = [bm.verts.new(_map(axis, p, q, a1)) for p, q in pts]
    n = len(pts)
    bm.faces.new(lo)
    bm.faces.new(hi[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return _obj(name, bm, coll)


def loft(name, rings, coll=None):
    """rings = [(pts, z), ...] dengan jumlah titik sama; menghasilkan benda tertutup (untuk chamfer)."""
    coll = coll or COL_MAIN
    bm = bmesh.new()
    vr = [[bm.verts.new((p, q, z)) for p, q in pts] for pts, z in rings]
    n = len(rings[0][0])
    bm.faces.new(vr[0])
    bm.faces.new(vr[-1][::-1])
    for a, b in zip(vr[:-1], vr[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([a[i], a[j], b[j], b[i]])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return _obj(name, bm, coll)


def rrect(cx, cy, hx, hy, r, n=12):
    r = min(r, hx, hy)
    if r <= 1e-6:
        return [(cx + hx, cy + hy), (cx - hx, cy + hy), (cx - hx, cy - hy), (cx + hx, cy - hy)]
    pts = []
    for (sx, sy, a0) in [(1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)]:
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((cx + sx * (hx - r) + r * math.cos(a), cy + sy * (hy - r) + r * math.sin(a)))
    return pts


def circle(cx, cy, r, n=64):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def hexagon(cx, cy, af, corners_on_q=True):
    R = af / math.sqrt(3)
    off = 90 if corners_on_q else 0
    return [(cx + R * math.cos(math.radians(off + 60 * k)), cy + R * math.sin(math.radians(off + 60 * k))) for k in range(6)]


def box(name, x0, x1, y0, y1, z0, z1, coll=None):
    return prism(name, [(x1, y1), (x0, y1), (x0, y0), (x1, y0)], z0, z1, "Z", coll)


def cyl(name, c1, c2, r, a0, a1, axis, n=64, coll=None):
    """silinder sumbu `axis`; (c1,c2) = koordinat dua sumbu lain ( Z:(x,y)  Y:(x,z)  X:(y,z) )."""
    return prism(name, circle(c1, c2, r, n), a0, a1, axis, coll)


def frustum(name, cx, cy, r0, r1, z0, z1, n=48):
    bm = bmesh.new()
    lo = [bm.verts.new((cx + r0 * math.cos(2 * math.pi * k / n), cy + r0 * math.sin(2 * math.pi * k / n), z0)) for k in range(n)]
    hi = [bm.verts.new((cx + r1 * math.cos(2 * math.pi * k / n), cy + r1 * math.sin(2 * math.pi * k / n), z1)) for k in range(n)]
    bm.faces.new(lo)
    bm.faces.new(hi[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
    return _obj(name, bm, COL_MAIN)


def _select_only(ob):
    for o in list(bpy.context.scene.objects):
        if o is not None:
            o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)


def bop(target, cutter, op="DIFFERENCE"):
    mod = target.modifiers.new("b", "BOOLEAN")
    mod.operation = op
    mod.object = cutter
    mod.solver = "MANIFOLD"
    _select_only(target)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return target


def union_all(target, parts):
    for p in parts:
        bop(target, p, "UNION")


def cut_all(target, parts):
    for p in parts:
        bop(target, p, "DIFFERENCE")


# ============================================================ SHELL (DEPAN) ==
N_RR = 12
shell = loft("Cover_Depan_Shell", [
    (rrect(0, OUT_CY, OUT_HX, OUT_HYH, OUT_R, N_RR), Z_SPLIT),
    (rrect(0, OUT_CY, OUT_HX, OUT_HYH, OUT_R, N_RR), Z_TOP - CH),
    (rrect(0, OUT_CY, OUT_HX - CH, OUT_HYH - CH, OUT_R - CH, N_RR), Z_TOP)])

# --- boss gland PG7 (sisi KANAN, -X): blok kecil dengan kantong mur segi-enam dari dalam
g = GLAND
gy, gz = g["y"], g["zc"]
g_hy = g["nut_af"] / 2 + 2.2
g_hz = g["nut_af"] / math.sqrt(3) + 2.2
g_zlo, g_zhi = gz - g_hz, gz + g_hz
U = g["out"]


def gx(u): return -(OUT_HX + u)          # u = jarak ke luar dari muka luar dinding Kanan


boss_g = prism("boss_gland",
               [(gx(-WALL), g_zlo), (gx(U), g_zlo), (gx(U), g_zhi), (gx(0), g_zhi + U), (gx(-WALL), g_zhi + U)],
               gy - g_hy, gy + g_hy, "Y")

# --- boss sekrup penutup (di bawah PCB, menempel di dinding Atas/Bawah)
screw_pos = []
boss_blocks = []
for sxp in SCREW_X:
    for side in (+1, -1):
        wall_in = wall_y(side)
        y_a, y_b = sorted([wall_in + side * 0.3, wall_in - side * BOSS_IN])
        if not RAKIT_ON:
            boss_blocks.append(box("boss_sekrup", sxp - BOSS_W / 2, sxp + BOSS_W / 2, y_a, y_b, Z_SPLIT, BOSS_TOP))
        screw_pos.append((sxp, wall_in - side * 3.5))

union_all(shell, [boss_g])        # (boss sekrup ditambah SETELAH rongga dipotong, kalau tidak ikut terhapus)

# --- rongga utama + jendela layar
cav = prism("cav", rrect(0, CAV_CY, CAV_HX, CAV_HYH, CAV_R), Z_SPLIT - 0.2, Z_CAV_TOP)
win = prism("win", rrect(WIN_CX, WIN_CY, WIN_W / 2, WIN_H / 2, WIN_R), Z_CAV_TOP - 0.5, Z_TOP + 0.5)
cut_all(shell, [cav, win])
union_all(shell, boss_blocks)

# --- lubang sisi BAWAH (-Y): micro-USB ESP32
m = MICRO
cut_all(shell, [box("micro", m["x"] - (m["w"] + HOLE_TOL) / 2, m["x"] + (m["w"] + HOLE_TOL) / 2,
                    OUT_YB - 0.5, CAV_YB + 0.5, m["zc"] - (m["h"] + HOLE_TOL) / 2, m["zc"] + (m["h"] + HOLE_TOL) / 2)])

# --- lubang sisi ATAS (+Y): jack AD8232
j = JACK
cut_all(shell, [cyl("jack", j["x"], j["zc"], (j["d"] + HOLE_TOL) / 2, CAV_HY - 0.5, OUT_HY + 0.5, "Y")])

# --- saklar KCD11 datar: jendela panel 14x9 + lekuk tipis dari dalam (panel 1.6 mm untuk snap-in)
s = SWITCH
y_panel_in = OUT_HY - s["panel"]
rec = box("rec", s["x"] - s["rec_w"] / 2, s["x"] + s["rec_w"] / 2, CAV_HY - 0.5, y_panel_in,
          s["zc"] - s["rec_h"] / 2, s["zc"] + s["rec_h"] / 2)
swc = box("swc", s["x"] - (s["cut_w"] + 0.1) / 2, s["x"] + (s["cut_w"] + 0.1) / 2, y_panel_in - 0.1, OUT_HY + 0.5,
          s["zc"] - (s["cut_h"] + 0.1) / 2, s["zc"] + (s["cut_h"] + 0.1) / 2)
cut_all(shell, [rec, swc])

# --- lubang sisi KANAN (-X): USB-C powerbank
u = USBC
cut_all(shell, [box("usbc", -OUT_HX - 0.5, -CAV_HX + 0.5, u["y"] - (u["w"] + HOLE_TOL) / 2, u["y"] + (u["w"] + HOLE_TOL) / 2,
                    u["zc"] - (u["h"] + HOLE_TOL) / 2, u["zc"] + (u["h"] + HOLE_TOL) / 2)])

# --- gland PG7: kantong mur segi-enam (dari dalam) + lubang ulir
x_pocket_in = -CAV_HX + 0.1
x_pocket_bot = gx(g["pocket"] - WALL)
pocket = prism("pocket", hexagon(gy, gz, g["nut_af"], True), x_pocket_bot, x_pocket_in, "X")
ghole = cyl("ghole", gy, gz, g["hole"] / 2, gx(U) - 0.5, x_pocket_bot + 0.1, "X")
cut_all(shell, [pocket, ghole])

# --- lubang pilot sekrup penutup (tembus ke atas boss supaya M3x8 tidak mentok)
if not RAKIT_ON:
    pilots = [cyl("pilot", px, py, PILOT_D / 2, Z_SPLIT - 0.2, BOSS_TOP + 0.2, "Z", n=32) for px, py in screw_pos]
    cut_all(shell, pilots)
else:
    # lubang tembus sekrup samping (dari luar dinding Atas/Bawah ke rongga) + alur dalam dinding untuk konektor yang menjorok
    R_ = RAKIT
    cut_all(shell, [cyl("sidehole", sxp, R_["z"], R_["clear_d"] / 2, min(wall_y(sd), wall_y(sd) + sd * (WALL + 0.5)) - 0.0,
                        max(wall_y(sd), wall_y(sd) + sd * (WALL + 0.5)), "Y", n=32)
                    for sxp, sd in RAKIT_POS])
    GROOVES = []
    # hidung jack AD8232 (Y+): laras Ø6 menembus ke dinding, alur dari bidang belah sampai lubang jack
    nose_y = my(3.977)
    d_ = max(0.0, nose_y - CAV_YT)
    if d_ > 0:
        GROOVES.append(dict(nama="jack", x=[JACK["x"] - 3.0 - R_["groove_side"], JACK["x"] + 3.0 + R_["groove_side"]],
                            y=[CAV_YT - 0.5, CAV_YT + d_ + R_["groove_clear"]], z=[Z_SPLIT - 0.2, JACK["zc"]]))
    # soket micro-USB ESP32 (Y-): badan 7.8 mm menjorok ke dinding
    usb_y = my(63.9)
    d_ = max(0.0, CAV_YB - usb_y)
    if d_ > 0:
        GROOVES.append(dict(nama="micro", x=[MICRO["x"] - 3.9 - R_["groove_side"], MICRO["x"] + 3.9 + R_["groove_side"]],
                            y=[CAV_YB - d_ - R_["groove_clear"], CAV_YB + 0.5], z=[Z_SPLIT - 0.2, MICRO["zc"]]))
    # port USB-C powerbank (X-): menjorok ke dinding Kanan
    usbc_x = mx(106.1)
    d_ = max(0.0, -CAV_HX - usbc_x)
    if d_ > 0:
        GROOVES.append(dict(nama="usbc", x=[-CAV_HX - d_ - R_["groove_clear"], -CAV_HX + 0.5],
                            y=[my(28.2) - R_["groove_side"], my(19.3) + R_["groove_side"]], z=[Z_SPLIT - 0.2, USBC["zc"]]))
    cut_all(shell, [box("alur_" + g_["nama"], g_["x"][0], g_["x"][1], g_["y"][0], g_["y"][1], g_["z"][0], g_["z"][1]) for g_ in GROOVES])

# ============================================================ BACK PLATE =====
PX, PY = OUT_HX + WING, OUT_HYH                     # plate + sayap = satu persegi panjang membulat
PR = 6.0
plate = loft("Cover_Belakang_BackPlate", [
    (rrect(0, OUT_CY, PX - CH, PY - CH, PR - CH, N_RR), Z_PLATE0),
    (rrect(0, OUT_CY, PX, PY, PR, N_RR), Z_PLATE0 + CH),
    (rrect(0, OUT_CY, PX, PY, PR, N_RR), Z_SPLIT)])

# rim penengah (masuk rongga, celah 0.2 mm), dipotong di sekitar boss sekrup dan sudut
rim_o = prism("rim_o", rrect(0, CAV_CY, CAV_HX - 0.2, CAV_HYH - 0.2, 0.3), Z_SPLIT - 0.01, Z_SPLIT + 2.0)
rim_i = prism("rim_i", rrect(0, CAV_CY, CAV_HX - 1.4, CAV_HYH - 1.4, 0.3), Z_SPLIT - 0.1, Z_SPLIT + 2.1)
bop(rim_o, rim_i, "DIFFERENCE")
for sxp in SCREW_X:
    for side in (+1, -1):
        wall_in = wall_y(side)
        y_a, y_b = sorted([wall_in + side * 1.0, wall_in - side * (BOSS_IN + 0.5)])
        bop(rim_o, box("rimcut", sxp - BOSS_W / 2 - 0.5, sxp + BOSS_W / 2 + 0.5, y_a, y_b, Z_SPLIT - 0.2, Z_SPLIT + 2.3))
for sx in (+1, -1):                    # rim dibuang di 4 sudut (area tiang) agar tidak ada sliver tipis
    for sy in (+1, -1):
        xa, xb = sorted([sx * (CAV_HX - 8.0), sx * (CAV_HX + 1.0)])
        ya, yb = sorted([sy * (CAV_HY - 8.0), wall_y(sy) + sy * 1.0])   # ujung rim berhenti di dalam area tiang (sama seperti sisi Atas)
        bop(rim_o, box("rimcorner", xa, xb, ya, yb, Z_SPLIT - 0.2, Z_SPLIT + 2.3))
union_all(plate, [rim_o])

# tiang penyangga PCB (cincin berongga untuk ekor baut + mur), dipangkas oleh dinding rongga
for k, (px, py) in enumerate(MOUNT):
    post = cyl(f"post{k}", px, py, POST_OD / 2, Z_SPLIT - 0.01, Z_PCB0, "Z", n=64)
    clip = prism(f"clip{k}", rrect(0, CAV_CY, CAV_HX - 0.6, CAV_HYH - 0.6, 0.3), Z_SPLIT - 0.3, Z_PCB0 + 0.5)
    bop(post, clip, "INTERSECT")
    sx, sy = (1 if px > 0 else -1), (1 if py > 0 else -1)
    xa, xb = sorted([px + sx * 1.5, px + sx * 9.0])
    ya, yb = sorted([py + sy * 1.5, py + sy * 9.0])
    bop(post, box(f"tip{k}", xa, xb, ya, yb, Z_SPLIT - 0.5, Z_PCB0 + 0.5), "DIFFERENCE")
    bop(plate, post, "UNION")
for k, (px, py) in enumerate(MOUNT):   # rongga ekor baut + mur juga memotong rim penengah
    bop(plate, cyl(f"hollow{k}", px, py, POST_ID / 2, Z_SPLIT, Z_PCB0 + 0.2, "Z", n=64))

# lubang sekrup + countersink (M3 flat head)
LUGS = []
if not RAKIT_ON:
    for px, py in screw_pos:
        bop(plate, cyl("thru", px, py, CLEAR_D / 2, Z_PLATE0 - 0.2, Z_SPLIT + 0.2, "Z", n=32))
        bop(plate, frustum("csk", px, py, CSK_D / 2 + 0.1, CLEAR_D / 2, Z_PLATE0 - 0.1, Z_PLATE0 + CSK_DEPTH))
else:
    # lug (pengganti boss di dinding): blok di bawah PCB menempel dinding Atas/Bawah, lubang pilot horizontal untuk sekrup samping
    R_ = RAKIT
    for sxp, sd in RAKIT_POS:
        y_out = wall_y(sd) - sd * R_["lug_gap"]                           # muka luar lug (celah 0.25 mm ke dinding)
        y_in = y_out - sd * R_["lug_in"]
        ya, yb = sorted([y_out, y_in])
        union_all(plate, [box("lug", sxp - R_["lug_w"] / 2, sxp + R_["lug_w"] / 2, ya, yb, Z_SPLIT - 0.01, R_["lug_top"])])
        y_p = y_out - sd * R_["pilot_depth"]
        pa, pb = sorted([y_out + sd * 0.3, y_p])
        bop(plate, cyl("pilot_lug", sxp, R_["z"], R_["pilot_d"] / 2, pa, pb, "Y", n=24))
        LUGS.append(dict(x=sxp, side=sd, y=[ya, yb], top=R_["lug_top"], pilot_y=[pa, pb]))

# slot sabuk (2): lubang vertikal (sumbu Z) di sayap -> sabuk turun lewat slot, lewat di belakang plate, naik lewat slot lain
SLOT_CX = OUT_HX + BELT_SLOT_OFF + BELT_SLOT_W / 2
for sgn in (+1, -1):
    bop(plate, prism("slot_sabuk", rrect(sgn * SLOT_CX, OUT_CY, BELT_SLOT_W / 2, BELT_SLOT_L / 2, BELT_SLOT_W / 2, 10),
                     Z_PLATE0 - 0.5, Z_SPLIT + 0.5))

# v3: penyangga baterai di back plate (hanya bagian yang menjorok keluar tepi Bawah PCB).
# Rusuk vertikal dari lantai plate sampai tepat di bawah alas baterai (celah 0.15 mm) + 2 stopper di kedua ujung baterai.
CRADLE = None
if BAY_ON:
    rib_y0 = CAV_YB + 1.0                                   # menyatu dengan rim Bawah
    rib_y1 = PCB["y0"] - 0.5                                # berhenti 0.5 mm sebelum tepi Bawah PCB
    rib_top = BAT["z0"] - 0.15
    RIB_X, RIB_W = (-37.0, -12.0, 3.0), 2.4
    for k, rx_ in enumerate(RIB_X):
        union_all(plate, [box(f"rib{k}", rx_ - RIB_W / 2, rx_ + RIB_W / 2, rib_y0, rib_y1, Z_SPLIT - 0.01, rib_top)])
    STOP_W, STOP_TOP = 2.0, BAT["z0"] + 5.0
    stop_y0, stop_y1 = CAV_YB + 1.0, CAV_YB + 1.0 + 3.8      # pendek (3.8 mm) supaya jauh dari tiang PCB
    for k, (xa, xb) in enumerate(((BAT["x0"] - BAT["gap_wall"] - STOP_W, BAT["x0"] - BAT["gap_wall"]),
                                  (BAT["x1"] + BAT["gap_wall"], BAT["x1"] + BAT["gap_wall"] + STOP_W))):
        union_all(plate, [box(f"stop{k}", xa, xb, stop_y0, stop_y1, Z_SPLIT - 0.01, STOP_TOP)])
    CRADLE = dict(ribs_x=list(RIB_X), rib_w=RIB_W, y=[rib_y0, rib_y1], top=rib_top, stop_w=STOP_W, stop_top=STOP_TOP, stop_y=[stop_y0, stop_y1])

# ============================================================ REFERENSI (ghost) ==
ghosts = {}


def ghost(name, ob, color):
    ob.name = "Ref_" + name
    ghosts[name] = ob
    mat = bpy.data.materials.new("m_" + name)
    mat.diffuse_color = color
    ob.data.materials.append(mat)
    ob.display_type = "WIRE"          # komponen referensi tampil sebagai kerangka kawat di viewport
    return ob


ghost("PCB_hijau", box("g", PCB["x0"], PCB["x1"], PCB["y0"], PCB["y1"], Z_PCB0, Z_PCB1, COL_GHOST), (0.05, 0.45, 0.15, 1))
ghost("TFT_PCB", box("g", -TFT_W / 2, TFT_W / 2, -TFT_H / 2, TFT_H / 2, Z_TFT0, Z_TFT1, COL_GHOST), (0.7, 0.05, 0.05, 1))
ghost("Kaca_touch", box("g", GLASS_CX - GLASS_W / 2, GLASS_CX + GLASS_W / 2, -GLASS_H / 2, GLASS_H / 2, Z_TFT1, Z_FRONT, COL_GHOST),
      (0.05, 0.05, 0.08, 1))
ghost("Area_aktif", box("g", GLASS_CX - AA_W / 2, GLASS_CX + AA_W / 2, -AA_H / 2, AA_H / 2, Z_FRONT - 0.05, Z_FRONT, COL_GHOST),
      (0.2, 0.5, 0.9, 1))
sp_parts = []
for k, (px, py) in enumerate(MOUNT):
    sp_parts.append(cyl(f"sp{k}", px, py, 2.75, Z_PCB1, Z_TFT0, "Z", n=32, coll=COL_GHOST))
    sp_parts.append(cyl(f"tail{k}", px, py, 3.2, 0.0, Z_PCB0, "Z", n=32, coll=COL_GHOST))
    sp_parts.append(cyl(f"head{k}", px, py, 3.0, Z_TFT1, Z_FRONT, "Z", n=32, coll=COL_GHOST))
base = sp_parts[0]
for p_ in sp_parts[1:]:
    bop(base, p_, "UNION")
ghost("Baut_spacer", base, (0.85, 0.65, 0.15, 1))
# sekrup penutup M3x8 flat head (kepala rata dengan sisi belakang plate)
scr = None
if not RAKIT_ON:
    for k, (px, py) in enumerate(screw_pos):
        a = cyl(f"s{k}", px, py, 1.5, Z_PLATE0, Z_PLATE0 + SCREW_LEN, "Z", n=24, coll=COL_GHOST)
        h = frustum(f"h{k}", px, py, CSK_D / 2, 1.5, Z_PLATE0, Z_PLATE0 + 1.6)
        COL_MAIN.objects.unlink(h); COL_GHOST.objects.link(h)
        bop(a, h, "UNION")
        if scr is None: scr = a
        else: bop(scr, a, "UNION")
    ghost("Sekrup_M3x8", scr, (0.7, 0.7, 0.75, 1))
else:
    # sekrup samping M3 x 8 kepala bulat: kepala di permukaan luar dinding, batang menembus dinding dan masuk lug
    R_ = RAKIT
    for k, (sxp, sd) in enumerate(RAKIT_POS):
        y_surf = (OUT_YT if sd > 0 else OUT_YB)
        sh_ = cyl(f"ss{k}", sxp, R_["z"], 1.5, min(y_surf, y_surf - sd * R_["screw_len"]), max(y_surf, y_surf - sd * R_["screw_len"]), "Y", n=24, coll=COL_GHOST)
        hd_ = cyl(f"sh{k}", sxp, R_["z"], R_["head_d"] / 2, min(y_surf, y_surf + sd * R_["head_h"]), max(y_surf, y_surf + sd * R_["head_h"]), "Y", n=24, coll=COL_GHOST)
        bop(sh_, hd_, "UNION")
        if scr is None: scr = sh_
        else: bop(scr, sh_, "UNION")
    ghost("Sekrup_samping_M3", scr, (0.7, 0.7, 0.75, 1))
if BAY_ON:
    ghost("Baterai_PALO103450", box("g", BAT["x0"], BAT["x1"], BAT["y0"], BAT["y1"], BAT["z0"], BAT["z1"], COL_GHOST), (0.95, 0.75, 0.1, 1))
# konektor
ghost("microUSB_ESP32", box("g", m["x"] - 3.9, m["x"] + 3.9, my(63.9), my(57.8), 16.5, 19.1, COL_GHOST), (0.7, 0.7, 0.75, 1))
ghost("USBC_powerbank", box("g", mx(106.1), mx(98.8), my(28.2), my(19.3), 8.0, 11.3, COL_GHOST), (0.7, 0.7, 0.75, 1))
jk = cyl("g", j["x"], j["zc"], 3.0, my(3.977) - 8, my(3.977), "Y", coll=COL_GHOST)
bop(jk, cyl("g2", j["x"], j["zc"], 3.25, my(3.977), my(3.977) + 12, "Y", coll=COL_GHOST), "UNION")
ghost("Plug_jack_AD8232", jk, (0.1, 0.1, 0.1, 1))
sw = box("g", s["x"] - 6.9, s["x"] + 6.9, y_panel_in - s["depth"], y_panel_in, s["zc"] - 4.5, s["zc"] + 4.5, COL_GHOST)
ghost("Badan_saklar_KCD11", sw, (0.1, 0.1, 0.1, 1))
gl = cyl("g", gy, gz, 6.25, gx(U), gx(U - 8.0), "X", coll=COL_GHOST)           # ulir PG7 12.5 mm, panjang 8 mm
nut = prism("g", hexagon(gy, gz, g["nut_af"] - 0.4, True), gx(g["pocket"] - WALL - g["nut_h"]), gx(g["pocket"] - WALL), "X", COL_GHOST)
bop(gl, nut, "UNION")
ghost("Gland_PG7_+_mur", gl, (0.2, 0.2, 0.6, 1))

# ============================================================ WARNA + EKSPOR ==
for ob, col in ((shell, (0.85, 0.85, 0.88, 1)), (plate, (0.35, 0.37, 0.4, 1))):
    mat = bpy.data.materials.new("m_" + ob.name)
    mat.diffuse_color = col
    ob.data.materials.append(mat)
    for poly in ob.data.polygons:
        poly.use_smooth = False


def export_stl(ob, path, rot_x180=False, shift_z=0.0):
    tmp = ob.copy()
    tmp.data = ob.data.copy()
    bpy.context.scene.collection.objects.link(tmp)
    if rot_x180:
        tmp.data.transform(Matrix.Rotation(math.pi, 4, "X"))
    tmp.data.transform(Matrix.Translation((0, 0, shift_z)))
    _select_only(tmp)
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, global_scale=1.0, apply_modifiers=True)
    bpy.data.objects.remove(tmp, do_unlink=True)


export_stl(shell, os.path.join(OUT, "1_Shell_Depan_siap_cetak.stl"), rot_x180=True, shift_z=Z_TOP)       # layar menghadap meja
export_stl(plate, os.path.join(OUT, "2_BackPlate_siap_cetak.stl"), shift_z=-Z_PLATE0)                     # sisi luar menghadap meja
chk = os.path.join(OUT, "_ref")
os.makedirs(chk, exist_ok=True)
export_stl(shell, os.path.join(chk, "shell_design.stl"))
export_stl(plate, os.path.join(chk, "plate_design.stl"))
for nm, ob in ghosts.items():
    export_stl(ob, os.path.join(chk, f"ref_{nm}.stl"))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "ECG_PPG_Cover.blend"))

summary = dict(
    mount_holes=MOUNT, pcb=PCB, cavity=[2 * CAV_HX, 2 * CAV_HYH], outer=[2 * OUT_HX, 2 * OUT_HYH], plate=[2 * PX, 2 * PY],
    cavity_y=[CAV_YB, CAV_YT], outer_y=[OUT_YB, OUT_YT], bay=BAY, battery=(BAT if BAY_ON else None), cradle=CRADLE,
    z=dict(plate_bottom=Z_PLATE0, split=Z_SPLIT, front_inner=Z_CAV_TOP, top=Z_TOP, pcb=[Z_PCB0, Z_PCB1], tft=[Z_TFT0, Z_TFT1], glass_front=Z_FRONT),
    micro=MICRO, jack=JACK, usbc=USBC, gland=GLAND, switch=SWITCH, screws=screw_pos, window=[WIN_W, WIN_H, WIN_CX, WIN_CY],
    belt=dict(slot_w=BELT_SLOT_W, slot_l=BELT_SLOT_L, slot_cx=SLOT_CX, wing=WING),
    screw=dict(len=SCREW_LEN, boss_top=BOSS_TOP, csk_depth=CSK_DEPTH, plate_t=PLATE_T), ch=CH, out_r=OUT_R, plate_r=PR,
    rakit=(dict(RAKIT, lugs=LUGS, grooves=GROOVES, pos=RAKIT_POS) if RAKIT_ON else None),
)
json.dump(summary, open(os.path.join(OUT, "_ref", "summary.json"), "w"), indent=1)
print("OK", OUT)
