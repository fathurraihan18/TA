"""Render visual pemasangan varian --penahan (v2c / v3c): 4 langkah + hasil jadi.
python render_pemasangan.py -- <folder_penahan> <folder_komponen_asm> <folder_keluaran>
  folder_komponen_asm = folder STL komponen nyata (mis. v3_baterai/_ref/asm); baterai dan klip PPG tidak dipakai.
Keluaran: langkah1.png ... langkah4.png, hasil.png (latar transparan)
"""
import bpy, sys, os, glob, math, json
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
D, ASM, OUT = a
os.makedirs(OUT, exist_ok=True)
R = os.path.join(D, "_ref")
S = json.load(open(os.path.join(R, "summary.json")))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x = 1400; sc.render.resolution_y = 1000
sc.render.film_transparent = True; sc.render.image_settings.color_mode = "RGBA"
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.45; sc.world = w
for d, e in (((-0.3, 0.4, 0.9), 1.5), ((0.5, -0.4, 0.6), 0.6), ((0.3, 0.2, -0.9), 1.3), ((-0.5, -0.4, -0.5), 0.6)):
    l = bpy.data.lights.new("s", "SUN"); l.energy = e; o = bpy.data.objects.new("s", l); sc.collection.objects.link(o)
    o.rotation_euler = Vector(d).to_track_quat("-Z", "Y").to_euler()
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"
sc.render.use_freestyle = True
vl = bpy.context.view_layer; vl.use_freestyle = True
fs = vl.freestyle_settings; fs.crease_angle = math.radians(38)
ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("L")
ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True
if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new("g")
ls.linestyle.color = (0.07, 0.07, 0.09); ls.linestyle.thickness = 1.0

MAT = {}


def mat(col, rough=0.5, metal=0.0):
    key = (col, rough, metal)
    if key not in MAT:
        m = bpy.data.materials.new("m%d" % len(MAT)); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
        MAT[key] = m
    return MAT[key]


def load(path, col, rough=0.5, metal=0.0, name=None):
    bpy.ops.wm.stl_import(filepath=path); o = bpy.context.selected_objects[0]
    if name: o.name = name
    o.data.materials.append(mat(col, rough, metal))
    for p in o.data.polygons: p.use_smooth = False
    return o


def comp_color(fn):
    g, n = fn[:-4].split("__")
    nl = n.lower()
    if g == "pcb": return (0.14, 0.60, 0.30), 0.5, 0.0
    if g == "tft":
        if "pcb" in nl: return (0.75, 0.10, 0.10), 0.5, 0.0
        return (0.03, 0.04, 0.07), 0.3, 0.0
    if g == "standoff": return (0.85, 0.68, 0.22), 0.35, 0.8
    if g == "esp32":
        if "perisai" in nl: return (0.78, 0.78, 0.80), 0.3, 0.8
        if "pin" in nl: return (0.85, 0.72, 0.35), 0.35, 0.8
        return (0.05, 0.05, 0.06), 0.5, 0.0
    if g == "ad8232":
        if "pcb" in nl: return (0.70, 0.10, 0.12), 0.5, 0.0
        if "metal" in nl: return (0.75, 0.75, 0.78), 0.3, 0.8
        return (0.04, 0.04, 0.05), 0.5, 0.0
    if g == "boost": return (0.15, 0.30, 0.78), 0.5, 0.0
    if g == "gland": return (0.08, 0.08, 0.09), 0.5, 0.0
    if g == "saklar": return ((0.85, 0.12, 0.12) if "rocker" in nl else (0.08, 0.08, 0.09)), 0.5, 0.0
    return (0.5, 0.5, 0.5), 0.5, 0.0


ORANGE, DARK, PEN, STEEL, EPOXY = (0.98, 0.62, 0.22), (0.27, 0.28, 0.32), (0.92, 0.10, 0.55), (0.78, 0.78, 0.82), (0.95, 0.95, 0.25)

