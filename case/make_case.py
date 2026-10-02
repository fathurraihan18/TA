"""
Cover alat ECG + PPG (ESP32 + TFT ILI9488 3.5" + PCB custom)  -  generator Blender (bpy)

Jalankan:   python make_case.py <folder_output>
Satuan  :   1 unit Blender = 1 mm

SISTEM KOORDINAT MODEL (dilihat dari DEPAN / sisi layar):
    +X = arah KIRI   (kanan di foto 1)      -X = KANAN
    +Y = arah ATAS                          -Y = BAWAH
    +Z = arah DEPAN (layar)                  Z=0 = ujung ekor baut belakang (bidang paling belakang tumpukan)
Titik (0,0) = pusat pola 4 lubang baut M3 (dari Gerber).

Konversi Gerber -> model:  X = -(Xg - 56.007)   Y = -(Yg - 33.655)
(PCB di Gerber ternyata terpasang diputar 180 derajat terhadap tampilan atas Gerber;
 terbukti dari posisi konektor PPG, port USB-C, header TFT dan micro-USB ESP32 pada foto.)
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else (sys.argv[1] if len(sys.argv) > 1 else ".")
os.makedirs(OUT, exist_ok=True)

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
TAIL = 5.0                    # panjang ekor baut bawah
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
CAV_R, OUT_R = 0.5, 3.5
Z_SPLIT = -0.5                                      # lantai rongga / bidang belah shell-plate
FRONT_GAP = 0.3
Z_CAV_TOP = Z_FRONT + FRONT_GAP                     # 31.5
FRONT_T = 2.4
Z_TOP = Z_CAV_TOP + FRONT_T                         # 33.9
PLATE_T = 3.0
Z_PLATE0 = Z_SPLIT - PLATE_T                        # -3.5
OUT_HX, OUT_HY = CAV_HX + WALL, CAV_HY + WALL       # 52.5 x 31.75
HOLE_TOL = 0.2                                      # kompensasi cetak (lubang jadi lebih kecil di printer)

WIN_W, WIN_H, WIN_CX, WIN_CY, WIN_R = 79.0, 52.0, GLASS_CX, 0.0, 2.0

# ---- lubang tetap (posisi dari Gerber + ukuran Anda) -----------------------
MICRO = dict(x=mx(27.686), zc=17.0, w=12.0, h=8.0)            # BAWAH: dinding Y-  (bawah 13..21 mm dari belakang)
JACK = dict(x=mx(68.326), zc=15.0, d=7.0)                      # ATAS : dinding Y+  (kabel jack 5-6 mm)
USBC = dict(y=my(23.936), zc=9.65, w=10.4, h=4.6)             # KANAN: dinding X-  (port 8.0 .. 11.3 mm dari belakang)
GLAND = dict(y=my(45.85), zc=15.0, thread=18.6, hole=19.0, nut_af=24.6, nut_depth=6.0, plate=3.0, out=6.0)  # PG11
SWITCH = dict(x=-40.0, zc=18.5, cut_w=13.6, cut_h=9.1, ch_w=17.0, ch_h=12.0, out=9.6, panel=1.6)  # KCD11

# ---- baut penutup plate (M3 x 8 flat head, ke boss di dinding panjang) ------
SCREW_X = [23.0, -23.0]
BOSS_W, BOSS_IN, BOSS_TOP = 8.0, 6.0, 4.8
PILOT_D, CLEAR_D, CSK_D = 2.7, 3.4, 6.4

# ---- tiang penyangga PCB di back plate ------------------------------------
POST_OD, POST_ID = 10.0, 7.2

# ============================================================ HELPER BLENDER ==
scene = bpy.context.scene
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
shell = prism("Cover_Depan_Shell", rrect(0, 0, OUT_HX, OUT_HY, OUT_R), Z_SPLIT, Z_TOP)

# --- boss gland PG11 (sisi KANAN, -X) : blok tebal, mur segi-enam ditanam di dalam
g = GLAND
gy, gz = g["y"], g["zc"]
g_hy = g["nut_af"] / 2 + 2.3
g_hz = g["nut_af"] / math.sqrt(3) + 2.3
g_ztop = gz + g_hz
x_in, x_out = -CAV_HX, -(OUT_HX + g["out"])
slope_x = -(OUT_HX + g["out"] - (Z_TOP - g_ztop))                # kemiringan 45 derajat (tanpa support)
boss_g = prism("boss_gland",
               [(x_in, Z_SPLIT), (x_out, Z_SPLIT), (x_out, g_ztop), (slope_x, Z_TOP), (x_in, Z_TOP)],
               gy - g_hy, gy + g_hy, "Y")

# --- boss saklar (sisi ATAS, +Y) : ruang badan saklar + panel tipis untuk snap-in
s = SWITCH
sx0, sx1 = s["x"] - 11.0, s["x"] + 11.0
s_zlo, s_zhi = s["zc"] - 8.5, s["zc"] + 8.5
y_out = OUT_HY + s["out"]
boss_s = prism("boss_saklar",
               [(CAV_HY - 0.5, s_zlo), (y_out, s_zlo), (y_out, s_zhi), (y_out - (Z_TOP - s_zhi), Z_TOP), (CAV_HY - 0.5, Z_TOP)],
               sx0, sx1, "X")

# --- boss sekrup penutup (di bawah PCB, menempel di dinding Atas/Bawah)
screw_pos = []
boss_blocks = []
for sxp in SCREW_X:
    for side in (+1, -1):
        wall_in = side * CAV_HY
        y_a, y_b = sorted([wall_in + side * 0.3, wall_in - side * BOSS_IN])
        boss_blocks.append(box("boss_sekrup", sxp - BOSS_W / 2, sxp + BOSS_W / 2, y_a, y_b, Z_SPLIT, BOSS_TOP))
        screw_pos.append((sxp, wall_in - side * 3.5))

union_all(shell, [boss_g, boss_s] + boss_blocks)

# --- rongga utama + jendela layar
cav = prism("cav", rrect(0, 0, CAV_HX, CAV_HY, CAV_R), Z_SPLIT - 0.2, Z_CAV_TOP)
win = prism("win", rrect(WIN_CX, WIN_CY, WIN_W / 2, WIN_H / 2, WIN_R), Z_CAV_TOP - 0.5, Z_TOP + 0.5)
cut_all(shell, [cav, win])

# --- lubang sisi BAWAH (-Y): micro-USB ESP32
m = MICRO
cut_all(shell, [box("micro", m["x"] - (m["w"] + HOLE_TOL) / 2, m["x"] + (m["w"] + HOLE_TOL) / 2,
                    -OUT_HY - 0.5, -CAV_HY + 0.5, m["zc"] - (m["h"] + HOLE_TOL) / 2, m["zc"] + (m["h"] + HOLE_TOL) / 2)])

# --- lubang sisi ATAS (+Y): jack AD8232
j = JACK
cut_all(shell, [cyl("jack", j["x"], j["zc"], (j["d"] + HOLE_TOL) / 2, CAV_HY - 0.5, OUT_HY + 0.5, "Y")])

# --- panel + ruang saklar KCD11
chamber = box("ch", s["x"] - s["ch_w"] / 2, s["x"] + s["ch_w"] / 2, CAV_HY - 0.8, y_out - s["panel"],
              s["zc"] - s["ch_h"] / 2, s["zc"] + s["ch_h"] / 2)
panel = box("pn", s["x"] - (s["cut_w"] + 0.1) / 2, s["x"] + (s["cut_w"] + 0.1) / 2, y_out - s["panel"] - 0.1, y_out + 0.5,
            s["zc"] - (s["cut_h"] + 0.1) / 2, s["zc"] + (s["cut_h"] + 0.1) / 2)
cut_all(shell, [chamber, panel])

# --- lubang sisi KANAN (-X): USB-C powerbank
u = USBC
cut_all(shell, [box("usbc", -OUT_HX - 0.5, -CAV_HX + 0.5, u["y"] - (u["w"] + HOLE_TOL) / 2, u["y"] + (u["w"] + HOLE_TOL) / 2,
                    u["zc"] - (u["h"] + HOLE_TOL) / 2, u["zc"] + (u["h"] + HOLE_TOL) / 2)])

# --- gland PG11: kantong mur segi-enam (dari dalam) + lubang ulir
x_pocket_in = -CAV_HX + 0.1
x_pocket_bot = -(OUT_HX + g["out"] - g["plate"])
pocket = prism("pocket", hexagon(gy, gz, g["nut_af"], True), x_pocket_bot, x_pocket_in, "X")
ghole = cyl("ghole", gy, gz, g["hole"] / 2, x_out - 0.5, x_pocket_bot + 0.1, "X")
cut_all(shell, [pocket, ghole])

# --- lubang pilot sekrup penutup
pilots = [cyl("pilot", px, py, PILOT_D / 2, Z_SPLIT - 0.2, BOSS_TOP - 0.5, "Z", n=32) for px, py in screw_pos]
cut_all(shell, pilots)

# ============================================================ BACK PLATE =====
plate = prism("Cover_Belakang_BackPlate", rrect(0, 0, OUT_HX, OUT_HY, OUT_R), Z_PLATE0, Z_SPLIT)

# rim penengah (masuk rongga, celah 0.2 mm), dipotong di sekitar boss sekrup
rim_o = prism("rim_o", rrect(0, 0, CAV_HX - 0.2, CAV_HY - 0.2, 0.3), Z_SPLIT - 0.01, Z_SPLIT + 2.0)
rim_i = prism("rim_i", rrect(0, 0, CAV_HX - 1.4, CAV_HY - 1.4, 0.3), Z_SPLIT - 0.1, Z_SPLIT + 2.1)
bop(rim_o, rim_i, "DIFFERENCE")
for sxp in SCREW_X:
    for side in (+1, -1):
        wall_in = side * CAV_HY
        y_a, y_b = sorted([wall_in + side * 1.0, wall_in - side * (BOSS_IN + 0.5)])
        bop(rim_o, box("rimcut", sxp - BOSS_W / 2 - 0.5, sxp + BOSS_W / 2 + 0.5, y_a, y_b, Z_SPLIT - 0.2, Z_SPLIT + 2.3))
for sx in (+1, -1):                    # rim dibuang di 4 sudut (area tiang) agar tidak ada sliver tipis
    for sy in (+1, -1):
        xa, xb = sorted([sx * (CAV_HX - 8.0), sx * (CAV_HX + 1.0)])
        ya, yb = sorted([sy * (CAV_HY - 8.0), sy * (CAV_HY + 1.0)])
        bop(rim_o, box("rimcorner", xa, xb, ya, yb, Z_SPLIT - 0.2, Z_SPLIT + 2.3))
union_all(plate, [rim_o])

# tiang penyangga PCB (cincin berongga untuk ekor baut + mur), dipangkas oleh dinding rongga
for k, (px, py) in enumerate(MOUNT):
    post = cyl(f"post{k}", px, py, POST_OD / 2, Z_SPLIT - 0.01, Z_PCB0, "Z", n=64)
    # dipangkas 0.6 mm dari dinding supaya rongga mur tembus ke sisi luar (tanpa sliver tipis)
    clip = prism(f"clip{k}", rrect(0, 0, CAV_HX - 0.6, CAV_HY - 0.6, 0.3), Z_SPLIT - 0.3, Z_PCB0 + 0.5)
    bop(post, clip, "INTERSECT")
    # buang ujung runcing di kuadran luar (dekat sudut dinding) supaya tidak ada sliver tipis
    sx, sy = (1 if px > 0 else -1), (1 if py > 0 else -1)
    xa, xb = sorted([px + sx * 1.5, px + sx * 9.0])
    ya, yb = sorted([py + sy * 1.5, py + sy * 9.0])
    bop(post, box(f"tip{k}", xa, xb, ya, yb, Z_SPLIT - 0.5, Z_PCB0 + 0.5), "DIFFERENCE")
    bop(plate, post, "UNION")
for k, (px, py) in enumerate(MOUNT):   # rongga ekor baut + mur juga memotong rim penengah
    bop(plate, cyl(f"hollow{k}", px, py, POST_ID / 2, Z_SPLIT, Z_PCB0 + 0.2, "Z", n=64))

# lubang sekrup + countersink (M3 flat head)
for px, py in screw_pos:
    bop(plate, cyl("thru", px, py, CLEAR_D / 2, Z_PLATE0 - 0.2, Z_SPLIT + 0.2, "Z", n=32))
    bop(plate, frustum("csk", px, py, CSK_D / 2 + 0.1, CLEAR_D / 2, Z_PLATE0 - 0.1, Z_PLATE0 + 1.6))

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


# PCB hijau, PCB merah, kaca
ghost("PCB_hijau", box("g", PCB["x0"], PCB["x1"], PCB["y0"], PCB["y1"], Z_PCB0, Z_PCB1, COL_GHOST), (0.05, 0.45, 0.15, 1))
ghost("TFT_PCB", box("g", -TFT_W / 2, TFT_W / 2, -TFT_H / 2, TFT_H / 2, Z_TFT0, Z_TFT1, COL_GHOST), (0.7, 0.05, 0.05, 1))
ghost("Kaca_touch", box("g", GLASS_CX - GLASS_W / 2, GLASS_CX + GLASS_W / 2, -GLASS_H / 2, GLASS_H / 2, Z_TFT1, Z_FRONT, COL_GHOST),
      (0.05, 0.05, 0.08, 1))
ghost("Area_aktif", box("g", GLASS_CX - AA_W / 2, GLASS_CX + AA_W / 2, -AA_H / 2, AA_H / 2, Z_FRONT - 0.05, Z_FRONT, COL_GHOST),
      (0.2, 0.5, 0.9, 1))
sp = box("g", 0, 0.1, 0, 0.1, 0, 0.1, COL_GHOST)
sp_parts = []
for k, (px, py) in enumerate(MOUNT):
    sp_parts.append(cyl(f"sp{k}", px, py, 2.75, Z_PCB1, Z_TFT0, "Z", n=32, coll=COL_GHOST))
    sp_parts.append(cyl(f"tail{k}", px, py, 3.2, 0.0, Z_PCB0, "Z", n=32, coll=COL_GHOST))
    sp_parts.append(cyl(f"head{k}", px, py, 3.0, Z_TFT1, Z_FRONT, "Z", n=32, coll=COL_GHOST))
bpy.data.objects.remove(sp, do_unlink=True)
base = sp_parts[0]
for p_ in sp_parts[1:]:
    bop(base, p_, "UNION")
ghost("Baut_spacer", base, (0.8, 0.65, 0.2, 1))
# konektor
ghost("microUSB_ESP32", box("g", m["x"] - 3.9, m["x"] + 3.9, my(63.9), my(57.8), 16.5, 19.1, COL_GHOST), (0.7, 0.7, 0.75, 1))
ghost("USBC_powerbank", box("g", mx(106.1), mx(98.8), my(28.2), my(19.3), 8.0, 11.3, COL_GHOST), (0.7, 0.7, 0.75, 1))
jk = cyl("g", j["x"], j["zc"], 3.0, my(3.977) - 8, my(3.977), "Y", coll=COL_GHOST)
bop(jk, cyl("g2", j["x"], j["zc"], 3.25, my(3.977), my(3.977) + 12, "Y", coll=COL_GHOST), "UNION")
ghost("Plug_jack_AD8232", jk, (0.1, 0.1, 0.1, 1))
sw = box("g", s["x"] - 6.7, s["x"] + 6.7, y_out - s["panel"] - 12.0, y_out - s["panel"], s["zc"] - 4.4, s["zc"] + 4.4, COL_GHOST)
ghost("Badan_saklar", sw, (0.1, 0.1, 0.1, 1))
gl = cyl("g", gy, gz, 9.3, x_out - 0.0, x_pocket_bot + 0.0, "X", coll=COL_GHOST)
nut = prism("g", hexagon(gy, gz, 24.0, True), x_pocket_bot, x_pocket_bot + 5.5, "X", COL_GHOST)
bop(gl, nut, "UNION")
ghost("Gland_PG11_+_mur", gl, (0.2, 0.2, 0.6, 1))

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
# referensi (untuk verifikasi) dalam orientasi rancangan
chk = os.path.join(OUT, "_ref")
os.makedirs(chk, exist_ok=True)
export_stl(shell, os.path.join(chk, "shell_design.stl"))
export_stl(plate, os.path.join(chk, "plate_design.stl"))
for nm, ob in ghosts.items():
    export_stl(ob, os.path.join(chk, f"ref_{nm}.stl"))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "ECG_PPG_Cover.blend"))

summary = dict(
    mount_holes=MOUNT, pcb=PCB, cavity=[2 * CAV_HX, 2 * CAV_HY], outer=[2 * OUT_HX, 2 * OUT_HY],
    z=dict(plate_bottom=Z_PLATE0, split=Z_SPLIT, front_inner=Z_CAV_TOP, top=Z_TOP, pcb=[Z_PCB0, Z_PCB1], tft=[Z_TFT0, Z_TFT1], glass_front=Z_FRONT),
    micro=MICRO, jack=JACK, usbc=USBC, gland=GLAND, switch=SWITCH, screws=screw_pos, window=[WIN_W, WIN_H, WIN_CX, WIN_CY],
)
json.dump(summary, open(os.path.join(OUT, "_ref", "summary.json"), "w"), indent=1)
print("OK", OUT)
