"""Perpustakaan Blender (bpy) untuk paket gambar FINAL: scene Cycles realistis, material, pemuat STL, model elektroda EKG + plug 3,5 mm.
Satuan mm. Dipakai oleh render_*.py (import dengan sys.path menunjuk ke folder ini).
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.dirname(HERE)                                   # folder case/

# warna elektroda sesuai kabel pengguna (spidol di konektor: merah=RA, kuning=LA, hijau=RL)
LEAD = {"RA": (0.80, 0.05, 0.04), "LA": (0.95, 0.72, 0.04), "RL": (0.02, 0.38, 0.22)}
LEAD_NAME = {"RA": "merah", "LA": "kuning", "RL": "hijau"}


# ------------------------------------------------------------------ scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MAT.clear()
    return bpy.context.scene


MAT = {}


def mat(name, color, rough=0.5, metal=0.0, **kw):
    key = (name, tuple(round(c, 3) for c in color[:3]), rough, metal, tuple(sorted(kw.items())))
    if key in MAT: return MAT[key]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color[:3], 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for k, v in kw.items():
        if k in b.inputs:
            b.inputs[k].default_value = v
    MAT[key] = m
    return m


def setup_cycles(res=(1600, 1000), samples=96, transparent=False, exposure=0.0, world=(1, 1, 1), world_strength=0.9):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception: pass
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 4
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = exposure
    w = bpy.data.worlds.new("w"); w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*world, 1); bg.inputs[1].default_value = world_strength
    sc.world = w
    return sc


def add_sun(direction, strength, angle_deg=4.0, color=(1, 1, 1)):
    l = bpy.data.lights.new("sun", "SUN"); l.energy = strength; l.angle = math.radians(angle_deg); l.color = color
    o = bpy.data.objects.new("sun", l); bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = Vector(direction).normalized().to_track_quat("-Z", "Y").to_euler()
    return o


def add_area(loc, target, size, energy, color=(1, 1, 1)):
    l = bpy.data.lights.new("area", "AREA"); l.energy = energy; l.size = size; l.color = color
    o = bpy.data.objects.new("area", l); bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def studio_lights(scale=1.0):
    """tiga cahaya: kunci (area besar, dari depan-kanan-atas), pengisi, dan kontur."""
    add_area((260 * scale, -340 * scale, 420 * scale), (0, 0, 0), 320 * scale, 90000 * scale ** 2)
    add_area((-380 * scale, -120 * scale, 260 * scale), (0, 0, 0), 300 * scale, 30000 * scale ** 2)
    add_area((0, 420 * scale, 300 * scale), (0, 0, 0), 300 * scale, 25000 * scale ** 2)


def add_floor(z, size=4000, color=(0.97, 0.97, 0.97), catcher=False, rough=0.9):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    f = bpy.context.active_object; f.name = "lantai"
    if catcher:
        f.is_shadow_catcher = True
    else:
        f.data.materials.append(mat("lantai", color, rough))
    return f


def camera(loc, target, lens=None, ortho=None, up=(0, 0, 1)):
    sc = bpy.context.scene
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    # up-vector eksplisit
    f = d.normalized(); r = f.cross(Vector(up)).normalized(); u = r.cross(f).normalized()
    cam.matrix_world = Matrix(((r.x, u.x, -f.x, loc[0]), (r.y, u.y, -f.y, loc[1]), (r.z, u.z, -f.z, loc[2]), (0, 0, 0, 1)))
    if ortho:
        cam.data.type = "ORTHO"; cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"; cam.data.lens = lens or 50
    cam.data.clip_start, cam.data.clip_end = 1, 20000
    return cam


def render(path):
    sc = bpy.context.scene
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("saved", os.path.basename(path), flush=True)


# ------------------------------------------------------------------ objek bantu
def link(ob, coll=None):
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def smooth(ob, angle=35):
    """shade smooth berdasarkan sudut: sisi datar tetap tegas, lengkung halus."""
    me = ob.data
    for p in me.polygons: p.use_smooth = True
    try:
        bpy.context.view_layer.objects.active = ob
        for o in bpy.context.selected_objects: o.select_set(False)
        ob.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    except Exception as e:
        print("smooth by angle gagal:", e)
    return ob


def mesh_obj(name, bm, material=None):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); link(ob)
    if material: ob.data.materials.append(material)
    return ob


def disc(name, r, h, z0=0.0, material=None, n=64, bevel=0.0, center=(0, 0), seg=1):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n, radius1=r, radius2=r, depth=h)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(center[0], center[1], z0 + h / 2))
    ob = mesh_obj(name, bm, material)
    if bevel > 0:
        m = ob.modifiers.new("bev", "BEVEL"); m.width = bevel; m.segments = 3; m.limit_method = "ANGLE"
    smooth(ob)
    return ob


def sphere(name, r, loc, material=None, sx=1, sy=1, sz=1, n=32):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=n, v_segments=n // 2, radius=r)
    bmesh.ops.scale(bm, verts=bm.verts, vec=(sx, sy, sz))
    bmesh.ops.translate(bm, verts=bm.verts, vec=loc)
    ob = mesh_obj(name, bm, material); smooth(ob)
    return ob


def hull_prism(name, circles, z0, z1, material=None, n=40):
    """prisma dari selubung cembung beberapa lingkaran [(cx, cy, r)], tinggi z0..z1 (bentuk tetesan)."""
    bm = bmesh.new()
    pts = []
    for cx, cy, r in circles:
        for k in range(n):
            a = 2 * math.pi * k / n
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    vs = [bm.verts.new((x, y, z)) for (x, y) in pts for z in (z0, z1)]
    bmesh.ops.convex_hull(bm, input=vs)
    ob = mesh_obj(name, bm, material)
    return ob


def tube(name, pts, r, material, res=10, taper=None):
    """kabel/kawat: kurva Bezier mulus melalui titik `pts`, diberi tebal r, lalu diubah menjadi mesh."""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = r; cu.bevel_resolution = 4; cu.resolution_u = res; cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts) - 1)
    for p, c in zip(sp.bezier_points, pts):
        p.co = c; p.handle_left_type = p.handle_right_type = "AUTO"
    ob = bpy.data.objects.new(name, cu); link(ob)
    ob.data.materials.append(material)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects: o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object
    smooth(ob, 50)
    return ob


def text_obj(name, s, size, loc, rot_z_deg, material, extrude=0.05):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = s; cu.size = size; cu.extrude = extrude
    cu.align_x = "CENTER"; cu.align_y = "CENTER"
    ob = bpy.data.objects.new(name, cu); link(ob); ob.location = loc; ob.rotation_euler = (0, 0, math.radians(rot_z_deg))
    ob.data.materials.append(material)
    return ob


def load_stl(path, material, xform=None, name=None, flat=True):
    bpy.ops.wm.stl_import(filepath=path)
    ob = bpy.context.selected_objects[0]
    for c in list(ob.users_collection): c.objects.unlink(ob)
    link(ob)
    if name: ob.name = name
    if xform is not None: ob.data.transform(xform)
    ob.data.materials.clear(); ob.data.materials.append(material)
    for p in ob.data.polygons: p.use_smooth = False
    if not flat: smooth(ob, 40)
    return ob


# ------------------------------------------------------------------ ELEKTRODA EKG (pad busa + gel biru + snap krom + konektor berwarna)
PAD_D = 45.0                                    # diameter pad (mm), sesuai model Sketchfab yang dirujuk pengguna
PAD_T = 1.2
SNAP_XY = (9.5, 6.5)                            # posisi snap terhadap pusat pad (di model Sketchfab snap bergeser dari pusat)


def mat_pad(): return mat("pad_busa", (0.93, 0.93, 0.91), 0.85, 0.0)
def mat_gel(): return mat("gel", (0.45, 0.78, 0.98), 0.12, 0.0, **{"Specular IOR Level": 0.6})
def mat_chrome(): return mat("krom", (0.82, 0.83, 0.86), 0.13, 1.0)
def mat_satin(): return mat("krom_satin", (0.80, 0.80, 0.82), 0.5, 0.35)
def mat_wire(): return mat("kawat_abu", (0.52, 0.52, 0.53), 0.55, 0.0)
def mat_black(): return mat("hitam", (0.02, 0.02, 0.025), 0.4, 0.0)


def electrode(label=None, loc=(0, 0, 0), rot_z=0.0, tail_deg=35.0, with_lead=True, tag="e", with_pad=True):
    """Satu elektroda sekali pakai. Koordinat lokal: pusat pad di (0,0), sisi kulit z = 0, +Z ke atas (arah snap).
    label: 'RA' | 'LA' | 'RL' -> konektor berwarna merah / kuning / hijau (teks spidol seperti pada kabel pengguna); None = tanpa konektor.
    tail_deg: arah ekor konektor (derajat dari +X lokal). Mengembalikan (daftar objek, titik keluar kawat lokal)."""
    objs = []
    if with_pad:
        objs.append(disc(f"{tag}_pad", PAD_D / 2, PAD_T, 0.0, mat_pad(), 96, bevel=0.35))
        z = PAD_T
        objs.append(disc(f"{tag}_gel1", 17.0, 0.25, z, mat_gel(), 80, center=(-1.5, -2.0)))
        objs.append(disc(f"{tag}_gel2", 9.5, 0.22, z, mat_gel(), 64, center=SNAP_XY))
        z += 0.25
    else:
        z = PAD_T + 0.25
    sx, sy = SNAP_XY
    objs.append(disc(f"{tag}_snap_flens", 4.9, 0.7, z, mat_satin(), 40, bevel=0.25, center=(sx, sy)))
    objs.append(disc(f"{tag}_snap_leher", 1.9, 1.5, z + 0.7, mat_chrome(), 32, center=(sx, sy)))
    objs.append(sphere(f"{tag}_snap_kepala", 2.6, (sx, sy, z + 0.7 + 1.5 + 0.9), mat_chrome(), 1, 1, 0.92))
    out = None
    if with_lead and label:
        col = LEAD[label]
        zc = z + 0.9                                           # dasar konektor di atas flens snap
        a = math.radians(tail_deg); ex, ey = math.cos(a), math.sin(a)
        body = hull_prism(f"{tag}_konektor", [(sx, sy, 6.1), (sx + ex * 12.0, sy + ey * 12.0, 3.1)], zc, zc + 6.4, mat(f"lead_{label}", col, 0.32, 0.0, **{"Coat Weight": 0.35}))
        m = body.modifiers.new("bev", "BEVEL"); m.width = 1.0; m.segments = 3
        smooth(body, 40); objs.append(body)
        # relief tarik beralur (5 rusuk) searah ekor
        axis_z = zc + 3.2
        for i in range(5):
            d0 = 12.0 + i * 1.7
            ob = tube(f"{tag}_rusuk{i}", [(sx + ex * d0, sy + ey * d0, axis_z), (sx + ex * (d0 + 1.0), sy + ey * (d0 + 1.0), axis_z)], 2.7 - 0.07 * i, mat(f"lead_{label}", col, 0.32, 0.0, **{"Coat Weight": 0.35}))
            objs.append(ob)
        # teks spidol hitam di atas konektor
        objs.append(text_obj(f"{tag}_teks", label, 3.0, (sx + ex * 1.2, sy + ey * 1.2, zc + 6.4 + 0.02), tail_deg + 180.0 if False else tail_deg, mat_black(), 0.04))
        out = (sx + ex * (12.0 + 5 * 1.7), sy + ey * (12.0 + 5 * 1.7), axis_z)
    # induk: semua objek dikelompokkan di Empty supaya mudah dipindah
    em = bpy.data.objects.new(f"{tag}_grup", None); link(em)
    for o in objs: o.parent = em
    em.location = loc; em.rotation_euler = (0, 0, math.radians(rot_z))
    return em, objs, out


def trs_plug(loc=(0, 0, 0), tag="plug", length_barrel=14.0):
    """Plug TRS 3,5 mm. Sumbu +Y; ujung barel di y=0 (masuk ke jack), badan hitam mulai y=length_barrel. Mengembalikan (grup, titik akhir kabel lokal)."""
    objs = []
    # barel logam + dua cincin isolator
    def cyl_y(name, r, y0, y1, material, n=40):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n, radius1=r, radius2=r, depth=(y1 - y0))
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(-90), 3, "X"))
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0, (y0 + y1) / 2, 0))
        ob = mesh_obj(name, bm, material); smooth(ob); return ob
    objs.append(cyl_y(f"{tag}_barel", 1.75, 0.0, length_barrel, mat_chrome()))
    for i, y in enumerate((5.0, 8.4)):
        objs.append(cyl_y(f"{tag}_cincin{i}", 1.78, y, y + 1.2, mat_black()))
    objs.append(cyl_y(f"{tag}_badan", 3.25, length_barrel, length_barrel + 10.3, mat_black()))
    # relief tarik meruncing
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=40, radius1=3.25, radius2=1.9, depth=11.0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(-90), 3, "X"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, length_barrel + 10.3 + 5.5, 0))
    ob = mesh_obj(f"{tag}_boot", bm, mat_black()); smooth(ob); objs.append(ob)
    em = bpy.data.objects.new(f"{tag}_grup", None); link(em)
    for o in objs: o.parent = em
    em.location = loc
    return em, objs, (0.0, length_barrel + 10.3 + 11.0, 0.0)


# ------------------------------------------------------------------ material per nama bagian (komponen dari perakitan/asm)
def pick_material(group, name):
    """(rgb, rough, metal, extra) untuk bagian STL hasil ekspor perakitan (v2d_penahan_strip/_ref/asm)."""
    n = name.lower()
    W = (0.93, 0.93, 0.91)
    if group == "gland":
        if "thread" in n: return W, 0.5, 0.0, {}
        return W, 0.45, 0.0, {"Coat Weight": 0.15}
    if group == "saklar":
        if "rocker" in n: return (0.80, 0.04, 0.03), 0.3, 0.0, {"Coat Weight": 0.3}
        if n in ("sw_t1", "sw_t2"): return (0.80, 0.80, 0.82), 0.25, 1.0, {}
        return (0.025, 0.025, 0.03), 0.4, 0.0, {}
    if group == "tft":
        if "glass" in n: return (0.005, 0.006, 0.01), 0.06, 0.0, {"Coat Weight": 0.8}
        if "pcb" in n: return (0.50, 0.02, 0.03), 0.35, 0.0, {"Coat Weight": 0.5}
        if "hdr" in n: return (0.02, 0.02, 0.025), 0.4, 0.0, {}
        return (0.80, 0.80, 0.82), 0.25, 1.0, {}
    if group == "boost":
        if "pcb" in n: return (0.04, 0.14, 0.55), 0.35, 0.0, {"Coat Weight": 0.5}
        if "usbc" in n: return (0.80, 0.80, 0.82), 0.25, 1.0, {}
        return (0.02, 0.02, 0.025), 0.4, 0.0, {}
    if group == "baterai":
        if n == "bat": return (0.86, 0.62, 0.08), 0.35, 0.0, {"Coat Weight": 0.3}
        if "label" in n: return (0.85, 0.86, 0.88), 0.5, 0.0, {}
        if "tape" in n: return (0.90, 0.75, 0.05), 0.5, 0.0, {}
        if "wire0" in n: return (0.75, 0.04, 0.03), 0.5, 0.0, {}
        if "wire1" in n: return (0.02, 0.02, 0.025), 0.5, 0.0, {}
        return W, 0.5, 0.0, {}
    if group == "pcb":
        if n == "pcb": return (0.02, 0.28, 0.09), 0.38, 0.0, {"Coat Weight": 0.5}
        if "jst" in n: return W, 0.5, 0.0, {}
        return (0.02, 0.02, 0.025), 0.4, 0.0, {}
    if group == "standoff":
        return (0.85, 0.66, 0.22), 0.3, 1.0, {}
    if group == "sekrup":
        return (0.78, 0.78, 0.80), 0.3, 1.0, {}
    return (0.5, 0.5, 0.5), 0.5, 0.0, {}


def screen_quad(x0, x1, y0, y1, z, image, name="layar", strength=1.0):
    """bidang layar TFT dengan gambar (emisi) - mengganti 'tft_layar' yang tidak diekspor ke STL."""
    bm = bmesh.new()
    v = [bm.verts.new((x0, y0, z)), bm.verts.new((x1, y0, z)), bm.verts.new((x1, y1, z)), bm.verts.new((x0, y1, z))]
    f = bm.faces.new(v)
    uv = bm.loops.layers.uv.new("UV")
    for lp, (u, w_) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        lp[uv].uv = (u, w_)
    ob = mesh_obj(name, bm)
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        if n_.type != "OUTPUT_MATERIAL": nt.nodes.remove(n_)
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(image)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = strength
    nt.links.new(t.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    ob.data.materials.append(m)
    return ob