shell = load(os.path.join(R, "shell_design.stl"), ORANGE, 0.55)
plate = load(os.path.join(R, "plate_design.stl"), DARK, 0.6)
pen = load(os.path.join(R, "penahan_design.stl"), PEN, 0.45)
screws = load(os.path.join(R, "ref_Sekrup_M3x8.stl"), (0.55, 0.56, 0.60), 0.4, 0.5)
stack, onshell = [], []
for f in sorted(glob.glob(os.path.join(ASM, "*.stl"))):
    fn = os.path.basename(f)
    g = fn.split("__")[0]
    if g in ("baterai", "ppg", "kabel_el", "sekrup"): continue
    col, ro, me = comp_color(fn)
    o = load(f, col, ro, me)
    (onshell if g in ("gland", "saklar") else stack).append(o)

# lapisan epoxy pada muka penahan yang menghadap dinding (digambar 1.2 mm supaya terlihat; nyatanya celah 0.3 mm)
import bmesh


def box_obj(name, x0, x1, y0, y1, z0, z1, col):
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    bmesh.ops.convex_hull(bm, input=vs)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.data.materials.append(mat(col, 0.4))
    return o


epoxy = []
P_ = S["penahan"]
for pc in P_.get("pieces", [dict(side=b["side"], x=[b["x"] - P_["w"] / 2, b["x"] + P_["w"] / 2], y=b["y"], zbar=[-0.5, P_["top"]]) for b in P_["blocks"]]):
    ya, yb = pc["y"]; side = pc["side"]
    face = yb if side > 0 else ya                                            # muka penahan yang menghadap dinding
    y0, y1 = (face, face + 1.2) if side > 0 else (face - 1.2, face)
    epoxy.append(box_obj("epoxy", pc["x"][0], pc["x"][1], y0, y1, pc["zbar"][0], pc["zbar"][1], EPOXY))

ALL = [shell, plate, pen, screws] + stack + onshell + epoxy
BASE = {o: o.location.copy() for o in ALL}


def setup(show, offsets=None):
    for o in ALL:
        o.hide_render = o not in show
        o.location = BASE[o] + Vector((offsets or {}).get(o, (0, 0, 0)))


def shot(name, d, target, ortho):
    d = Vector(d).normalized(); cam.location = Vector(target) + d * 700
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = ortho
    sc.render.filepath = os.path.join(OUT, name); bpy.ops.render.render(write_still=True)


REAR = (0.62, -0.72, -0.55)              # kamera di belakang-kanan-bawah: lihat dari belakang
FRONT = (0.5, -0.65, 0.75)
Z = lambda dz: {"z": dz}
# ---- langkah 1: tumpukan didorong lurus dari belakang ke shell
off = {o: (0, 0, -62) for o in stack}
setup([shell] + onshell + stack, off)
shot("langkah1.png", REAR, (0, -2, -6), 235)
# ---- langkah 2: penahan di atas plate, 4 sekrup dari belakang plate
off = {screws: (0, 0, -16)}
setup([plate, pen, screws], off)
shot("langkah2.png", FRONT, (0, 0, 0), 175)
# ---- langkah 3: plate + penahan (+epoxy pada muka dinding) didorong ke shell berisi tumpukan
off = {o: (0, 0, -60) for o in [plate, pen, screws] + epoxy}
setup([shell] + onshell + stack + [plate, pen, screws] + epoxy, off)
shot("langkah3.png", REAR, (0, -2, -18), 235)
# ---- langkah 4: terpasang, tampak belakang: kepala sekrup rata dengan plate (tidak ada lubang terbuka)
setup([shell] + onshell + [plate, screws, pen] + stack)
pen.hide_render = True
shot("hasil_belakang.png", (0.12, -0.38, -1.0), (0, 0, 0), 175)
# ---- tampak dalam: penahan di bawah PCB, dilihat dari belakang dengan plate dilepas
setup([shell] + onshell + stack + [pen])
shot("hasil_dalam.png", (0.45, -0.75, -1.0), (0, 0, 6), 160)
print("done")
