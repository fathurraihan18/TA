"""Render peletakan penahan: plate v2 + 3 penahan berwarna beda (1 magenta, 2 oranye, 3 cyan).
python render_penahan_label.py -- <plate.stl> <p1.stl> <p2.stl> <p3.stl> <keluaran.png>
"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
plate_f, p1, p2, p3, out = a
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x = 1600; sc.render.resolution_y = 1000
sc.render.film_transparent = True; sc.render.image_settings.color_mode = "RGBA"
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.45; sc.world = w
for d, e in (((-0.3, 0.4, 0.9), 1.5), ((0.5, -0.4, 0.6), 0.6), ((0.3, 0.2, -0.9), 1.0)):
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


def load(f, col):
    bpy.ops.wm.stl_import(filepath=f); o = bpy.context.selected_objects[0]
    m = bpy.data.materials.new("m"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 0.5
    o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = False


load(plate_f, (0.55, 0.60, 0.72)); load(p1, (0.92, 0.10, 0.55)); load(p2, (0.98, 0.55, 0.08)); load(p3, (0.10, 0.70, 0.85))
d = Vector((0.0, -0.45, 1.0)).normalized(); cam.location = Vector((0, 0, 0)) + d * 700
cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
cam.data.ortho_scale = 170
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
print("done")
