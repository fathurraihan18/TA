"""Model modul MAX30102 HW-605 (PCB hitam 18,0 x 13,5 x 1,6 mm) dari foto dan datasheet: bukan model resmi, perkiraan komponen.
python make_hw605.py -- <folder_keluar>
Koordinat lokal: pusat PCB di (0,0), PCB z 0..1,6; panjang 13,5 sepanjang X (arah jari), lebar 18,0 sepanjang Y; baris 4 pad di tepi +X."""
import sys, os, json, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sensor_ppg"))
from bl_helpers import *            # noqa
from bl_helpers import _select_only

out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)
L, Wd, T = 13.5, 18.0, 1.6
pcb = box("pcb", -L / 2, L / 2, -Wd / 2, Wd / 2, 0, T)
# 4 lubang tembus di baris pad (-X tepi) dan 4 takik setengah lingkaran di tepi +X (pad solder kawat)
for yy in (-3.81, -1.27, 1.27, 3.81):
    cut_all(pcb, [cyl("lubang", -L / 2 + 1.3, yy, 0.55, -0.1, T + 0.1, "Z", n=24)])
    cut_all(pcb, [cyl("takik", L / 2, yy, 0.9, -0.1, T + 0.1, "Z", n=24)])
for sgn in (-1, 1):                       # 2 slot pelindung di sisi
    cut_all(pcb, [prism("slot", [(sgn * (Wd / 2 - 1.3) + dy, dx) for dx, dy in ((-2.2, -0.45), (-2.2, 0.45), (2.2, 0.45), (2.2, -0.45))], -0.1, T + 0.1, "Z")]) if False else None
parts = {"pcb": (pcb, [0.02, 0.02, 0.025])}
pads = box("pads", 0, 0.01, 0, 0.01, 0, 0.01)
for yy in (-3.81, -1.27, 1.27, 3.81):
    union_all(pads, [cyl("p1", L / 2 - 0.2, yy, 1.15, T, T + 0.06, "Z", n=24), cyl("p2", -L / 2 + 1.3, yy, 0.95, T, T + 0.06, "Z", n=24)])
parts["pad"] = (pads, [0.85, 0.7, 0.3])
sens = box("sensor", -2.8, 2.8, -1.65, 1.65, T, T + 1.55)
parts["sensor"] = (sens, [0.12, 0.12, 0.14])
win = box("window", -1.2, 1.2, -0.9, 0.9, T + 1.55, T + 1.6)
parts["jendela"] = (win, [0.35, 0.45, 0.6])
chips = box("u1", -L / 2 + 2.0 - 1.5, -L / 2 + 2.0 + 1.5, 4.8 - 0.85, 4.8 + 0.85, T, T + 1.1)
union_all(chips, [box("u2", -L / 2 + 2.0 - 1.5, -L / 2 + 2.0 + 1.5, 6.9 - 0.85, 6.9 + 0.85, T, T + 1.1)])
union_all(chips, [box("q", 2.8, 4.6, -6.6, -4.9, T, T + 1.0)])
parts["ic"] = (chips, [0.05, 0.05, 0.06])
smd = box("s0", 2.2, 3.0, 3.0, 4.2, T, T + 0.5)
for (x, y, dx, dy) in ((2.2, 5.6, 0.8, 1.2), (2.2, 7.0, 0.8, 1.2), (-0.8, -6.8, 1.2, 0.8), (0.8, -6.8, 1.2, 0.8), (3.3, 2.0, 1.2, 0.8), (-3.6, -2.5, 1.2, 0.8), (-3.6, 2.5, 1.2, 0.8), (-0.5, 5.6, 0.8, 1.2), (4.7, 5.0, 0.8, 1.2)):
    union_all(smd, [box("s", x - dx / 2, x + dx / 2, y - dy / 2, y + dy / 2, T, T + 0.5)])
parts["smd"] = (smd, [0.62, 0.55, 0.42])


def export_stl(ob, path):
    tmp = ob.copy(); tmp.data = ob.data.copy(); bpy.context.scene.collection.objects.link(tmp)
    _select_only(tmp)
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, global_scale=1.0, apply_modifiers=True)
    bpy.data.objects.remove(tmp, do_unlink=True)


info = {}
for k, (ob, col) in parts.items():
    p = os.path.join(out, f"hw605_{k}.stl")
    export_stl(ob, p)
    info[k] = dict(file=os.path.basename(p), color=col)
json.dump(info, open(os.path.join(out, "hw605_parts.json"), "w"), indent=1)
print("OK")
