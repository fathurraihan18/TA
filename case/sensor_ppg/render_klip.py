"""Render berwarna klip sensor PPG (Blender Eevee, latar transparan) + titik jangkar balon.
python render_klip.py -- <folder_klip> <folder_render> [mode ...]
mode: iso (rakitan nominal), pakai (jari terpasang, rahang terbuka 8 derajat), meledak (eksplode + jangkar), bawah (tanpa tutup, tampak dari bawah)
Env: RES (lebar piksel, default 1500)
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

A_ = sys.argv[sys.argv.index("--") + 1:]
D, OUT = A_[0], A_[1]
MODES = A_[2:] or ["iso", "pakai", "meledak", "bawah"]
RES = int(os.environ.get("RES", "1500"))
os.makedirs(OUT, exist_ok=True)
R = os.path.join(D, "_ref")
S = json.load(open(os.path.join(R, "summary.json")))
XP = S["XP"]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
sc.render.film_transparent = True
sc.render.image_settings.color_mode = "RGBA"
try:
    sc.eevee.taa_render_samples = 48
except Exception:
    pass
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.45
sc.world = w


def mat(name, color, rough=0.55, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


MAT = {
    "A": mat("A", (0.62, 0.64, 0.68, 1)), "B": mat("B", (0.72, 0.68, 0.58, 1)), "C": mat("C", (0.12, 0.3, 0.72, 1)), "D": mat("D", (0.9, 0.38, 0.05, 1)),
    "board": mat("board", (0.03, 0.03, 0.04, 1), 0.4), "sensor": mat("sensor", (0.1, 0.1, 0.12, 1), 0.3), "solder": mat("solder", (0.75, 0.75, 0.78, 1), 0.3, 0.8),
    "cable": mat("cable", (0.85, 0.12, 0.1, 1), 0.5), "spring": mat("spring", (0.7, 0.72, 0.75, 1), 0.25, 1.0), "screw": mat("screw", (0.06, 0.06, 0.07, 1), 0.35, 0.6),
    "finger": mat("finger", (0.9, 0.62, 0.5, 1), 0.7), "foam": mat("foam", (0.15, 0.15, 0.17, 1), 0.9),
    "w1": mat("w1", (0.95, 0.8, 0.1, 1)), "w2": mat("w2", (0.95, 0.95, 0.95, 1)), "w3": mat("w3", (0.85, 0.1, 0.1, 1)), "w4": mat("w4", (0.05, 0.05, 0.05, 1)),
}


def load_stl(path, name, m):
    bpy.ops.wm.stl_import(filepath=path)
    ob = bpy.context.selected_objects[0]
    ob.name = name
    ob.data.materials.append(m)
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e); e.location = loc
    return e


def seg(name, p0, p1, r, m, n=16):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0; L = d.length
    bm = bmesh.new()
    lo = [bm.verts.new((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), 0)) for k in range(n)]
    hi = [bm.verts.new((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), L)) for k in range(n)]
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    ob.rotation_mode = "QUATERNION"; ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized()); ob.location = p0
    ob.data.materials.append(m)
    return ob


def polyline(name, pts, r, m):
    obs = [seg(f"{name}_{i}", a, b, r, m) for i, (a, b) in enumerate(zip(pts[:-1], pts[1:]))]
    for (x, y, z) in pts[1:-1]:
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=8, radius=r)
        for v in bm.verts: v.co += Vector((x, y, z))
        me = bpy.data.meshes.new(name + "_j"); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name + "_j", me); bpy.context.scene.collection.objects.link(o); o.data.materials.append(m); obs.append(o)
    return obs


def helix(name, x, y, z0, z1, od, wire, turns, m):
    """pegas tekan: kawat membentuk heliks sepanjang sumbu Z dari z0 ke z1."""
    Rm = (od - wire) / 2
    bm = bmesh.new()
    nstep = int(turns * 28)
    nc = 8
    rings = []
    for i in range(nstep + 1):
        t = i / nstep
        a = 2 * math.pi * turns * t
        c = Vector((x + Rm * math.cos(a), y + Rm * math.sin(a), z0 + (z1 - z0) * t))
        tan = Vector((-Rm * math.sin(a) * 2 * math.pi * turns, Rm * math.cos(a) * 2 * math.pi * turns, (z1 - z0))).normalized()
        nrm = Vector((math.cos(a), math.sin(a), 0))
        bn = tan.cross(nrm).normalized()
        nrm = bn.cross(tan).normalized()
        ring = []
        for k in range(nc):
            b = 2 * math.pi * k / nc
            ring.append(bm.verts.new(c + (nrm * math.cos(b) + bn * math.sin(b)) * (wire / 2)))
        rings.append(ring)
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for k in range(nc):
            kk = (k + 1) % nc
            bm.faces.new([a_[k], a_[kk], b_[kk], b_[k]])
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.data.materials.append(m)
    return ob


# ---------------------------------------------------------------- bagian
G = {}
G["A"] = [load_stl(os.path.join(R, "A_desain.stl"), "A", MAT["A"])]
G["B"] = [load_stl(os.path.join(R, "B_desain.stl"), "B", MAT["B"])]
G["C"] = [load_stl(os.path.join(R, "C_desain.stl"), "C", MAT["C"])]
G["D"] = [load_stl(os.path.join(R, "D_desain.stl"), "D", MAT["D"])]
G["D"][0].location = (XP + S["seats_ls"][0], 0, S["BLK"][0] + 6.0)          # shim contoh melayang di atas pin dudukan 1
brd = load_stl(os.path.join(R, "ref_Modul_HW605.stl"), "board", MAT["board"])
G["board"] = [brd]
# sensor dan solder diberi warna terpisah: bagian di atas PCB
bm = bmesh.new()
XS, ZL, BT = S["XS"], S["Z_L"], S["board"]["t"]
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co = Vector((XS + v.co.x * S["board"]["sens_l"], v.co.y * S["board"]["sens_w"], ZL + BT + S["board"]["sens_h"] / 2 + v.co.z * S["board"]["sens_h"]))
me = bpy.data.meshes.new("sens"); bm.to_mesh(me); bm.free()
so = bpy.data.objects.new("sens", me); bpy.context.scene.collection.objects.link(so); so.data.materials.append(MAT["sensor"])
G["board"].append(so)
cab_z = S["z_ax"]
G["cable"] = polyline("cable", [(52.0, -8.4, cab_z), (59.0, 0.0, cab_z), (S["XL"] + 14.0, 0.0, cab_z)], S["cable_d"] / 2, MAT["cable"])
# 4 kawat (bundel) dari pad ke ujung jaket
pad_x = XS + S["board"]["l"] / 2 - 1.5
zw = ZL + BT + 0.9
wires = []
for i, (m_, off) in enumerate((("w1", -3.81), ("w2", -1.27), ("w3", 1.27), ("w4", 3.81))):
    k = (i - 1.5) * 0.9
    pts = [(pad_x, off, zw), (33.0, off * 0.35 + k * 0.6, zw), (37.5, -8.4 + k, zw + 0.2), (52.0, -8.4 + k, cab_z)]
    wires += polyline(f"wire{i}", pts, 0.5, MAT[m_])
G["wires"] = wires
G["spring"] = [helix("spring", XP + S["seats_ls"][0], 0.0, S["BLK"][0], S["BLK"][1] + S["pocket_depth"][0], S["spring"]["od"], S["spring"]["wire"], S["spring"]["n_active"] + 1.5, MAT["spring"])]
scr = load_stl(os.path.join(R, "ref_Sekrup_engsel.stl"), "screw", MAT["screw"])
G["screw"] = [scr]
fing = load_stl(os.path.join(R, "ref_Jari_telunjuk.stl"), "finger", MAT["finger"])
G["finger"] = [fing]
# busa 1 mm pada rahang B (rata di lekuk, hanya untuk gambar)
foam = bpy.data.objects.new("foam", None)
bm = bmesh.new()
n = 18
ys = [-8.0 + 16.0 * i / n for i in range(n + 1)]
R_C = S["cradle"]["R"]
top, bot = [], []
for x in (10.0, 33.0):
    for y in ys:
        zb = S["ZP"] + (R_C - math.sqrt(R_C ** 2 - y * y))
        top.append((x, y, zb + 0.05)); bot.append((x, y, zb - 1.0))
vt = [bm.verts.new(p) for p in top]; vb = [bm.verts.new(p) for p in bot]
m_ = n + 1
for i in range(n):
    bm.faces.new([vt[i], vt[i + 1], vt[m_ + i + 1], vt[m_ + i]])
    bm.faces.new([vb[m_ + i], vb[m_ + i + 1], vb[i + 1], vb[i]])
    bm.faces.new([vt[i], vb[i], vb[i + 1], vt[i + 1]])
    bm.faces.new([vt[m_ + i + 1], vb[m_ + i + 1], vb[m_ + i], vt[m_ + i]])
bm.faces.new([vt[0], vt[m_], vb[m_], vb[0]]); bm.faces.new([vt[n], vb[n], vb[m_ + n], vt[m_ + n]])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("foam"); bm.to_mesh(me); bm.free()
fo = bpy.data.objects.new("foam", me); bpy.context.scene.collection.objects.link(fo); fo.data.materials.append(MAT["foam"])
G["foam"] = [fo]

# grup -> empty induk (untuk offset eksplode dan rotasi B)
PAR = {}
for k, obs in G.items():
    e = empty("G_" + k)
    for o in obs:
        o.parent = e
    PAR[k] = e
pivot_B = empty("pivot_B", (XP, 0, 0))


def set_pose(offsets=None, theta=0.0, show=("A", "B", "C", "D", "board", "cable", "wires", "spring", "screw", "foam")):
    offsets = offsets or {}
    for k, e in PAR.items():
        e.location = Vector(offsets.get(k, (0, 0, 0)))
        e.rotation_euler = (0, 0, 0)
        for o in G[k]:
            o.hide_render = k not in show
    # B dan komponen yang ikut B (busa) berputar di sekitar sumbu engsel sebesar theta (positif = membuka depan)
    for k in ("B", "foam"):
        if k in show:
            a = math.radians(theta)
            c, s_ = math.cos(a), math.sin(a)
            # rotasi sekitar +Y melalui (XP,0,0): lokasi empty = pivot + R(0 - pivot) - ... diselesaikan dengan matriks dunia
            PAR[k].matrix_world = Matrix.Translation((XP, 0, 0)) @ Matrix.Rotation(a, 4, "Y") @ Matrix.Translation((-XP, 0, 0)) @ Matrix.Translation(Vector(offsets.get(k, (0, 0, 0))))
    bpy.context.view_layer.update()


def sun(d, e):
    l = bpy.data.lights.new("s", "SUN"); l.energy = e; l.angle = 0.1
    o = bpy.data.objects.new("s", l); sc.collection.objects.link(o)
    o.rotation_euler = Vector(d).normalized().to_track_quat("-Z", "Y").to_euler()


sun((0.5, 0.7, -0.6), 1.7); sun((-0.6, -0.5, -0.4), 0.7); sun((0.2, -0.2, 0.9), 0.4)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"
sc.render.use_freestyle = True
vl = bpy.context.view_layer
vl.use_freestyle = True
fs = vl.freestyle_settings
fs.crease_angle = math.radians(35)
ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("L")
ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True
if ls.linestyle is None:
    ls.linestyle = bpy.data.linestyles.new("garis")
ls.linestyle.color = (0.05, 0.05, 0.08); ls.linestyle.thickness = 1.2
sc.render.line_thickness_mode = "ABSOLUTE"


def look(direction, target, ortho, w, h):
    f = -Vector(direction).normalized()
    up = Vector((0, 0, 1))
    right = f.cross(up).normalized()
    upv = right.cross(f).normalized()
    cam.location = Vector(target) - f * 800
    cam.matrix_world = Matrix(((right.x, upv.x, -f.x, cam.location.x), (right.y, upv.y, -f.y, cam.location.y), (right.z, upv.z, -f.z, cam.location.z), (0, 0, 0, 1)))
    cam.data.ortho_scale = ortho
    cam.data.clip_start, cam.data.clip_end = 1, 3000
    sc.render.resolution_x, sc.render.resolution_y = w, h
    bpy.context.view_layer.update()


def render(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("saved", os.path.basename(path), flush=True)


def proj(p):
    co = world_to_camera_view(sc, cam, Vector(p))
    return (co.x, co.y)


if "iso" in MODES:
    set_pose(show=("A", "B", "C", "board", "cable", "wires", "screw", "spring", "foam"))
    look((-0.75, -0.9, 0.6), (33, 0, -1), 100, RES, int(RES * 0.62))
    render(os.path.join(OUT, "klip_iso.png"))
if "pakai" in MODES:
    set_pose(theta=0.0, show=("A", "B", "C", "board", "cable", "screw", "spring", "foam", "finger"))
    look((-0.75, -0.9, 0.55), (28, 0, -1), 100, RES, int(RES * 0.62))
    render(os.path.join(OUT, "klip_pakai.png"))
if "bawah" in MODES:
    set_pose(show=("A", "board", "cable", "wires", "spring"))
    look((0.5, -0.7, -0.9), (35, -2, -9), 100, RES, int(RES * 0.62))
    render(os.path.join(OUT, "klip_bawah.png"))
if "meledak" in MODES:
    off = {"B": (0, 0, 46), "foam": (0, 0, 30), "spring": (0, 0, 24), "screw": (0, 40, 0), "D": (0, 0, 14), "C": (0, 0, -34), "board": (0, 0, -17),
           "cable": (0, 0, 0), "wires": (0, 0, -17)}
    set_pose(offsets=off, show=("A", "B", "C", "D", "board", "cable", "wires", "spring", "screw", "foam"))
    G["D"][0].location = (XP + S["seats_ls"][0] + 9.0, 14.0, S["BLK"][0] + 6.0)
    G["spring"][0].location = (0, 0, 0)
    look((-0.75, -0.95, 0.6), (33, 8, 8), 150, RES, int(RES * 0.92))
    render(os.path.join(OUT, "klip_meledak.png"))
    anchors = {
        "A": (3.0, -13.0, -8.0),
        "B": (20.0, -13.0, 4.0 + off["B"][2]),
        "C": (50.0, -10.6, S["Z_O"] + off["C"][2]),
        "D": (XP + S["seats_ls"][0] + 9.0, 14.0, S["BLK"][0] + 6.5 + 14.0),
        "board": (S["XS"] - 6.0, 6.0, S["Z_L"] + S["board"]["t"] + off["board"][2]),
        "cable": (S["XL"] + 10.0, 0.0, cab_z),
        "spring": (XP + S["seats_ls"][0], 0.0, S["BLK"][0] + 3.0 + off["spring"][2]),
        "screw": (XP, 40.0 + 6.0, 0.0),
        "foam": (20.0, 6.0, S["ZP"] - 1.0 + off["foam"][2]),
        "wires": (40.0, -8.4, S["Z_L"] + 3.0 + off["wires"][2]),
    }
    json.dump({k: proj(v) for k, v in anchors.items()}, open(os.path.join(OUT, "anchors_meledak.json"), "w"), indent=1)
print("OK")
