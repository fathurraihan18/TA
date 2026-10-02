"""
Klip jari sensor PPG MAX30102 (modul HW-605)  -  generator Blender (bpy)    [v2: desain ulang]

Jalankan:   python make_clip.py -- <folder_output>
Satuan   :  mm.   Sumbu: +X = ke belakang (arah engsel/kabel), X=0 = mulut klip (tempat jari masuk),
            Y = melintang (lebar klip), Z = tegak; Z=0 = bidang tengah antara rahang (sumbu engsel).
            Semua bentuk dibuat pada POSISI NOMINAL: jari terpasang, permukaan bantalan kedua rahang sejajar.

Bagian cetak:  A = rahang bawah (sensor + jalur kabel), B = rahang atas (engsel + dudukan pegas),
               C = tutup bawah (sliding/press-fit, menutup modul dan kabel), D = ring shim 1 mm (x4).
Perangkat keras: 1 sekrup engsel, 1 pegas tekan, kabel 4 inti, busa tipis (opsional).

Perbaikan terhadap klip lama (foto pengguna):
  1. Kabel TIDAK bisa lepas: terowongan tertutup, leher sempit, jalur berkelok (S), rib penjepit di tutup.
  2. Modul tetap bisa disolder: modul dipasang dari BAWAH setelah disolder; kabel dan kawat tidak terjepit rahang.
  3. Penjepit lebih kuat dan bisa diatur: pegas punya dudukan (pin + kantong), 2 posisi dudukan + ring shim.
  4. Nyaman: permukaan jari berlekuk (radius 15,6), mulut membulat, sensor rata tanpa PCB terbuka, bantalan busa.
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_helpers import *          # noqa
from bl_helpers import _select_only, _obj

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(OUT, exist_ok=True)

# =============================================================== PARAMETER ==
# ---- komponen (UKUR dengan jangka sorong lalu ubah di sini) ------------------
BOARD = dict(w=18.0, l=13.5, t=1.6, sens_l=5.6, sens_w=3.3, sens_h=1.55, tol=0.2)   # HW-605 (w = sisi melintang jari)
SPRING = dict(od=4.2, wire=0.45, L0=12.0, n_active=6.0)        # pegas tekan (perkiraan dari foto)
SCREW = dict(d=3.0, head_d=5.6, head_h=1.8, length=14.0)       # sekrup engsel
CABLE_D = 4.0                                                   # kabel 4 inti AWG (diameter luar)
FINGER = dict(w=17.0, h=14.0)                                   # telunjuk dewasa (lebar x tebal ujung jari)

# ---- bentuk -----------------------------------------------------------------
W = 26.0                      # lebar klip
HW = W / 2
XL = 67.0                     # panjang total
R_PLAN = 3.5                  # radius sudut (tampak atas)
CH = 1.4                      # chamfer sisi luar (nyaman dan bisa dicetak tanpa support)
XP = 46.0                     # sumbu engsel
G0 = 15.0                     # jarak nominal bantalan (jari 14 mm + busa 1 mm)
ZP = G0 / 2                   # 7,5 : permukaan bantalan (titik terdalam lekuk) di +-ZP
R_C, CW = 15.6, 9.2           # lekuk jari: radius dan setengah lebar (kedalaman 3,0 mm)
XS = 22.0                     # pusat sensor dari mulut
SENS_REC = 0.8                # sensor masuk 0,8 mm dari permukaan bantalan (ruang untuk solder dan kawat di atas PCB)
LID_T = 2.0
Z_L = -ZP - SENS_REC - (BOARD["t"] + BOARD["sens_h"])      # permukaan atas tutup = alas PCB = -11,05
Z_O = Z_L - LID_T                                          # muka luar bawah rahang A = -13,05
Z_T = 11.5                                                 # muka luar atas rahang B
X_STOP0, X_STOP1 = 35.0, 37.5                              # dinding penahan ujung jari
Z_RIM_A = -2.0
BLK_A, BLK_B = -3.0, 3.0                                   # puncak balok ekor A / dasar balok ekor B (celah 6,0)
X_BLK = XP + 7.5                                           # awal balok ekor
LUG_Y0, LUG_T, TAB_HALF, LUG_R = 3.3, 2.4, 3.0, 6.0        # engsel: lug 2 sisi (2,4 mm), tab tengah 6 mm
HINGE_HOLE = SCREW["d"] + 0.2
SEAT_LS = (9.0, 14.0)                                      # dudukan pegas: jarak dari sumbu engsel
XB_SEATS = [XP + ls for ls in SEAT_LS]
SPR_ID = SPRING["od"] - 2 * SPRING["wire"]
PIN_D = SPR_ID - 0.5
POCKET_D = SPRING["od"] + 0.8
PIN_H = 2.5
FORCE_TARGET = (2.0, 3.5)                                  # gaya jepit pada jari (N) yang dituju untuk dudukan 1 dan 2 (pegas perkiraan)
LF = XP - XS                                               # lengan gaya: engsel -> pusat sensor
CAB_H = CABLE_D + 1.0                                      # tinggi terowongan kabel
CAB_W = CABLE_D + 1.2                                      # lebar terowongan kabel
WIRE_W = CAB_W + 0.2                                       # lebar jalur kawat (sedikit lebih lebar dari terowongan kabel)
Z_C1 = Z_L + BOARD["t"] + BOARD["sens_h"] + SENS_REC       # langit-langit zona solder = -7,5
Z_C2 = Z_L + CAB_H                                         # langit-langit terowongan kabel
Z_AX = Z_L + CAB_H / 2                                     # sumbu kabel
CLAMP_RIB = 1.3                                            # rib penjepit di tutup (menyisakan 0,3 mm tekan pada kabel 4,0)
ROUTE = [(28.0, 0.0), (33.0, 0.0), (37.0, -8.4), (52.0, -8.4), (59.0, 0.0), (64.3, 0.0)]   # jalur kawat -> kabel (tampak atas)
LID_X0, LID_X1 = 13.0, 64.3
LID_HY = 10.6

def spring_k(sp=SPRING, G=79000.0):
    """kekakuan pegas tekan baja (N/mm): G d^4 / (8 D^3 N)."""
    D = sp["od"] - sp["wire"]
    return G * sp["wire"] ** 4 / (8 * D ** 3 * sp["n_active"])


K_EST = spring_k()


def pocket_depth(ls, F, L0=SPRING["L0"], k=K_EST):
    """kedalaman kantong pada B supaya gaya jepit pada jari (posisi nominal) = F:  F = k (L0 - s) Ls / Lf."""
    s_nom = L0 - F * LF / (k * ls)                         # jarak antar dudukan pada posisi nominal
    return max(0.8, s_nom - (BLK_B - BLK_A))


POCKET_DEPTH = [pocket_depth(ls, F) for ls, F in zip(SEAT_LS, FORCE_TARGET)]


def z_pad(x):
    """titik terdalam lekuk bantalan A sepanjang X (bahu naik di belakang jendela sensor)."""
    x0, x1, dz = 25.6, 28.4, 2.2
    if x <= x0: return -ZP
    if x >= x1: return -ZP + dz
    t = (x - x0) / (x1 - x0)
    return -ZP + dz * (3 * t * t - 2 * t ** 3)


def arc(y, R=R_C):
    return R - math.sqrt(R * R - y * y)


def stadium(p, q, w, n=14):
    """poligon bidang XY: pil dengan lebar w dari p ke q."""
    r = w / 2
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    pts = []
    for k in range(n + 1):
        a = ang - math.pi / 2 + math.pi * k / n
        pts.append((q[0] + r * math.cos(a), q[1] + r * math.sin(a)))
    for k in range(n + 1):
        a = ang + math.pi / 2 + math.pi * k / n
        pts.append((p[0] + r * math.cos(a), p[1] + r * math.sin(a)))
    return pts


def outline_mask(name, chamfer_side):
    """topeng bentuk luar: persegi membulat + chamfer 45 derajat di sisi luar (chamfer_side = 'bawah'/'atas')."""
    cx, hx = XL / 2, XL / 2
    big = lambda inset: rrect(cx, 0, hx - inset, HW - inset, max(R_PLAN - inset, 0.4), 12)
    if chamfer_side == "bawah":
        rings = [(big(CH), Z_O), (big(0), Z_O + CH), (big(0), 30.0)]
    else:
        rings = [(big(0), -30.0), (big(0), Z_T - CH), (big(CH), Z_T)]
    return loft(name, rings)


def teardrop(cx, cz, r, n=36):
    """lingkaran dengan puncak runcing 45 derajat di atas (lubang horizontal tanpa overhang)."""
    pts = [(cx, cz + r * math.sqrt(2.0))]
    for k in range(n + 1):
        a = math.radians(45.0 - 270.0 * k / n)
        pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def xz_prism(name, pts, y0, y1):
    return prism(name, pts, y0, y1, "Y")


def lug_profile(upper=True):
    pts = [(XP - LUG_R, -ZP - 1.0 if upper else ZP + 1.0), (XP + LUG_R, -ZP - 1.0 if upper else ZP + 1.0), (XP + LUG_R, 0.0)]
    n = 24
    for k in range(1, n):
        a = math.pi * k / n
        pts.append((XP + LUG_R * math.cos(a), (LUG_R * math.sin(a)) if upper else -(LUG_R * math.sin(a))))
    pts.append((XP - LUG_R, 0.0))
    return pts


# ============================================================ RAHANG A (BAWAH) ==
parts = {}

A = box("A", 0, XL, -HW, HW, Z_O - 0.5, -ZP)                                  # pelat dasar
union_all(A, [box("A_front", 0, X_STOP1, -HW, HW, -ZP - 0.5, Z_RIM_A)])        # blok depan (bibir + dinding penahan)
for sgn in (+1, -1):
    ya, yb = sorted([sgn * 4.6, sgn * HW])
    union_all(A, [box("A_side", X_STOP1 - 0.5, X_BLK + 0.2, ya, yb, -ZP - 0.5, BLK_A)])   # blok samping (atap terowongan kabel)
union_all(A, [box("A_tail", X_BLK, XL, -HW, HW, -ZP - 0.5, BLK_A)])             # balok ekor (dudukan pegas + terowongan)
for sgn in (+1, -1):                                                           # lug engsel
    ya, yb = sorted([sgn * LUG_Y0, sgn * (LUG_Y0 + LUG_T)])
    union_all(A, [xz_prism("A_lug", lug_profile(True), ya, yb)])
for ls in SEAT_LS:                                                             # pin dudukan pegas
    union_all(A, [cyl("A_pin", XP + ls, 0.0, PIN_D / 2, BLK_A - 0.3, BLK_A + PIN_H, "Z", n=32)])

# --- lekuk jari (bantalan) mengikuti bahu: loft potongan tegak lurus X
xs_c = [-1.0, 2.0, 12.0, 24.0, 25.6, 26.0, 26.4, 26.8, 27.2, 27.6, 28.0, 28.4, 30.0, 33.0, X_STOP0]
rings = []
ys = [-CW + 2 * CW * i / 16 for i in range(17)]
for x in xs_c:
    zc = z_pad(max(x, 0.0))
    ring = [(y, zc + arc(y)) for y in ys] + [(CW, 6.0), (-CW, 6.0)]
    rings.append((x, ring))
cut_all(A, [loft_x("A_lekuk", rings)])
# --- mulut membulat: potong sudut atas bibir
cut_all(A, [xz_prism("A_mulut", [(-1.0, Z_RIM_A + 0.2), (5.5, Z_RIM_A + 0.2), (-1.0, -ZP - 0.4)], -HW - 1, HW + 1)])

# --- rongga dari bawah (diurutkan: tutup, modul, zona solder, jalur kawat/kabel)
cut_all(A, [box("lid_rec", LID_X0, LID_X1, -LID_HY, LID_HY, Z_O - 1.0, Z_L)])
bx0, bx1 = XS - BOARD["l"] / 2 - BOARD["tol"], XS + BOARD["l"] / 2 + BOARD["tol"]
by = BOARD["w"] / 2 + BOARD["tol"]
BOARD_LIFT = 0.6              # ruang untuk lapisan double-tape foam di bawah modul (mengangkat sensor mendekati permukaan bantalan)
cut_all(A, [box("board_pocket", bx0, bx1, -by, by, Z_L - 0.05, Z_L + BOARD["t"] + 0.2 + BOARD_LIFT)])
cut_all(A, [cyl("pry", LID_X0, 0.0, 3.2, Z_O - 1.0, Z_O + 1.4, "Z", n=40)])        # takik untuk mencungkil tutup
win_l = BOARD["sens_l"] + 1.2
win_w = BOARD["sens_w"] + 1.6
cut_all(A, [box("jendela", XS - win_l / 2, XS + win_l / 2, -win_w / 2, win_w / 2, Z_L + BOARD["t"] - 0.1, 0.0)])
cut_all(A, [box("zona_solder", 26.4, 31.5, -5.2, 5.2, Z_L - 0.05, Z_C1)])      # 4 pad solder (pitch 2,54) + kawat
# jalur: zona kawat (R0..R2) lalu terowongan kabel (R2..R5)
cut_all(A, [prism("rute_kawat", stadium(ROUTE[0], ROUTE[1], WIRE_W), Z_L - 0.05, Z_C1)])
for (p, q) in zip(ROUTE[1:-2], ROUTE[2:-1]):
    cut_all(A, [prism("rute_kabel", stadium(p, q, CAB_W), Z_L - 0.05, Z_C2)])
cut_all(A, [box("rute_ujung", ROUTE[-2][0], LID_X1, -CAB_W / 2, CAB_W / 2, Z_L - 0.05, Z_C2)])          # lurus ke leher (tanpa tutup bulat)
# leher keluar kabel (sumbu X) menembus dinding ujung
cut_all(A, [prism("leher", teardrop(0.0, Z_AX, (CABLE_D + 0.3) / 2), LID_X1 - 0.3, XL + 1.0, "X")])
# --- lubang engsel (lug +Y bebas, lug -Y sedikit lebih kecil untuk sekrup mengulir sendiri)
cut_all(A, [xz_prism("engsel_a", teardrop(XP, 0.0, HINGE_HOLE / 2), 0.0, HW + 1), xz_prism("engsel_b", teardrop(XP, 0.0, (SCREW["d"] - 0.4) / 2), -HW - 1, 0.0)])
# --- topeng bentuk luar
bop(A, outline_mask("mask_A", "bawah"), "INTERSECT")
A.name = "A_RahangBawah"
parts["A"] = A

# ============================================================ RAHANG B (ATAS) ==
B = box("B", 0, X_BLK + 0.2, -HW, HW, ZP, Z_T)
union_all(B, [box("B_front", 0, X_STOP1, -HW, HW, 2.5, ZP + 0.5)])
union_all(B, [box("B_tail", X_BLK, XL, -HW, HW, BLK_B, Z_T)])
union_all(B, [xz_prism("B_tab", lug_profile(False), -TAB_HALF, TAB_HALF)])
rings = []
for x in (-1.0, 12.0, X_STOP0):
    ring = [(y, ZP + arc(y)) for y in ys] + [(CW, 1.0), (-CW, 1.0)]
    rings.append((x, ring))
cut_all(B, [loft_x("B_lekuk", rings)])
cut_all(B, [xz_prism("B_mulut", [(-1.0, 2.3), (5.5, 2.3), (-1.0, ZP + 0.1)], -HW - 1, HW + 1)])
for xsd, dep in zip(XB_SEATS, POCKET_DEPTH):
    cut_all(B, [cyl("B_kantong", xsd, 0.0, POCKET_D / 2, BLK_B - 0.2, BLK_B + dep, "Z", n=40)])
cut_all(B, [xz_prism("engsel_tab", teardrop(XP, 0.0, HINGE_HOLE / 2), -HW - 1, HW + 1)])
bop(B, outline_mask("mask_B", "atas"), "INTERSECT")
B.name = "B_RahangAtas"
parts["B"] = B

# ============================================================ TUTUP C =========
C = box("C", LID_X0 + 0.1, LID_X1 - 0.1, -LID_HY + 0.1, LID_HY - 0.1, Z_O, Z_L)
for xr in (60.6, 62.8):                                      # rib penjepit kabel (menekan jaket 0,3 mm)
    union_all(C, [box("C_rib", xr, xr + 1.0, -CAB_W / 2 + 0.2, CAB_W / 2 - 0.2, Z_L - 0.01, Z_L + CLAMP_RIB)])
cut_all(C, [cyl("C_takik", LID_X0 + 0.1, Z_O + 1.0, 4.0, -3.0, 3.0, "Y", n=40) if False else cyl("C_takik", LID_X0 + 0.1, 0.0, 4.0, Z_O - 1.0, Z_O + 0.9, "Z", n=40)])
for xr in (20.0, 34.0, 48.0, 58.0):                         # rusuk gesek di sisi tutup (menahan tutup, interferensi 0,15 mm)
    for sgn in (+1, -1):
        ya, yb = sorted([sgn * (LID_HY - 0.1), sgn * (LID_HY - 0.1 + 0.25)])
        union_all(C, [box("C_gesek", xr, xr + 6.0, ya, yb, Z_O + 0.5, Z_L - 0.4)])
C.name = "C_TutupBawah"
parts["C"] = C

# ============================================================ RING SHIM D ======
D = cyl("D", 0.0, 0.0, 2.8, 0.0, 1.0, "Z", n=40)
cut_all(D, [cyl("D_lubang", 0.0, 0.0, (PIN_D + 0.3) / 2, -0.1, 1.1, "Z", n=32)])
D.name = "D_ShimPegas"
parts["D"] = D

# ============================================================ REFERENSI (ghost) ==
ghosts = {}


def ghost(name, ob, color):
    ob.name = "Ref_" + name
    ghosts[name] = ob
    mat = bpy.data.materials.new("m_" + name)
    mat.diffuse_color = color
    ob.data.materials.append(mat)
    ob.display_type = "WIRE"
    if ob.name in COL_MAIN.objects:
        COL_MAIN.objects.unlink(ob)
    if ob.name not in COL_GHOST.objects:
        COL_GHOST.objects.link(ob)
    return ob


def seg3(name, p0, p1, r, n=24):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    bm = bmesh.new()
    lo = [bm.verts.new((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), 0)) for k in range(n)]
    hi = [bm.verts.new((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), L)) for k in range(n)]
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); COL_GHOST.objects.link(ob)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    ob.location = p0
    bpy.context.view_layer.update()
    me2 = me.copy(); me2.transform(ob.matrix_world)
    bpy.data.objects.remove(ob, do_unlink=True)
    ob2 = bpy.data.objects.new(name, me2); COL_GHOST.objects.link(ob2)
    return ob2


# modul HW-605: PCB + sensor + 4 solder
board = box("g", XS - BOARD["l"] / 2, XS + BOARD["l"] / 2, -BOARD["w"] / 2, BOARD["w"] / 2, Z_L, Z_L + BOARD["t"], COL_GHOST)
union_all(board, [box("g2", XS - BOARD["sens_l"] / 2, XS + BOARD["sens_l"] / 2, -BOARD["sens_w"] / 2, BOARD["sens_w"] / 2, Z_L + BOARD["t"], Z_L + BOARD["t"] + BOARD["sens_h"])])
pad_x = XS + BOARD["l"] / 2 - 1.5
for yy in (-3.81, -1.27, 1.27, 3.81):
    union_all(board, [box("g3", pad_x - 0.9, pad_x + 0.9, yy - 0.9, yy + 0.9, Z_L + BOARD["t"], Z_L + BOARD["t"] + 1.5)])
ghost("Modul_HW605", board, (0.1, 0.1, 0.12, 1))
# kabel (jaket) sepanjang jalur dari ujung jaket sampai keluar leher
pts3 = [(52.0, -8.4, Z_AX), (59.0, 0.0, Z_AX), (XL + 12.0, 0.0, Z_AX)]
cab = seg3("g", pts3[0], pts3[1], CABLE_D / 2)
union_all(cab, [seg3("g", pts3[1], pts3[2], CABLE_D / 2)])
ghost("Kabel_4_inti", cab, (0.8, 0.1, 0.1, 1))
# bundel kawat 4 inti (diameter bundel 3,2) dari pad ke ujung jaket
wr = [(pad_x, 0.0, Z_L + BOARD["t"] + 0.9), (33.0, 0.0, Z_L + BOARD["t"] + 0.9), (37.0, -8.4, Z_L + BOARD["t"] + 0.9), (52.0, -8.4, Z_AX)]
wire = seg3("g", wr[0], wr[1], 1.4)
for a_, b_ in zip(wr[1:-1], wr[2:]):
    union_all(wire, [seg3("g", a_, b_, 1.4)])
ghost("Kawat_bundel", wire, (0.9, 0.7, 0.1, 1))
# pegas (silinder OD; kondisi nominal) pada dudukan 1
sp = cyl("g", XB_SEATS[0], 0.0, SPRING["od"] / 2, BLK_A, BLK_B + POCKET_DEPTH[0], "Z", n=32, coll=COL_GHOST)
ghost("Pegas", sp, (0.6, 0.6, 0.65, 1))
# sekrup engsel
y_head0 = LUG_Y0 + LUG_T
scr = cyl("g", XP, 0.0, SCREW["d"] / 2, y_head0 - (SCREW["length"] - SCREW["head_h"]), y_head0, "Y", n=24, coll=COL_GHOST)
union_all(scr, [cyl("g2", XP, 0.0, SCREW["head_d"] / 2, y_head0, y_head0 + SCREW["head_h"], "Y", n=32, coll=COL_GHOST)])
ghost("Sekrup_engsel", scr, (0.1, 0.1, 0.1, 1))
# jari (elips) pada posisi nominal, ujung membulat di X_STOP0 - 1
fx1 = X_STOP0 - 1.0
rings = []
for x in (-5.0, 5.0, 25.0, fx1 - 4.0, fx1 - 2.0, fx1 - 0.8):
    f = 1.0 if x <= fx1 - 4.0 else math.sqrt(max(0.0, 1 - ((x - (fx1 - 4.0)) / 4.0) ** 2))
    f = max(f, 0.15)
    ring = [(f * FINGER["w"] / 2 * math.cos(2 * math.pi * k / 40), f * FINGER["h"] / 2 * math.sin(2 * math.pi * k / 40)) for k in range(40)]
    rings.append((x, ring))
finger = loft_x("g", rings, COL_GHOST)
ghost("Jari_telunjuk", finger, (0.9, 0.6, 0.5, 1))

# ============================================================ WARNA + EKSPOR ==
cols = {"A": (0.92, 0.92, 0.95, 1), "B": (0.85, 0.88, 0.95, 1), "C": (0.55, 0.65, 0.8, 1), "D": (0.9, 0.5, 0.2, 1)}
for k, ob in parts.items():
    mat = bpy.data.materials.new("m_" + ob.name)
    mat.diffuse_color = cols[k]
    ob.data.materials.append(mat)
    for poly in ob.data.polygons:
        poly.use_smooth = False


def export_stl(ob, path, matrix=None):
    tmp = ob.copy(); tmp.data = ob.data.copy()
    bpy.context.scene.collection.objects.link(tmp)
    if matrix is not None:
        tmp.data.transform(matrix)
    _select_only(tmp)
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, global_scale=1.0, apply_modifiers=True)
    bpy.data.objects.remove(tmp, do_unlink=True)


chk = os.path.join(OUT, "_ref"); os.makedirs(chk, exist_ok=True)
for k, ob in parts.items():
    export_stl(ob, os.path.join(chk, f"{k}_desain.stl"))
for nm, ob in ghosts.items():
    export_stl(ob, os.path.join(chk, f"ref_{nm}.stl"))
# orientasi cetak: A = muka luar bawah di meja; B = muka luar atas di meja (diputar 180 derajat sekitar Y); C = rata; D = rata
export_stl(parts["A"], os.path.join(OUT, "A_RahangBawah_siap_cetak.stl"), Matrix.Translation((0, 0, -(Z_O))))
export_stl(parts["B"], os.path.join(OUT, "B_RahangAtas_siap_cetak.stl"), Matrix.Translation((0, 0, Z_T)) @ Matrix.Rotation(math.pi, 4, "Y"))
export_stl(parts["C"], os.path.join(OUT, "C_TutupBawah_siap_cetak.stl"), Matrix.Translation((0, 0, -(Z_O))))
export_stl(parts["D"], os.path.join(OUT, "D_ShimPegas_siap_cetak.stl"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Klip_PPG.blend"))

summary = dict(
    board=BOARD, spring=SPRING, screw=SCREW, cable_d=CABLE_D, finger=FINGER,
    W=W, XL=XL, XP=XP, G0=G0, ZP=ZP, XS=XS, Z_L=Z_L, Z_O=Z_O, Z_T=Z_T, LID_T=LID_T, X_STOP=[X_STOP0, X_STOP1],
    BLK=[BLK_A, BLK_B], X_BLK=X_BLK, seats_ls=list(SEAT_LS), seats_x=XB_SEATS, pocket_depth=POCKET_DEPTH, pocket_d=POCKET_D, pin_d=PIN_D, pin_h=PIN_H,
    k_est=K_EST, force_target=list(FORCE_TARGET), lf=LF, route=ROUTE, cab_w=CAB_W, cab_h=CAB_H, z_ax=Z_AX, z_c1=Z_C1, z_c2=Z_C2, hinge_hole=HINGE_HOLE, lug_y0=LUG_Y0, lug_t=LUG_T, tab_half=TAB_HALF, lug_r=LUG_R,
    lid=dict(x0=LID_X0 + 0.1, x1=LID_X1 - 0.1, hy=LID_HY - 0.1, t=LID_T, rib_h=CLAMP_RIB), cradle=dict(R=R_C, hw=CW), pad_ramp=[25.6, 29.6, 2.6],
)
json.dump(summary, open(os.path.join(chk, "summary.json"), "w"), indent=1)
print("OK", OUT)
