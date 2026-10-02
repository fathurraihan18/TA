"""Tahap 1 gambar teknik: render garis proyeksi ortografis (Blender Freestyle) per tampak.
Jalankan: python gambar_render.py <folder_blend> <folder_output>
"""
import bpy, math, os, sys, json
from mathutils import Vector, Matrix

CASE_DIR = sys.argv[sys.argv.index("--") + 1]
BLEND = os.path.join(CASE_DIR, "ECG_PPG_Cover.blend")
_S = json.load(open(os.path.join(CASE_DIR, "_ref", "summary.json")))
YC = sum(_S["outer_y"]) / 2 if "outer_y" in _S else 0.0       # pusat outline sumbu Y (v3: rongga Bawah diperlebar -> -3,4)
OUT = sys.argv[sys.argv.index("--") + 2]
os.makedirs(OUT, exist_ok=True)
PX = 12  # piksel per mm

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
sc.render.film_transparent = False
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
sc.world = w

white = bpy.data.materials.new("putih"); white.use_nodes = True
nt = white.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1, 1, 1, 1); em.inputs["Strength"].default_value = 1.0
outn = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], outn.inputs["Surface"])
for ob in bpy.data.objects:
    if ob.name.startswith("Ref_"):
        ob.hide_render = True
    elif ob.type == "MESH":
        ob.data.materials.clear(); ob.data.materials.append(white)

# Freestyle: garis hitam tegas
sc.render.use_freestyle = True
vl = bpy.context.view_layer
vl.use_freestyle = True
fs = vl.freestyle_settings
fs.crease_angle = math.radians(35)
ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("L")
ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True
ls.select_contour = True; ls.select_external_contour = True
if ls.linestyle is None:
    ls.linestyle = bpy.data.linestyles.new("garis")
ls.linestyle.color = (0, 0, 0)
ls.linestyle.thickness = 2.4
sc.render.line_thickness_mode = "ABSOLUTE"

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.clip_start, cam.data.clip_end = 1, 2000

# (nama, arah kamera ke objek f, up, jendela (w,h) mm, pusat jendela dalam koordinat model)
VIEWS = {
    "depan":   dict(f=(0, 0, -1), up=(0, 1, 0), win=(140, 76), ctr=(0, YC, 15.2)),
    "belakang": dict(f=(0, 0, 1), up=(0, 1, 0), win=(140, 76), ctr=(0, YC, 15.2)),
    "atas":    dict(f=(0, -1, 0), up=(0, 0, -1), win=(140, 48), ctr=(0, 0, 15.2)),
    "bawah":   dict(f=(0, 1, 0), up=(0, 0, 1), win=(140, 48), ctr=(0, 0, 15.2)),
    "kiri":    dict(f=(-1, 0, 0), up=(0, 1, 0), win=(48, 76), ctr=(0, YC, 15.2)),
    "kanan":   dict(f=(1, 0, 0), up=(0, 1, 0), win=(48, 76), ctr=(0, YC, 15.2)),
}

for name, v in VIEWS.items():
    f = Vector(v["f"]).normalized(); up = Vector(v["up"]).normalized()
    right = f.cross(up).normalized()
    ctr = Vector(v["ctr"])
    # lokasi kamera: mundur 600 mm dari titik pusat sepanjang -f; pusat jendela: pakai shift di bidang tampak
    cam.location = ctr - f * 600
    z_axis = -f
    y_axis = up
    x_axis = right
    cam.matrix_world = Matrix(((x_axis.x, y_axis.x, z_axis.x, cam.location.x),
                               (x_axis.y, y_axis.y, z_axis.y, cam.location.y),
                               (x_axis.z, y_axis.z, z_axis.z, cam.location.z),
                               (0, 0, 0, 1)))
    ww, hh = v["win"]
    cam.data.ortho_scale = max(ww, hh)
    sc.render.resolution_x, sc.render.resolution_y = int(ww * PX), int(hh * PX)
    sc.render.filepath = os.path.join(OUT, f"garis_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("saved", name, flush=True)
