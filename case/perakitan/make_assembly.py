"""
Model PERAKITAN berwarna (cover + semua komponen) -> render rakitan, render eksplode, data jangkar balon.
Jalankan:  python make_assembly.py -- <folder_case> <folder_output> <mode...>
mode: assembled | back | exploded | layout | all
Koordinat sama dengan make_case.py: +X=Kiri, +Y=Atas, +Z=Depan, Z=0 = ujung ekor baut.
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

A = sys.argv[sys.argv.index("--") + 1:]
CASE, OUT = A[0], A[1]
MODES = A[2:] or ["all"]
os.makedirs(OUT, exist_ok=True)
S = json.load(open(os.path.join(CASE, "_ref", "summary.json")))
RES = int(os.environ.get("RES", "1400"))

bpy.ops.wm.open_mainfile(filepath=os.path.join(CASE, "ECG_PPG_Cover.blend"))
sc = bpy.context.scene
for ob in list(bpy.data.objects):
    if ob.name.startswith("Ref_"):
        bpy.data.objects.remove(ob, do_unlink=True)
shell = bpy.data.objects["Cover_Depan_Shell"]
plate = bpy.data.objects["Cover_Belakang_BackPlate"]
COL = bpy.data.collections["Rumah"]


# ------------------------------------------------------------------ helper geometri
def _select_only(ob):
    for o in list(bpy.context.scene.objects):
        if o is not None: o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)


def _obj(name, bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); COL.objects.link(ob)
    return ob


def _map(axis, p, q, a):
    return {"Z": (p, q, a), "Y": (p, a, q), "X": (a, p, q)}[axis]


def prism(name, pts, a0, a1, axis="Z"):
    bm = bmesh.new()
    lo = [bm.verts.new(_map(axis, p, q, a0)) for p, q in pts]
    hi = [bm.verts.new(_map(axis, p, q, a1)) for p, q in pts]
    n = len(pts)
    bm.faces.new(lo); bm.faces.new(hi[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return _obj(name, bm)


def rrect(cx, cy, hx, hy, r, n=8):
    r = min(r, hx, hy)
    if r <= 1e-6:
        return [(cx + hx, cy + hy), (cx - hx, cy + hy), (cx - hx, cy - hy), (cx + hx, cy - hy)]
    pts = []
    for (sx, sy, a0) in [(1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)]:
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((cx + sx * (hx - r) + r * math.cos(a), cy + sy * (hy - r) + r * math.sin(a)))
    return pts


def circle(cx, cy, r, n=40):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def hexagon(cx, cy, af, corners_on_q=True):
    R = af / math.sqrt(3); off = 90 if corners_on_q else 0
    return [(cx + R * math.cos(math.radians(off + 60 * k)), cy + R * math.sin(math.radians(off + 60 * k))) for k in range(6)]


def box(name, x0, x1, y0, y1, z0, z1):
    return prism(name, [(x1, y1), (x0, y1), (x0, y0), (x1, y0)], z0, z1, "Z")


def rbox(name, x0, x1, y0, y1, z0, z1, r=1.0):
    return prism(name, rrect((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, r), z0, z1, "Z")


def cyl(name, c1, c2, r, a0, a1, axis="Z", n=36):
    return prism(name, circle(c1, c2, r, n), a0, a1, axis)


def seg(name, p0, p1, r, n=16):
    """silinder dari titik p0 ke p1 (arah bebas)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    ob = cyl(name, 0, 0, r, 0, L, "Z", n)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    ob.matrix_world = Matrix.Translation(p0) @ q.to_matrix().to_4x4()
    me = ob.data; me.transform(ob.matrix_world); ob.matrix_world = Matrix.Identity(4)
    return ob


def quad_uv(name, x0, x1, y0, y1, z):
    bm = bmesh.new()
    v = [bm.verts.new((x0, y0, z)), bm.verts.new((x1, y0, z)), bm.verts.new((x1, y1, z)), bm.verts.new((x0, y1, z))]
    f = bm.faces.new(v)
    uv = bm.loops.layers.uv.new("UV")
    for lp, (u, w) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        lp[uv].uv = (u, w)
    return _obj(name, bm)


