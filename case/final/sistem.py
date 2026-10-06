"""Bangun scene SISTEM LENGKAP di Blender: cover v2 final (v2d) + semua komponen nyata + klip PPG + elektroda 3 lead (merah RA, kuning LA, hijau RL).
Dipanggil dari render_sistem.py. Koordinat model: +X = Kiri perangkat, +Y = Atas, +Z = Depan (layar); Z = 0 ujung ekor baut; plate bawah z = -3.5.
"""
import sys, os, json, math, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import numpy as np

REF = os.path.join(CASE, "v2d_penahan_strip", "_ref")
ASM = os.path.join(REF, "asm")
KOMP = os.path.join(CASE, "komponen")
KLIPREF = os.path.join(CASE, "sensor_ppg", "klip_v2", "_ref")
S = json.load(open(os.path.join(REF, "summary.json")))
KS = json.load(open(os.path.join(KLIPREF, "summary.json")))
TABLE_Z = S["z"]["plate_bottom"]                      # -3.5: permukaan meja saat perangkat rebah (layar menghadap atas)
G = {}                                                # nama grup -> dict(empty, objs)


def group(name, objs, children=None):
    """kelompokkan objs di bawah satu Empty (agar bisa digeser). children: objek yang di-parent-kan (bawaan = objs);
    dipakai bila objs sudah punya induk dengan transformasi sendiri (mis. elektroda)."""
    em = bpy.data.objects.new("G_" + name, None); link(em)
    for o in (children if children is not None else objs): o.parent = em
    G[name] = dict(empty=em, objs=objs)
    return em


def petg(rough=0.42):
    return mat("petg_putih", (0.90, 0.90, 0.88), rough, 0.0, **{"Coat Weight": 0.12})


def asm_files(prefix, skip=()):
    out = []
    for f in sorted(glob.glob(os.path.join(ASM, prefix + "__*.stl"))):
        nm = os.path.basename(f)[:-4].split("__")[1]
        if nm in skip: continue
        out.append((f, nm))
    return out


def load_group(prefix, group_for_mat, skip=(), flat=True, colorfn=None, xform=None):
    objs = []
    for f, nm in asm_files(prefix, skip):
        col, rg, mt, ex = (colorfn or pick_material)(group_for_mat, nm)
        objs.append(load_stl(f, mat("c_" + nm, col, rg, mt, **ex), xform=xform, name=nm, flat=flat))
    return objs


def esp_color(group_, nm):
    pj = json.load(open(os.path.join(KOMP, "esp32", "esp32_parts.json")))
    k = nm[4:] if nm.startswith("esp_") else nm
    v = pj.get(k)
    col = tuple(v["color"][:3]) if v else (0.02, 0.02, 0.025)
    metal = 1.0 if k in ("pin", "perisai", "usb", "strip") else 0.0
    rough = {"pin": 0.28, "perisai": 0.3, "usb": 0.3, "strip": 0.35}.get(k, 0.45)
    if k == "pin": col = (0.90, 0.72, 0.30)
    if k == "perisai": col = (0.80, 0.80, 0.82)
    if k == "usb": col = (0.80, 0.80, 0.82)
    if k == "usb_slot": col = (0.02, 0.02, 0.025)
    return col, rough, metal, ({"Coat Weight": 0.4} if k in ("pcb", "modul_pcb") else {})


def ad_color(group_, nm):
    n = nm.lower()
    if "pcb" in n: return (0.62, 0.03, 0.05), 0.35, 0.0, {"Coat Weight": 0.5}
    if "dark" in n: return (0.03, 0.03, 0.035), 0.4, 0.0, {}
    return (0.78, 0.78, 0.80), 0.3, 1.0, {}


def hw_color(k):
    pj = json.load(open(os.path.join(KOMP, "hw605", "hw605_parts.json")))
    col = pj[k]["color"][:3]
    return col, {"pad": 0.3, "pcb": 0.4, "jendela": 0.12}.get(k, 0.45), (1.0 if k == "pad" else 0.0), ({"Coat Weight": 0.3} if k == "pcb" else {})


