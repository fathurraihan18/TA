"""Render realistis (Cycles) satu komponen: iso, atas, depan, samping. Keluaran: <out>/<nama>_<view>.png + <nama>_info.json
python r_komponen.py -- <nama> <out_dir> [samples]
nama: esp32 | ad8232 | hw605 | elektroda | gland | saklar | tft | powerbank | baterai | pcb
Tampak orto: atas = +X kanan, +Y atas; depan = kamera di -Y menatap +Y (X kanan, Z atas); samping = kamera di +X menatap -X (Y kiri, Z atas).
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import numpy as np

A = sys.argv[sys.argv.index("--") + 1:]
NAME, OUT = A[0], A[1]
SAMPLES = int(A[2]) if len(A) > 2 else 96
VIEWS = os.environ.get("VIEWS", "iso,top,front,side").split(",")
os.makedirs(OUT, exist_ok=True)
KOMP = os.path.join(CASE, "komponen")
ASM = os.path.join(CASE, "v2d_penahan_strip", "_ref", "asm")


def parts_spec():
    """kembalikan [(path_stl, nama, rgb, rough, metal, extra_dict)]"""
    P = []
    if NAME == "esp32":
        pj = json.load(open(os.path.join(KOMP, "esp32", "esp32_parts.json")))
        for k, v in pj.items():
            metal = 1.0 if k in ("pin", "perisai", "usb", "strip") else 0.0
            rough = {"pin": 0.28, "perisai": 0.3, "usb": 0.3, "strip": 0.35}.get(k, 0.45)
            col = v["color"][:3]
            if k == "pin": col = (0.90, 0.72, 0.30)
            if k == "perisai": col = (0.80, 0.80, 0.82)
            extra = {"Coat Weight": 0.4} if k in ("pcb", "modul_pcb") else {}
            P.append((os.path.join(KOMP, "esp32", v["file"]), k, col, rough, metal, extra))
    elif NAME == "ad8232":
        pj = json.load(open(os.path.join(KOMP, "ad8232", "ad8232_parts.json")))
        for pth, v in pj.items():
            nm = v["name"]
            if nm == "PCB Re1": col, rg, mt, ex = (0.62, 0.03, 0.05), 0.35, 0.0, {"Coat Weight": 0.5}
            elif nm.startswith("Dark"): col, rg, mt, ex = (0.03, 0.03, 0.035), 0.4, 0.0, {}
            else: col, rg, mt, ex = (0.78, 0.78, 0.80), 0.3, 1.0, {}
            P.append((os.path.join(KOMP, "ad8232", os.path.basename(pth)), nm, col, rg, mt, ex))
    elif NAME == "hw605":
        pj = json.load(open(os.path.join(KOMP, "hw605", "hw605_parts.json")))
        for k, v in pj.items():
            col = v["color"][:3]; mt = 1.0 if k == "pad" else 0.0
            rg = {"pad": 0.3, "pcb": 0.4, "jendela": 0.12}.get(k, 0.45)
            ex = {"Coat Weight": 0.3} if k in ("pcb",) else {}
            P.append((os.path.join(KOMP, "hw605", v["file"]), k, col, rg, mt, ex))
    elif NAME in ("gland", "saklar"):
        pass
    elif NAME in ("tft", "powerbank", "baterai", "pcb"):
        pref = {"gland": "gland", "saklar": "saklar", "tft": "tft", "powerbank": "boost", "baterai": "baterai", "pcb": "pcb"}[NAME]
        for f in sorted(os.listdir(ASM)):
            if f.startswith(pref + "__") and f.endswith(".stl"):
                P.append((os.path.join(ASM, f), f[:-4].split("__")[1], None, None, None, {}))
    return P


def pref_of(n): return {"powerbank": "boost"}.get(n, n)


ex_objs = []
reset()
sc = setup_cycles((1400, 1000), SAMPLES, transparent=True, world_strength=0.85)
studio_lights(0.25)

if NAME in ("gland", "saklar"):
    import parts
    Sm = json.load(open(os.path.join(CASE, "v2d_penahan_strip", "_ref", "summary.json")))
    (parts.make_gland if NAME == "gland" else parts.make_saklar)(Sm)
elif NAME == "elektroda":
    e0, o0, _ = electrode(None, loc=(-30, 0, 0), tag="p0")
    e1, o1, _ = electrode("RA", loc=(30, 0, 0), tag="p1")
    ex_objs = o0 + o1
else:
    for (path, nm, col, rg, mt, ex) in parts_spec():
        if col is None:
            col, rg, mt, ex = pick_material(pref_of(NAME), nm)
        load_stl(path, mat("c_" + nm, col, rg, mt, **ex), name=nm, flat=True)

if NAME == "tft":
    screen_quad(-0.5 - 36.72, -0.5 + 36.72, -24.48, 24.48, 31.2 + 0.03, os.path.join(HERE, "layar_ui.png"))
objs = [o for o in bpy.data.objects if o.type == "MESH"]
allv = np.array([(o.matrix_world @ v.co)[:] for o in objs for v in o.data.vertices])
lo, hi = allv.min(0), allv.max(0)
cen = (lo + hi) / 2
size = float((hi - lo).max())
floor = add_floor(lo[2] - 0.02, catcher=True)

info = dict(bbox_min=lo.tolist(), bbox_max=hi.tolist(), center=cen.tolist())
spec = {"iso": ((1, -1.15, 0.95), (0, 0, 1)), "top": ((0, 0, 1), (0, 1, 0)), "front": ((0, -1, 0), (0, 0, 1)), "side": ((1, 0, 0), (0, 0, 1))}
PX = 1400
for v in VIEWS:
    d, up = spec[v]
    d = Vector(d).normalized(); f = -d
    right = f.cross(Vector(up)).normalized(); u = right.cross(f).normalized()
    rel = allv - cen
    dr, du = rel @ np.array(right), rel @ np.array(u)
    rmid, umid = (dr.max() + dr.min()) / 2, (du.max() + du.min()) / 2
    ortho = float(os.environ.get("ORTHO", max(dr.max() - dr.min(), du.max() - du.min()) * 1.16))
    target = Vector(cen) + right * rmid + u * umid
    sc.render.resolution_x = sc.render.resolution_y = PX
    cam = camera(tuple(target + d * 1500), tuple(target), ortho=ortho, up=up)
    floor.hide_render = (v != "iso")
    render(os.path.join(OUT, f"{NAME}_{v}.png"))
    info[v] = dict(ortho=ortho, px=[PX, PX], target=list(target), right=list(right), up=list(u))
    bpy.data.objects.remove(cam, do_unlink=True)
json.dump(info, open(os.path.join(OUT, f"{NAME}_info.json"), "w"), indent=1)
