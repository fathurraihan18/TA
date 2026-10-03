"""Render pratinjau perbaikan shell v2: bagian yang dibuang (merah, di atas shell v2b hasil akhir) dan jig bor (biru) di atas shell v2.
python render_perbaikan.py -- <shell_v2.stl> <shell_v2b.stl> <bagian_dibuang.stl> <jig_ATAS.stl> <jig_BAWAH.stl> <prefix_keluaran>
"""
import bpy, sys, math
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
shell_f, shell_b_f, rem_f, jigA_f, jigB_f, out = a
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x = 1600; sc.render.resolution_y = 1100
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.7; sc.world = w


def load(f, col, alpha=1.0, shift=(0, 0, 0)):
    bpy.ops.wm.stl_import(filepath=f); o = bpy.context.selected_objects[0]
    o.location = shift
    m = bpy.data.materials.new("m"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 0.6
    o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = False
    return o


def sun(d, e):
    l = bpy.data.lights.new("s", "SUN"); l.energy = e; o = bpy.data.objects.new("s", l); sc.collection.objects.link(o)
    o.rotation_euler = Vector(d).to_track_quat("-Z", "Y").to_euler()


sun((-0.3, 0.4, 0.9), 2.4); sun((0.5, -0.4, 0.6), 1.2); sun((0, 0, 1), 0.8)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 135
sc.render.use_freestyle = True
vl = bpy.context.view_layer; vl.use_freestyle = True
fs = vl.freestyle_settings; fs.crease_angle = math.radians(35)
ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("L")
ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True
if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new("g")
ls.linestyle.color = (0.1, 0.1, 0.12); ls.linestyle.thickness = 0.8


def shot(name, d, target, ortho):
    d = Vector(d).normalized(); cam.location = Vector(target) + d * 600
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = ortho
    sc.render.filepath = out + name; bpy.ops.render.render(write_still=True)


# --- 1. bagian yang dibuang (merah) pada shell v2, dilihat dari belakang (kamera di sisi -Z)
sh = load(shell_b_f, (0.62, 0.64, 0.68)); rm = load(rem_f, (0.95, 0.12, 0.1))
shot("_dibuang.png", (0.45, -0.75, -1.0), (0, 0, 8), 150)
for o in (sh, rm): bpy.data.objects.remove(o, do_unlink=True)
# --- 2. jig bor di atas shell (jig diproduksi dengan flange di Z=0 -> kembalikan ke bingkai desain: Z -3.5)
sh = load(shell_f, (0.62, 0.64, 0.68))
jA = load(jigA_f, (0.15, 0.4, 0.9), shift=(0, 0, -3.5)); jB = load(jigB_f, (0.1, 0.6, 0.75), shift=(0, 0, -3.5))
shot("_jig.png", (0.45, -0.75, -1.0), (0, 0, 8), 150)
print("done")