def build(table=True, clip_xy=(-100.0, -32.0), tilt=0.0, penahan=True, elektroda=True, white_clip=True, layout="foto"):
    """Bangun semua grup. table=True: klip, kabel, dan elektroda rebah di meja (z = TABLE_Z)."""
    G.clear()
    W = petg()
    # ---------------- cover
    shell = load_stl(os.path.join(REF, "shell_design.stl"), W, name="shell", flat=False); group("shell", [shell])
    plate = load_stl(os.path.join(REF, "plate_design.stl"), W, name="plate", flat=False); group("plate", [plate])
    if penahan:
        pen = load_stl(os.path.join(REF, "penahan_design.stl"), mat("penahan", (0.70, 0.74, 0.80), 0.45, 0.0), name="penahan", flat=False); group("penahan", [pen])
    group("sekrup", load_group("sekrup", "sekrup"))
    # ---------------- tumpukan elektronik
    tft = load_group("tft", "tft")
    tft.append(screen_quad(-0.5 - 36.72, -0.5 + 36.72, -24.48, 24.48, S["z"]["glass_front"] + 0.03, os.path.join(HERE, "layar_ui.png"), strength=0.9))
    group("tft", tft)
    group("standoff", load_group("standoff", "standoff", colorfn=lambda g, n: ((0.80, 0.80, 0.82), 0.3, 1.0, {}) if "nut" in n else ((0.85, 0.66, 0.22), 0.3, 1.0, {})))
    group("pcb", load_group("pcb", "pcb"))
    group("esp32", load_group("esp32", "esp32", colorfn=esp_color))
    group("ad8232", load_group("ad8232", "ad8232", colorfn=ad_color))
    group("boost", load_group("boost", "boost"))
    bat = load_group("baterai", "baterai")
    group("baterai", bat)
    # ---------------- saklar dan gland
    import parts
    group("saklar", parts.make_saklar(S))
    group("gland", parts.make_gland(S))
    # ---------------- kabel PPG di dalam (konektor + PCB kecil + kabel menembus gland)
    wh = mat("kabel_putih", (0.92, 0.92, 0.90), 0.5, 0.0)
    inside = []
    for nm in ("ppg_pcb", "ppg_conn"):
        f = os.path.join(ASM, f"ppg__{nm}.stl")
        col, rg, mt, ex = ((0.04, 0.14, 0.55), 0.35, 0.0, {"Coat Weight": 0.5}) if nm == "ppg_pcb" else ((0.92, 0.92, 0.90), 0.5, 0.0, {})
        inside.append(load_stl(f, mat("c_" + nm, col, rg, mt, **ex), name=nm))
    for nm in ("ppg_cable1", "ppg_cable2"):
        inside.append(load_stl(os.path.join(ASM, f"ppg__{nm}.stl"), wh, name=nm, flat=False))
    group("kabel_ppg_dalam", inside)
    # ---------------- klip jari PPG (A, B, C + modul HW-605 + pegas + sekrup), dikerjakan di bingkai asm lalu diturunkan ke meja
    clip = []
    for k_, col in (("A", (0.93, 0.93, 0.91)), ("B", (0.93, 0.93, 0.91)), ("C", (0.93, 0.93, 0.91))):
        clip.append(load_stl(os.path.join(ASM, f"ppg__clip_{k_}.stl"), mat("klip_" + k_, col if white_clip else {"A": (0.66, 0.68, 0.72), "B": (0.74, 0.70, 0.60), "C": (0.12, 0.30, 0.72)}[k_], 0.45, 0.0, **{"Coat Weight": 0.1}), name="clip_" + k_, flat=False))
    for k_ in ("pcb", "pad", "sensor", "jendela", "ic", "smd"):
        col, rg, mt, ex = hw_color(k_)
        clip.append(load_stl(os.path.join(ASM, f"ppg__clip_hw605_{k_}.stl"), mat("hw_" + k_, col, rg, mt, **ex), name="hw_" + k_))
    clip.append(load_stl(os.path.join(ASM, "ppg__clip_pegas.stl"), mat("pegas", (0.72, 0.74, 0.77), 0.25, 1.0), name="pegas"))
    clip.append(load_stl(os.path.join(ASM, "ppg__clip_sekrup.stl"), mat("sekrup_klip", (0.06, 0.06, 0.07), 0.35, 0.6), name="sekrup_klip"))
    group("klip", clip)
    # posisi klip: di bingkai asm klip menggantung (z min 14,7); pindahkan ke meja
    cx0, cy0 = clip_xy
    dz = (TABLE_Z - 14.7) if table else 0.0
    sx_, sy_ = cx0 - (-100.0), cy0 - (-32.0)                     # geser terhadap posisi asm (leher kabel di x=-100, y=-32)
    G["klip"]["base"] = (sx_, sy_, dz)
    # ---------------- kabel PPG luar: dari gland ke leher klip
    gx_exit = (-75.0, S["gland"]["y"], S["gland"]["zc"])
    neck = (-100.0 + sx_, -34.2 + sy_, 19.2 + dz)
    pts = [gx_exit, (-86.0 + sx_ * 0.4, -13.0 + sy_ * 0.15, 12.0 + dz * 0.3), (-95.0 + sx_ * 0.9, -18.0 + sy_ * 0.5, 17.0 + dz * 0.8), (-100.0 + sx_, -26.0 + sy_, 19.2 + dz), neck] if table else [gx_exit, (-86, -14, 14), (-100.0, -18.2, 19.2), neck]
    kab = tube("kabel_ppg_luar", pts, 2.0, wh, 14)
    group("kabel_ppg_luar", [kab])
    # ---------------- elektroda + kabel + plug
    if elektroda:
        build_elektroda(table, layout)
    # ---------------- baterai (miring opsional)
    return G


