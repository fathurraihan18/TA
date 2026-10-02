"""Render pratinjau komponen berwarna dari daftar bagian (JSON {nama: {file, color}}).
python render_komponen.py -- <parts.json> <png_prefix> [ortho_mm] [geser x y z]   (env PX="lebar,tinggi", bawaan 1400,900)"""
import bpy, sys, os, json, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
pj, out = a[0], a[1]
ORTHO = float(a[2]) if len(a) > 2 else None
SHIFT = [float(v) for v in a[3:6]] if len(a) > 5 else [0, 0, 0]
base = os.path.dirname(os.path.abspath(pj))
parts = json.load(open(pj))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"; _px = [int(v) for v in os.environ.get("PX", "1400,900").split(",")]   # PX="lebar,tinggi"
sc.render.resolution_x, sc.render.resolution_y = _px
sc.view_settings.view_transform = "Standard"
sc.render.film_transparent = True; sc.render.image_settings.color_mode = "RGBA"
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.45; sc.world = w
objs = []
for k, p in parts.items():
    f = os.path.join(base, p["file"]) if "file" in p else p["path"]
    bpy.ops.wm.stl_import(filepath=f); o = bpy.context.selected_objects[0]; objs.append(o)
    m = bpy.data.materials.new(k); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*p["color"][:3], 1); b.inputs["Roughness"].default_value = 0.45
    o.data.materials.append(m)
allv = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
c = sum(allv, Vector()) / len(allv)
size = max((max(v[i] for v in allv) - min(v[i] for v in allv)) for i in range(3))


def sun(d, e):
    l = bpy.data.lights.new("s", "SUN"); l.energy = e; o = bpy.data.objects.new("s", l); sc.collection.objects.link(o)
    o.rotation_euler = Vector(d).to_track_quat("-Z", "Y").to_euler()


sun((0.4, -0.6, -0.7), 1.8); sun((-0.6, 0.3, -0.4), 0.8); sun((0, 0, -1), 0.4)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = ORTHO or size * 1.2
sc.render.use_freestyle = True
vl = bpy.context.view_layer; vl.use_freestyle = True
fs = vl.freestyle_settings; fs.crease_angle = math.radians(35)
ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("L")
ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True
if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new("g")
ls.linestyle.color = (0.05, 0.05, 0.08); ls.linestyle.thickness = 0.9
for nm, d in (("iso", (1, -1.2, 0.9)), ("top", (0.0, -0.0001, 1))):
    d = Vector(d).normalized(); cam.location = c + d * 600
    # tampak atas: kamera tanpa rotasi menatap -Z dengan +X ke kanan dan +Y ke atas (selaras dengan koordinat model)
    cam.rotation_euler = (0, 0, 0) if nm == "top" else (-d).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{out}_{nm}.png"; bpy.ops.render.render(write_still=True)
json.dump(dict(center=[c.x, c.y, c.z], ortho=cam.data.ortho_scale, px=[sc.render.resolution_x, sc.render.resolution_y]), open(out + "_info.json", "w"))
print("done")
