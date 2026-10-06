"""Ekspor gland PG7 dan saklar KCD11 parametrik (parts.py) ke STL per bagian untuk gambar potongan. python export_parts.py -- <folder_keluaran>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import parts
OUT = sys.argv[sys.argv.index("--") + 1]
os.makedirs(OUT, exist_ok=True)
S = json.load(open(os.path.join(CASE, "v2d_penahan_strip", "_ref", "summary.json")))
reset()
objs = parts.make_gland(S) + parts.make_saklar(S)
deps = bpy.context.evaluated_depsgraph_get()
for o in objs:
    ev = o.evaluated_get(deps)
    me = bpy.data.meshes.new_from_object(ev)
    t = bpy.data.objects.new("t", me); bpy.context.scene.collection.objects.link(t)
    for x in bpy.context.selected_objects: x.select_set(False)
    t.select_set(True); bpy.context.view_layer.objects.active = t
    bpy.ops.wm.stl_export(filepath=os.path.join(OUT, o.name + ".stl"), export_selected_objects=True)
    print("ekspor", o.name)
