import bpy, sys, math, os
from mathutils import Vector

"""Render pratinjau (luar, dalam, potongan).  python render_previews.py -- <folder_case> [ext] [int] [sec]
   (folder_case berisi ECG_PPG_Cover.blend; hasil ke <folder_case>/preview)"""
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
CASE = args[0]
OUT = os.path.join(CASE, "preview")
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(CASE, "ECG_PPG_Cover.blend"))
import json
S_ = json.load(open(os.path.join(CASE, "_ref", "summary.json")))
YC = sum(S_["outer_y"]) / 2 if "outer_y" in S_ else 0.0           # pusat outline pada sumbu Y (v3: -3.4)
BAT_ON = bool(S_.get("battery"))
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1200, 800
sc.eevee.taa_render_samples = 24
sc.view_settings.view_transform = "Standard"

# dunia abu-abu
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.19, 0.21, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
sc.world = w


def mk_mat(name, color, alpha=1.0, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    return m


for ob in bpy.data.objects:
    ob.data.materials.clear()
shell = bpy.data.objects["Cover_Depan_Shell"]
plate = bpy.data.objects["Cover_Belakang_BackPlate"]
shell.data.materials.append(mk_mat("shell", (0.82, 0.84, 0.88, 1)))
plate.data.materials.append(mk_mat("plate", (0.30, 0.45, 0.65, 1)))
ghost_cols = {"PCB_hijau": (0.05, 0.5, 0.15, 1), "TFT_PCB": (0.75, 0.05, 0.05, 1), "Kaca_touch": (0.02, 0.02, 0.04, 1),
              "Area_aktif": (0.2, 0.55, 1, 1), "Baut_spacer": (0.85, 0.65, 0.15, 1), "microUSB_ESP32": (0.75, 0.75, 0.8, 1),
              "USBC_powerbank": (0.75, 0.75, 0.8, 1), "Plug_jack_AD8232": (0.05, 0.05, 0.05, 1), "Badan_saklar_KCD11": (0.05, 0.05, 0.05, 1), "Sekrup_M3x8": (0.8, 0.8, 0.85, 1),
              "Gland_PG7_+_mur": (0.1, 0.2, 0.9, 1), "Baterai_PALO103450": (0.95, 0.75, 0.1, 1)}
ghosts = [o for o in bpy.data.objects if o.name.startswith("Ref_")]
for g in ghosts:
    g.data.materials.append(mk_mat("g_" + g.name, ghost_cols[g.name[4:]], 1.0, 0.5))


def light(loc, strength):
    l = bpy.data.lights.new("L", "SUN"); l.energy = strength
    o = bpy.data.objects.new("L", l); sc.collection.objects.link(o); o.location = loc
    d = Vector((0, 0, 15)) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


light((-200, 150, 250), 3.5)
light((200, -150, 120), 2.0)
light((0, 0, -250), 1.6)

cam_ob = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam_ob); sc.camera = cam_ob


def view(name, loc, target=(0, 0, 15), ortho=None, show=("shell", "plate"), ghosts_on=False, up="Z", only=None):
    cam_ob.location = Vector(loc)
    d = Vector(target) - cam_ob.location
    cam_ob.rotation_euler = d.to_track_quat("-Z", "Y" if up == "Y" else "Y").to_euler()
    if ortho:
        cam_ob.data.type = "ORTHO"; cam_ob.data.ortho_scale = ortho
    else:
        cam_ob.data.type = "PERSP"; cam_ob.data.lens = 45
    shell.hide_render = "shell" not in show
    plate.hide_render = "plate" not in show
    for g in ghosts:
        g.hide_render = not ghosts_on if only is None else (g.name[4:] not in only)
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("saved", name, flush=True)


which = args[1:] or ["all"]
if "all" in which or "ext" in which:
    view("1_depan_kanan_atas", (-190, 190, 190), (0, 8 + YC, 15))
    view("2_depan_kiri_bawah", (190, -150, 170), (0, -5 + YC, 15))
    view("3_belakang_sayap_sabuk", (-60, -120, -230), (0, YC, 10))
    view("3b_depan_lurus", (0, YC, 400), (0, 5 + YC, 15), ortho=150)
if "all" in which or "int" in which:
    view("4_terbuka_dari_belakang_dgn_komponen", (-70, -110, -200), (0, YC, 15), show=("shell",), ghosts_on=True)
    if BAT_ON:
        view("4b_penyangga_baterai_di_back_plate", (-150, -190, 150), (-5, YC, 3), show=("plate",), only=("PCB_hijau", "Baterai_PALO103450", "Baut_spacer"))


def section(name, axis, val, keep, cam_loc, ortho, target):
    """potong dengan bidang axis=val; keep='lt' menyimpan sisi nilai lebih kecil."""
    mods = []
    big = 400
    for ob in [shell, plate] + ghosts:
        ob.hide_render = False
        if ob.name.startswith("Ref_") and not ("Area" in ob.name):
            pass
        cutter = bpy.data.objects.new("cut", bpy.data.meshes.new("cut"))
        import bmesh
        bm = bmesh.new()
        lo = [-big, -big, -big]; hi = [big, big, big]
        i = {"X": 0, "Y": 1, "Z": 2}[axis]
        if keep == "lt": lo[i] = val
        else: hi[i] = val
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x = hi[0] if v.co.x > 0 else lo[0]
            v.co.y = hi[1] if v.co.y > 0 else lo[1]
            v.co.z = hi[2] if v.co.z > 0 else lo[2]
        bm.to_mesh(cutter.data); bm.free()
        sc.collection.objects.link(cutter)
        md = ob.modifiers.new("sec", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = cutter; md.solver = "MANIFOLD"
        cutter.hide_render = True; cutter.hide_viewport = True
        mods.append((ob, md, cutter))
    cam_ob.location = Vector(cam_loc)
    d = Vector(target) - cam_ob.location
    cam_ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam_ob.data.type = "ORTHO"; cam_ob.data.ortho_scale = ortho
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("saved", name, flush=True)
    for ob, md, cutter in mods:
        ob.modifiers.remove(md)
        bpy.data.objects.remove(cutter, do_unlink=True)


if "all" in which or "sec" in which:
    OR = 115 if BAT_ON else 100
    section("5_potongan_gland_PG7", "Y", -12.195, "lt", (0, 300, 15), 130, (-10, 0, 15))
    section("6_potongan_microUSB_bawah", "X", 28.321, "lt", (300, 0, 15), OR, (0, YC, 15))
    section("7_potongan_saklar_atas", "X", 3.0, "lt", (300, 0, 15), OR, (0, YC, 15))
    section("8_potongan_baut_penutup", "X", 23.0, "lt", (300, 0, 15), OR, (0, YC, 15))
    if BAT_ON:
        section("9_potongan_baterai_X-12", "X", -12.0, "lt", (300, 0, 15), OR, (0, YC, 15))
        section("9b_potongan_baterai_X-37", "X", -37.0, "lt", (300, 0, 15), OR, (0, YC, 15))