# ------------------------------------------------------------------ material
def mat(name, color, metallic=0.0, rough=0.5, emit_img=None, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if emit_img:
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(emit_img)
        em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.1
        nt.links.new(t.outputs["Color"], em.inputs["Color"])
        out = nt.nodes["Material Output"]
        nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


C = {
    "orange": mat("orange", (0.80, 0.34, 0.06), 0.0, 0.32),
    "black": mat("black", (0.025, 0.025, 0.03), 0.0, 0.35),
    "plate": mat("plate", (0.05, 0.05, 0.06), 0.0, 0.4),
    "glass": mat("glass", (0.01, 0.012, 0.02), 0.2, 0.15),
    "pcbgreen": mat("pcbgreen", (0.02, 0.28, 0.09), 0.0, 0.45),
    "pcbred": mat("pcbred", (0.50, 0.02, 0.03), 0.0, 0.45),
    "pcbred2": mat("pcbred2", (0.45, 0.02, 0.12), 0.0, 0.45),
    "pcbblue": mat("pcbblue", (0.04, 0.14, 0.55), 0.0, 0.45),
    "pcbblack": mat("pcbblack", (0.02, 0.02, 0.025), 0.0, 0.4),
    "gold": mat("gold", (0.95, 0.70, 0.08), 0.0, 0.3),
    "brass": mat("brass", (0.80, 0.58, 0.14), 0.9, 0.3),
    "steel": mat("steel", (0.75, 0.76, 0.78), 0.9, 0.28),
    "silver": mat("silver", (0.85, 0.86, 0.88), 0.9, 0.25),
    "white": mat("white", (0.9, 0.9, 0.88), 0.0, 0.5),
    "red": mat("red", (0.75, 0.04, 0.03), 0.0, 0.35),
    "label": mat("label", (0.82, 0.83, 0.85), 0.2, 0.4),
    "wired": mat("wired", (0.8, 0.02, 0.02), 0.0, 0.5),
    "yellow": mat("yellow", (0.9, 0.75, 0.05), 0.0, 0.5),
    "floor": mat("floor", (0.97, 0.97, 0.97), 0.0, 0.9),
    "screen": mat("screen", (1, 1, 1), 0.0, 0.2, emit_img=os.path.join(os.path.dirname(os.path.abspath(__file__)), "layar_ecg.png")),
}


def paint(ob, key):
    ob.data.materials.clear(); ob.data.materials.append(C[key])
    for p in ob.data.polygons: p.use_smooth = False
    return ob


# shell dua warna (bezel depan hitam), plate hitam
shell.data.materials.clear(); shell.data.materials.append(C["orange"]); shell.data.materials.append(C["black"])
zcut = S["z"]["front_inner"] + 1.2
for p in shell.data.polygons:
    p.material_index = 1 if p.center.z > zcut else 0
paint(plate, "plate")

# ------------------------------------------------------------------ komponen
GR = {}        # key -> dict(item, empty, objs)
Z0 = S["z"]
PCB = S["pcb"]
mc, jk, uc, gl, sw = S["micro"], S["jack"], S["usbc"], S["gland"], S["switch"]
HX = S["outer"][0] / 2
YB_OUT, HY = S.get("outer_y", [-S["outer"][1] / 2, S["outer"][1] / 2])      # muka luar dinding Bawah / Atas (HY = Atas)
YC = (YB_OUT + HY) / 2                                                      # pusat outline di sumbu Y (v3: -3,4)


def group(key, item, objs):
    e = bpy.data.objects.new("G_" + key, None); bpy.context.scene.collection.objects.link(e)
    for o in objs:
        o.parent = e
    GR[key] = dict(item=item, empty=e, objs=objs)
    return e


gx = lambda xg: -(xg - 56.007)
gy_ = lambda yg: -(yg - 33.655)

# --- 1 shell (+ kaca tidak) ; saklar & gland dikelompokkan sendiri
group("shell", 1, [shell])

# --- 2 TFT: PCB merah, kaca, layar, header, slot SD
zt0, zt1, zf = Z0["tft"][0], Z0["tft"][1], Z0["glass_front"]
tft = [paint(box("tft_pcb", -49.0, 49.0, -28.17, 28.17, zt0, zt1), "pcbred"),
       paint(rbox("tft_glass", -43.0, 42.0, -27.5, 27.5, zt1, zf, 0.8), "glass"),
       paint(box("tft_hdr", 45.6, 48.1, -16.9, 17.0, zt0 - 2.5, zt0), "pcbblack"),
       paint(box("tft_sd", -20, -3, -22, -9, zt0 - 2.0, zt0), "steel")]
scr = quad_uv("tft_layar", S["window"][2] - 36.72, S["window"][2] + 36.72, -24.48, 24.48, zf + 0.03)
scr.data.materials.append(C["screen"]); tft.append(scr)
for (px, py) in S["mount_holes"]:
    tft.append(paint(cyl("tft_screw", px, py, 3.0, zt1, zf, "Z", 24), "steel"))
group("tft", 2, tft)

# --- 3 standoff M3 20 mm + stud/mur
so = []
for k, (px, py) in enumerate(S["mount_holes"]):
    so.append(paint(prism(f"standoff{k}", hexagon(px, py, 5.0), Z0["pcb"][1], zt0), "brass"))
    so.append(paint(cyl(f"stud{k}", px, py, 1.5, 0.0, Z0["pcb"][0], "Z", 16), "brass"))
    so.append(paint(prism(f"nut{k}", hexagon(px, py, 5.5), 0.0, 2.4), "steel"))
group("standoff", 3, so)

# --- 4 PCB utama + soket header ESP32 + header lain
pcb = [paint(box("pcb", PCB["x0"], PCB["x1"], PCB["y0"], PCB["y1"], Z0["pcb"][0], Z0["pcb"][1]), "pcbgreen")]
for xg in (14.986, 40.386):
    pcb.append(paint(box("socket", gx(xg) - 1.27, gx(xg) + 1.27, gy_(60.198) - 1.27, gy_(14.478) + 1.27, Z0["pcb"][1], 15.1), "pcbblack"))
pcb.append(paint(box("hdr_ad", gx(67.437) - 1.27, gx(54.737) + 1.27, gy_(32.893) - 1.27, gy_(32.893) + 1.27, Z0["pcb"][1], 10.4), "pcbblack"))
pcb.append(paint(box("pads_ad", gx(77.597) - 1.27, gx(77.597) + 1.27, gy_(18.923) - 1.27, gy_(13.843) + 1.27, Z0["pcb"][1], 8.0), "pcbblack"))
pcb.append(paint(box("jst_sw", gx(94.341) - 5.0, gx(91.841) + 5.0, gy_(9.652) - 3.0, gy_(9.652) + 3.0, Z0["pcb"][1], 12.6), "white"))
group("pcb", 4, pcb)

# --- 5 ESP32 DevKitC V4 (di atas soket)
ex = gx(27.686)
esp = [paint(box("esp_pcb", ex - 13.95, ex + 13.95, -28.0, 26.4, 15.1, 16.7), "pcbblack"),
       paint(box("esp_modul", ex - 9.0, ex + 9.0, 0.9, 26.4, 16.7, 19.8), "steel"),
       paint(box("esp_ant", ex - 9.0, ex + 9.0, 19.8, 26.4, 19.8, 19.9), "pcbblack"),
       paint(box("esp_usb", ex - 3.75, ex + 3.75, -30.2, -24.6, 16.5, 19.1), "steel"),
       paint(box("esp_chip", ex - 2.5, ex + 2.5, -17.5, -12.5, 16.7, 17.6), "pcbblack"),
       paint(box("esp_btn1", ex - 9.5, ex - 6.5, -22, -19, 16.7, 18.2), "white"),
       paint(box("esp_btn2", ex + 6.5, ex + 9.5, -22, -19, 16.7, 18.2), "white")]
group("esp32", 5, esp)

# --- 6 AD8232 + jack
ax0, ax1 = gx(78.867), gx(43.307)
ay0, ay1 = gy_(34.163), gy_(6.2)
ad = [paint(box("ad_pcb", min(ax0, ax1), max(ax0, ax1), min(ay0, ay1), max(ay0, ay1), 10.4, 12.0), "pcbred2"),
      paint(box("ad_ic", gx(54) - 2.5, gx(54) + 2.5, gy_(20) - 2.5, gy_(20) + 2.5, 12.0, 12.9), "pcbblack")]
jxc = jk["x"]
ad.append(paint(box("jack_body", jxc - 3.0, jxc + 3.0, 14.0, 27.5, 12.0, 18.0), "pcbblack"))
ad.append(paint(cyl("jack_nose", jxc, jk["zc"], 2.9, 27.5, 29.7, "Y", 24), "pcbblack"))
group("ad8232", 6, ad)

# --- 7 plug jack + kabel elektroda (3 lead)
cab = [paint(cyl("plug_boot", jxc, jk["zc"], 3.25, 29.7, 40.0, "Y", 24), "black"),
       paint(cyl("kabel_el", jxc, jk["zc"], 2.3, 40.0, 58.0, "Y", 20), "black")]
for k, (dx, col) in enumerate(((-3.2, "red"), (0.0, "yellow"), (3.2, "white"))):
    cab.append(paint(seg(f"lead{k}", (jxc, 58.0, jk["zc"]), (jxc + dx * 3.0, 80.0, jk["zc"] + (k - 1) * 5), 1.0), col))
    cab.append(paint(cyl(f"snap{k}", jxc + dx * 3.0, jk["zc"] + (k - 1) * 5, 4.5, 80.0, 82.2, "Y", 20), "silver"))
group("kabel_el", 7, cab)

# --- 8 modul powerbank TYPE-C boost
bx0, bx1 = gx(104.7), gx(80.0)
by0, by1 = gy_(34.2), gy_(13.8)
bo = [paint(box("bo_pcb", min(bx0, bx1), max(bx0, bx1), min(by0, by1), max(by0, by1), 6.8, 8.0), "pcbblue"),
      paint(rbox("bo_usbc", gx(106.1), gx(98.8), gy_(28.2), gy_(19.3), 8.0, 11.3, 1.2), "steel"),
      paint(box("bo_ind", gx(88) - 3.5, gx(88) + 3.5, gy_(26) - 3.5, gy_(26) + 3.5, 8.0, 12.0), "pcbblack"),
      paint(cyl("bo_cap", gx(90.5), gy_(17.5), 3.2, 8.0, 19.4, "Z", 24), "pcbblack"),
      paint(box("bo_ic", gx(94) - 2.0, gx(94) + 2.0, gy_(31) - 2.0, gy_(31) + 2.0, 8.0, 8.9), "pcbblack")]
group("boost", 8, bo)

# --- 9 baterai Li-ion 103450 (10x34x50) rapat sisi Bawah; menumpuk +-6 mm di tepi AD8232 (konfirmasi pengguna)
BAT = dict(x0=-41.5, x1=8.5, y0=-28.4, y1=5.6, z0=6.6, z1=16.6)      # v2: menumpuk 6,1 mm di tepi AD8232
if S.get("battery"):                                                       # v3: tidak menumpuk (dari summary.json)
    BAT = {k: S["battery"][k] for k in ("x0", "x1", "y0", "y1", "z0", "z1")}
S_BAT = BAT
ba = [paint(rbox("bat", BAT["x0"], BAT["x1"], BAT["y0"], BAT["y1"], BAT["z0"], BAT["z1"], 3.0), "gold"),
      paint(box("bat_label", BAT["x0"] + 4, BAT["x1"] - 4, BAT["y0"] + 4, BAT["y1"] - 4, BAT["z1"], BAT["z1"] + 0.12), "label"),
      paint(box("bat_tape", BAT["x1"] - 0.2, BAT["x1"] + 0.4, BAT["y0"] + 10, BAT["y1"] - 10, BAT["z0"] + 2, BAT["z1"] - 2), "yellow")]
by_c = (BAT["y0"] + BAT["y1"]) / 2
for k, (dy, col) in enumerate(((-1.2, "wired"), (1.2, "black"))):
    ba.append(paint(seg(f"bat_wire{k}", (BAT["x1"], by_c + dy, 11.6), (gx(44.32) - 1.0, gy_(46.733 + (2.038 if k else 0)) , 11.0), 0.7, 10), col))
ba.append(paint(box("bat_jst", gx(44.32) - 2.5, gx(44.32) + 2.5, gy_(48.771) - 2.5, gy_(46.733) + 2.5, 6.6, 12.6), "white"))
group("baterai", 9, ba)

# --- 10 modul PPG + konektor 4 pin + kabel keluar via gland
pp = [paint(box("ppg_pcb", gx(104.4), gx(98.3), gy_(52.2), gy_(39.4), 6.6, 7.8), "pcbblue"),
      paint(box("ppg_conn", gx(104.6), gx(98.0), gy_(50.9), gy_(40.8), 7.8, 13.0), "white")]
gyc, gzc = gl["y"], gl["zc"]
pp.append(paint(seg("ppg_cable1", (gx(101.5), gyc, 12.5), (-52.0, gyc, gzc), 2.0, 14), "black"))
pp.append(paint(cyl("ppg_cable2", gyc, gzc, 2.0, -75.0, -52.0, "X", 14), "black"))
pp.append(paint(seg("ppg_cable3", (-75.0, gyc, gzc), (-96.0, gyc - 12.0, gzc + 10.0), 2.0, 14), "black"))
sx0 = -96.0
pp.append(paint(rbox("ppg_sensor", sx0 - 11.0, sx0 + 0.5, gyc - 12.0 - 8.0, gyc - 12.0 + 8.0, gzc + 10.0 - 1.0, gzc + 10.0 + 4.0, 1.2), "pcbblack"))
pp.append(paint(box("ppg_window", sx0 - 6.0, sx0 - 1.0, gyc - 12.0 - 3.0, gyc - 12.0 + 3.0, gzc + 14.0, gzc + 14.4), "red"))
group("ppg", 10, pp)

# --- 11 saklar KCD11
swc, swz = sw["x"], sw["zc"]
yin = HY - sw["panel"]
sws = [paint(box("sw_body", swc - 6.9, swc + 6.9, yin - sw["depth"], yin, swz - 4.5, swz + 4.5), "pcbblack"),
       paint(box("sw_flange", swc - 7.4, swc + 7.4, HY, HY + 1.5, swz - 5.15, swz + 5.15), "pcbblack"),
       paint(box("sw_rocker", swc - 6.0, swc + 6.0, HY + 1.5, HY + 4.2, swz - 4.0, swz + 4.0), "red"),
       paint(box("sw_t1", swc - 3.4, swc - 2.6, yin - sw["depth"] - 5.0, yin - sw["depth"], swz - 2.4, swz + 2.4), "steel"),
       paint(box("sw_t2", swc + 2.6, swc + 3.4, yin - sw["depth"] - 5.0, yin - sw["depth"], swz - 2.4, swz + 2.4), "steel")]
group("saklar", 11, sws)

# --- 12 gland PG7 + mur
U = gl["out"]
gxu = lambda u: -(HX + u)
gp = [paint(cyl("gl_thread", gyc, gzc, 6.25, gxu(U), gxu(U - 8.0), "X", 28), "black"),
      paint(prism("gl_nut", hexagon(gyc, gzc, gl["nut_af"] - 0.4), gxu(gl["pocket"] - 3.0), gxu(gl["pocket"] - 3.0 - gl["nut_h"]), "X"), "black"),
      paint(prism("gl_hex", hexagon(gyc, gzc, 15.0), gxu(U), gxu(U + 5.0), "X"), "black"),
      paint(cyl("gl_dome", gyc, gzc, 7.4, gxu(U + 5.0), gxu(U + 17.0), "X", 28), "black")]
group("gland", 12, gp)

# --- 13 back plate
group("plate", 13, [plate])

# --- 14 sekrup M3x8 flat head
scs = []
for k, (px, py) in enumerate(S["screws"]):
    zb = S["z"]["plate_bottom"]
    scs.append(paint(cyl(f"scr_shank{k}", px, py, 1.5, zb, zb + 8.0, "Z", 16), "steel"))
    hb = bmesh.new(); n_ = 24
    lo_ = [hb.verts.new((px + 3.1 * math.cos(2 * math.pi * i / n_), py + 3.1 * math.sin(2 * math.pi * i / n_), zb)) for i in range(n_)]
    hi_ = [hb.verts.new((px + 1.5 * math.cos(2 * math.pi * i / n_), py + 1.5 * math.sin(2 * math.pi * i / n_), zb + 1.6)) for i in range(n_)]
    hb.faces.new(lo_); hb.faces.new(hi_[::-1])
    for i in range(n_):
        j = (i + 1) % n_
        hb.faces.new([lo_[i], lo_[j], hi_[j], hi_[i]])
    scs.append(paint(_obj(f"scr_head{k}", hb), "steel"))
group("sekrup", 14, scs)

def export_objects():
    d = os.path.join(CASE, "_ref", "asm"); os.makedirs(d, exist_ok=True)
    for k, g in GR.items():
        if k in ("shell", "plate"): continue
        for o in g["objs"]:
            if o.name.startswith("tft_layar"): continue
            me = o.data.copy(); me.transform(o.matrix_world)
            t = bpy.data.objects.new("tmp", me); bpy.context.scene.collection.objects.link(t)
            _select_only(t)
            bpy.ops.wm.stl_export(filepath=os.path.join(d, f"{k}__{o.name}.stl"), export_selected_objects=True, global_scale=1.0)
            bpy.data.objects.remove(t, do_unlink=True)
    json.dump(dict(BAT=BAT), open(os.path.join(d, "meta.json"), "w"))


if "stl" in MODES:
    export_objects()

# ------------------------------------------------------------------ nama item (untuk daftar)
ITEMS = {
    "shell": 1, "tft": 2, "standoff": 3, "pcb": 4, "esp32": 5, "ad8232": 6, "kabel_el": 7,
    "boost": 8, "baterai": 9, "ppg": 10, "saklar": 11, "gland": 12, "plate": 13, "sekrup": 14,
}

# ------------------------------------------------------------------ lantai, cahaya, kamera
FLOOR = None


COL_FLOOR = bpy.data.collections.new("Lantai"); bpy.context.scene.collection.children.link(COL_FLOOR)


def add_floor():
    global FLOOR
    FLOOR = box("lantai", -6000, 6000, YB_OUT - 3.0, YB_OUT, -6000, 6000)
    COL.objects.unlink(FLOOR); COL_FLOOR.objects.link(FLOOR)
    paint(FLOOR, "floor")
    return FLOOR


def remove_floor():
    global FLOOR
    if FLOOR is not None:
        bpy.data.objects.remove(FLOOR, do_unlink=True); FLOOR = None


w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.75
sc.world = w
sc.render.engine = "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
try:
    sc.eevee.taa_render_samples = 48
except Exception:
    pass


def mk_sun(direction, strength, angle=0.08):
    l = bpy.data.lights.new("S", "SUN"); l.energy = strength; l.angle = angle
    o = bpy.data.objects.new("S", l); bpy.context.scene.collection.objects.link(o)
    d = Vector(direction).normalized()
    o.rotation_euler = (-d).to_track_quat("Z", "Y").to_euler() if False else d.to_track_quat("-Z", "Y").to_euler()
    return o


mk_sun((0.5, -0.9, -0.6), 2.2)
mk_sun((-0.6, -0.2, -0.8), 0.9)
mk_sun((0.2, -0.3, 0.9), 0.5)

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.scene.collection.objects.link(cam); sc.camera = cam

# freestyle (garis tepi tipis)
sc.render.use_freestyle = True
vl = bpy.context.view_layer
vl.use_freestyle = True
fs = vl.freestyle_settings
fs.crease_angle = math.radians(32)
ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("L")
ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True
ls.select_by_collection = True; ls.collection = COL
if ls.linestyle is None:
    ls.linestyle = bpy.data.linestyles.new("garis")
ls.linestyle.color = (0.08, 0.08, 0.1); ls.linestyle.thickness = 1.3
sc.render.line_thickness_mode = "ABSOLUTE"


def look(direction, target, dist, ortho=None, lens=50, up=(0, 1, 0)):
    f = -Vector(direction).normalized()          # arah pandang
    upv = Vector(up)
    right = f.cross(upv).normalized()
    upv = right.cross(f).normalized()
    cam.location = Vector(target) - f * dist
    cam.matrix_world = Matrix(((right.x, upv.x, -f.x, cam.location.x), (right.y, upv.y, -f.y, cam.location.y),
                               (right.z, upv.z, -f.z, cam.location.z), (0, 0, 0, 1)))
    if ortho:
        cam.data.type = "ORTHO"; cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"; cam.data.lens = lens
    cam.data.clip_start, cam.data.clip_end = 1, 5000
    bpy.context.view_layer.update()
    return f


def render(path, w, h):
    if os.environ.get("NORENDER"):
        return
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("saved", os.path.basename(path), flush=True)


def set_offsets(offs):
    for k, g in GR.items():
        g["empty"].location = Vector(offs.get(k, (0, 0, 0)))
    bpy.context.view_layer.update()


def hide(keys, state=True):
    for k in keys:
        for o in GR[k]["objs"]:
            o.hide_render = state
            o.hide_viewport = state


HINT = {"shell": (-30.0, 31.75, 6.0), "pcb": (46.0, -8.0, 6.6), "plate": (-30.0, -20.0, -3.5)}


def vis_anchor(key, f_dir):
    """cari titik pada bagian `key` yang terlihat dari kamera (ray cast); kembalikan koordinat 2D normal (0-1)."""
    dg = bpy.context.evaluated_depsgraph_get()
    objs = GR[key]["objs"]
    if key in HINT:
        p = Vector(HINT[key]) + GR[key]["empty"].location
        co = world_to_camera_view(sc, cam, p)
        origin, direction = (p - f_dir * 3000, f_dir) if cam.data.type == "ORTHO" else (cam.location, (p - cam.location).normalized())
        ok, loc, nrm, idx, hit, _m = sc.ray_cast(dg, origin, direction)
        if ok and hit is not None and hit.name in {x.name for x in objs} and (loc - p).length < 1.0 and 0.03 < co.x < 0.97 and 0.03 < co.y < 0.97:
            return (co.x, co.y)
    if key == "pcb":      # titik hijau polos (bukan konektor) yang terlihat, tepat di tepi layar-luar
        board = objs[0]
        best_pt, best_sc = None, -1.0
        for gxm in range(-44, 45, 4):
            for gym in range(-24, 25, 4):
                good = True
                for ox, oy in ((0, 0), (2.5, 0), (-2.5, 0), (0, 2.5), (0, -2.5)):
                    p = Vector((gxm + ox, gym + oy, 6.6)) + GR[key]["empty"].location
                    origin = p - f_dir * 3000 if cam.data.type == "ORTHO" else cam.location
                    d = f_dir if cam.data.type == "ORTHO" else (p - origin).normalized()
                    ok, loc, nrm, idx, hit, _m = sc.ray_cast(dg, origin, d)
                    if not (ok and hit is not None and hit.name == board.name and (loc - p).length < 0.3):
                        good = False
                        break
                if not good:
                    continue
                p = Vector((gxm, gym, 6.6)) + GR[key]["empty"].location
                co = world_to_camera_view(sc, cam, p)
                if not (0.03 < co.x < 0.97 and 0.03 < co.y < 0.97):
                    continue
                sc_ = (co.x - 0.5) ** 2 + (co.y - 0.5) ** 2
                if sc_ > best_sc:
                    best_sc, best_pt = sc_, (co.x, co.y)
        if best_pt is not None:
            return best_pt
    if key == "ppg":      # arahkan ke badan sensor (bila tampil), bukan kabel; pada denah hanya konektor yang tampil
        vis = [o for o in objs if not o.hide_render]
        objs = [o for o in vis if o.name == "ppg_sensor"] or vis or objs
    cands = []
    rnd = random.Random(7)
    for o in objs:
        mw = o.matrix_world
        vs = [mw @ v.co for v in o.data.vertices]
        if len(vs) > 300:
            vs = rnd.sample(vs, 300)
        cands += [(p, o) for p in vs]
    # pusat massa objek terbesar
    allp = [p for p, _ in cands]
    cen = sum(allp, Vector()) / len(allp)
    cands.sort(key=lambda t: (t[0] - cen).length)
    best = None
    for p, o in cands[:400]:
        co = world_to_camera_view(sc, cam, p)
        if not (0.03 < co.x < 0.97 and 0.03 < co.y < 0.97):
            continue
        if cam.data.type == "ORTHO":
            origin, direction = p - f_dir * 3000, f_dir
        else:
            origin = cam.location; direction = (p - origin).normalized()
        ok, loc, nrm, idx, hit, _m = sc.ray_cast(dg, origin, direction)
        if ok and hit is not None and hit.name in {x.name for x in objs} and (loc - p).length < 0.6:
            best = (co.x, co.y)
            break
    if best is None:
        c = world_to_camera_view(sc, cam, cen)
        best = (c.x, c.y)
    return best


def project_points(pts):
    out = {}
    for k, p in pts.items():
        co = world_to_camera_view(sc, cam, Vector(p))
        out[k] = (co.x, co.y)
    return out


def anchors(f_dir, extra=None):
    d = {}
    for k in GR:
        if GR[k]["objs"][0].hide_render:
            continue
        d[k] = vis_anchor(k, f_dir)
    return d


EXPL_A = {"plate": (0, 0, -78), "sekrup": (0, 0, -105), "tft": (0, 0, 72), "shell": (0, 0, 140),
          "saklar": (0, 0, 140), "gland": (0, 0, 140)}
EXPL_B = {"esp32": (46, 8, 44), "ad8232": (4, 50, 40), "kabel_el": (4, 50, 40), "boost": (-54, 44, 40),
          "baterai": (-6, -54, 36), "ppg": (-62, -30, 32)}
DIR_EXP = (-0.42, 0.74, 0.55)
HIDE_B = ["shell", "tft", "standoff", "saklar", "gland", "plate", "sekrup"]


def png_transparent():
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = "RGBA"


if "all" in MODES or "assembled" in MODES:
    set_offsets({}); remove_floor(); add_floor()
    sc.render.film_transparent = False
    look((-0.62, 0.42, 0.66), (-8, 6 + YC, 15), 560, ortho=None, lens=50)
    render(os.path.join(OUT, "render_rakitan_depan.png"), RES, int(RES * 0.78))
    json.dump(project_points({"layar": (S["window"][2] + 25, 15, S["z"]["top"]), "saklar": (swc, HY + 4.2, swz), "kabel_el": (jxc, 50.0, jk["zc"]),
                              "usbc": (-HX, uc["y"], uc["zc"]), "gland": (gxu(U + 12.0), gyc, gzc), "sensor": (sx0 - 3.5, gyc - 12.0, gzc + 14.4)}),
              open(os.path.join(OUT, "points_depan.json"), "w"), indent=1)
if "all" in MODES or "back" in MODES:
    set_offsets({}); remove_floor(); add_floor()
    sc.render.film_transparent = False
    look((-0.55, 0.45, -0.7), (-6, 4 + YC, 12), 560, lens=50)
    render(os.path.join(OUT, "render_rakitan_belakang.png"), RES, int(RES * 0.78))
    json.dump(project_points({"slot1": (S["belt"]["slot_cx"], 18.0, S["z"]["plate_bottom"]), "slot2": (-S["belt"]["slot_cx"], -18.0, S["z"]["plate_bottom"]),
                              "sekrup": (S["screws"][0][0], S["screws"][0][1], S["z"]["plate_bottom"]), "plate": (-10.0, -12.0, S["z"]["plate_bottom"])}),
              open(os.path.join(OUT, "points_belakang.json"), "w"), indent=1)
if "all" in MODES or "expA" in MODES:
    remove_floor(); png_transparent()
    set_offsets(EXPL_A)
    f = look(DIR_EXP, (-6, YC, 28), 1500, ortho=float(os.environ.get("SCA", "330")))
    render(os.path.join(OUT, "render_eksplodeA.png"), int(RES * 1.5), int(RES * 1.5))
    json.dump(anchors(f), open(os.path.join(OUT, "anchors_eksplodeA.json"), "w"), indent=1)
if "all" in MODES or "expB" in MODES:
    remove_floor(); png_transparent()
    hide(HIDE_B, True)
    set_offsets(EXPL_B)
    f = look(DIR_EXP, (-14, 4 + YC, 22), 1500, ortho=float(os.environ.get("SCB", "330")))
    render(os.path.join(OUT, "render_eksplodeB.png"), int(RES * 1.5), int(RES * 1.2))
    json.dump(anchors(f), open(os.path.join(OUT, "anchors_eksplodeB.json"), "w"), indent=1)
    hide(HIDE_B, False)
if "all" in MODES or "layout" in MODES:
    remove_floor(); png_transparent()
    set_offsets({})
    hide(["shell", "tft", "standoff", "saklar", "gland", "plate", "sekrup"], True)
    cable_objs = [o for o in GR["ppg"]["objs"] if o.name in ("ppg_cable1", "ppg_cable2", "ppg_cable3", "ppg_sensor", "ppg_window")]
    for o in cable_objs: o.hide_render = True
    f = look((0.0, 0.0, 1.0), (0, YC, 10), 900, ortho=125)
    render(os.path.join(OUT, "render_denah.png"), RES, int(RES * 0.62))
    json.dump(anchors(f), open(os.path.join(OUT, "anchors_denah.json"), "w"), indent=1)
    hide(["shell", "tft", "standoff", "saklar", "gland", "plate", "sekrup"], False)
    for o in cable_objs: o.hide_render = False

json.dump(dict(ITEMS=ITEMS, BAT=BAT), open(os.path.join(OUT, "items.json"), "w"), indent=1)
print("OK")
