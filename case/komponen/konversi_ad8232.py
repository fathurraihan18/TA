"""Konversi model AD8232 (Thingiverse thing:5330841 oleh jaggz, remake model GrabCAD) dari .blend ke STL per material (mm).
python konversi_ad8232.py -- <file.blend> <folder_keluar>
Lisensi model asli: lihat LICENSE.txt dari arsip Thingiverse (dipakai sebagai referensi gambar)."""
import bpy, sys, os, json
a = sys.argv[sys.argv.index("--") + 1:]
src, out = a[0], a[1]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=src)
ob = bpy.data.objects["ECG Ad8232"]
me = ob.data
cols = []
for i, m in enumerate(me.materials):
    c = tuple(m.diffuse_color)
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                c = tuple(n.inputs["Base Color"].default_value)
    cols.append(dict(name=m.name, color=[round(v, 3) for v in c]))
info = {}
for idx, m in enumerate(me.materials):
    tmp = ob.copy(); tmp.data = ob.data.copy(); bpy.context.scene.collection.objects.link(tmp)
    bpy.context.view_layer.objects.active = tmp
    for o in bpy.context.scene.objects: o.select_set(False)
    tmp.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
    for p in tmp.data.polygons: p.select = (p.material_index != idx)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="FACE"); bpy.ops.object.mode_set(mode="OBJECT")
    tmp.data.transform(__import__("mathutils").Matrix.Scale(1000.0, 4))     # meter -> mm
    path = os.path.join(out, f"ad8232_{idx}_{m.name.replace(' ', '_').replace('.', '_')}.stl")
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, global_scale=1.0)
    vs = [tmp.matrix_world @ v.co for v in tmp.data.vertices]
    info[path] = dict(color=cols[idx]["color"], name=m.name, bounds=[[round(min(v[i] for v in vs), 2) for i in range(3)], [round(max(v[i] for v in vs), 2) for i in range(3)]])
    bpy.data.objects.remove(tmp, do_unlink=True)
# pin dipendekkan (3,8 mm di bawah PCB) agar muat di soket 3,8 mm pada PCB utama
import trimesh
for pth in info:
    m = trimesh.load(pth)
    if m.bounds[0][2] < -5.4:
        m.slice_plane([0, 0, -5.4], [0, 0, 1], cap=True).export(pth)
json.dump(info, open(os.path.join(out, "ad8232_parts.json"), "w"), indent=1)
print(json.dumps(info, indent=1))