def build_elektroda(table, layout):
    jx, jz = S["jack"]["x"], S["jack"]["zc"]
    plug, plug_objs, plug_end = trs_plug(loc=(jx, 29.7 - 14.0, jz), tag="plug")
    group("plug", plug_objs, children=[plug])
    cable_m = mat_wire()
    zt = TABLE_Z + 1.9 if table else 0.0                   # sumbu kabel di meja
    J = (52.0, 104.0)
    P = {"RA": (98.0, 152.0), "RL": (162.0, 112.0), "LA": (118.0, 46.0)}
    z_pad = TABLE_Z if table else 0.0
    # kabel utama dari plug ke titik sambung
    p0 = (jx, 29.7 + 10.3 + 11.0, jz)
    pts = [p0, (jx, 66.0, jz - 1.0), (jx + 8.0, 82.0, (jz - 10.0) if table else jz - 4.0), (jx + 30.0, 96.0, zt + 0.2), (J[0], J[1], zt)]
    main = tube("kabel_utama", pts, 1.9, cable_m, 14)
    sleeve = None
    ang_main = math.atan2(J[1] - 98.0, J[0] - (jx + 8.0))
    # selongsong sambungan (kecil) di J
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=2.6, radius2=2.6, depth=16.0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    sleeve = mesh_obj("sambungan", bm, mat("selongsong", (0.15, 0.15, 0.17), 0.5)); smooth(sleeve)
    sleeve.location = (J[0] + 3.0, J[1] + 1.0, zt); sleeve.rotation_euler = (0, 0, math.atan2(J[1] - 96.0, J[0] - (jx + 30.0)))
    elec, wires = [], []
    for lb in ("RA", "RL", "LA"):
        px, py = P[lb]
        to_j = math.degrees(math.atan2(J[1] - py, J[0] - px))
        rot = to_j - 35.0
        em, objs, out = electrode(lb, loc=(px, py, z_pad), rot_z=rot, tail_deg=35.0, tag=lb.lower())
        # titik keluar kawat (dunia)
        R = Matrix.Rotation(math.radians(rot), 3, "Z")
        ow = Vector(R @ Vector(out)) + Vector((px, py, z_pad))
        mid = ((ow.x + J[0]) / 2, (ow.y + J[1]) / 2, zt)
        perp = Vector((-(J[1] - ow.y), J[0] - ow.x, 0)).normalized() * (7.0 if lb != "RL" else -7.0)
        pw = [tuple(ow), (ow.x + (J[0] - ow.x) * 0.3 + perp.x * 0.6, ow.y + (J[1] - ow.y) * 0.3 + perp.y * 0.6, zt), (mid[0] + perp.x, mid[1] + perp.y, zt), (J[0] + (ow.x - J[0]) * 0.22, J[1] + (ow.y - J[1]) * 0.22, zt), (J[0] + 6.0, J[1] + 2.0, zt)]
        w = tube(f"kawat_{lb}", pw, 0.85, cable_m, 14)
        wires.append(w)
        elec.append((lb, em, objs))
    group("elektroda", sum([o for _, _, o in elec], []) + wires + [main, sleeve], children=[em for _, em, _ in elec] + wires + [main, sleeve])
    G["elektroda"]["parents"] = [em for _, em, _ in elec]
    return G


def set_offsets(offs):
    """offs: {grup: (dx,dy,dz)}; grup tanpa offset kembali ke posisi dasar."""
    for k, g in G.items():
        base = Vector(g.get("base", (0, 0, 0)))
        g["empty"].location = base + Vector(offs.get(k, (0, 0, 0)))
    bpy.context.view_layer.update()


def hide(keys, state=True):
    for k in keys:
        if k not in G: continue
        for o in G[k]["objs"]:
            o.hide_render = state; o.hide_viewport = state
        if k == "elektroda":
            for e in G[k].get("parents", []): e.hide_render = state


def bbox(keys=None):
    pts = []
    for k, g in G.items():
        if keys and k not in keys: continue
        for o in g["objs"]:
            if o.hide_render: continue
            mw = o.matrix_world
            for c in o.bound_box:
                pts.append(mw @ Vector(c))
    a = np.array([[p.x, p.y, p.z] for p in pts])
    return a.min(0), a.max(0)
