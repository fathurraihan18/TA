"""Torso manusia 3D (mannequin kulit) untuk ilustrasi pemasangan elektroda: loft penampang + bagian anatomi (otot dada, bahu, lengan, tangan, leher, panggul),
digabung dengan voxel remesh lalu dihaluskan. Pasien menghadap -Y (kamera di -Y); +X = sisi KIRI pasien (tampak di KANAN gambar), +Z = atas.
Satuan mm. Pusar di z = 0. Hanya dipakai untuk render ilustrasi (bukan model medis)."""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from scipy.interpolate import PchipInterpolator
from lib import *

# ------------------------------------------------------------- profil penampang torso: z -> (setengah lebar a, setengah kedalaman b, pergeseran y c; + = ke belakang)
PROF = [
    (-480, 124, 82, 8), (-400, 136, 86, 8), (-300, 144, 90, 8), (-170, 150, 94, 8), (-90, 150, 94, 8), (-30, 146, 92, 4), (30, 142, 90, 2), (100, 152, 98, 0),
    (170, 168, 110, -1), (240, 181, 121, -3), (300, 187, 118, -3), (355, 189, 102, 0), (400, 174, 84, 6),
    (440, 122, 70, 12), (468, 72, 62, 14), (520, 60, 58, 18),
]
EXP_SUP = 2.35                                                # eksponen superellipse (sedikit lebih "kotak" daripada elips)


TR = 5.0                                                    # tebal celana (mm) di atas kulit
PROF_TR = [(-250, 162, 92, 8), (-215, 162, 96, 8), (-170, 158, 101, 8), (-130, 157, 101, 8), (-90, 156, 100, 8), (-30, 152, 98, 4), (30, 148, 96, 2)]
LEG = dict(c0=(80.0, 8.0, -215.0), c1=(86.0, 12.0, -540.0), r0=84.0, r1=57.0)          # paha laki-laki: pusat x per sisi, y, z; jari-jari atas dan bawah


def prof_fn_tr():
    z = np.array([p[0] for p in PROF_TR], float)
    return (PchipInterpolator(z, [p[1] for p in PROF_TR]), PchipInterpolator(z, [p[2] for p in PROF_TR]), PchipInterpolator(z, [p[3] for p in PROF_TR]))


def prof_fn():
    z = np.array([p[0] for p in PROF], float)
    return (PchipInterpolator(z, [p[1] for p in PROF]), PchipInterpolator(z, [p[2] for p in PROF]), PchipInterpolator(z, [p[3] for p in PROF]))


def loft_torso(name="torso_loft", z0=-150, z1=520, dz=8, nseg=96, fns=None):
    fa, fb, fc = fns or prof_fn()
    bm = bmesh.new()
    rings = []
    zs = np.arange(z0, z1 + 0.1, dz)
    for z in zs:
        a, b, c = float(fa(z)), float(fb(z)), float(fc(z))
        ring = []
        for k in range(nseg):
            t = 2 * math.pi * k / nseg
            ct, st = math.cos(t), math.sin(t)
            x = a * math.copysign(abs(ct) ** (2 / EXP_SUP), ct)
            y = c + b * math.copysign(abs(st) ** (2 / EXP_SUP), st)
            ring.append(bm.verts.new((x, y, float(z))))
        rings.append(ring)
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(nseg):
            kk = (k + 1) % nseg
            bm.faces.new([r0[k], r0[kk], r1[kk], r1[k]])
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    ob = mesh_obj(name, bm)
    return ob


def ellipsoid(name, c, half, rot_deg=(0, 0, 0), n=32):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=n, v_segments=n // 2, radius=1.0)
    bmesh.ops.scale(bm, verts=bm.verts, vec=half)
    ob = mesh_obj(name, bm)
    ob.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    ob.location = c
    bpy.context.view_layer.update()
    me = ob.data; me.transform(ob.matrix_world); ob.matrix_world = Matrix.Identity(4)
    return ob


def capsule(name, p0, p1, r0, r1, n=24):
    """kerucut terpancung + bola di kedua ujung (diratakan ke satu mesh)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0; L = d.length
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=n, radius1=r0, radius2=r1, depth=L)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, L / 2))
    for r, z in ((r0, 0.0), (r1, L)):
        m2 = bmesh.new()
        bmesh.ops.create_uvsphere(m2, u_segments=n, v_segments=n // 2, radius=r)
        bmesh.ops.translate(m2, verts=m2.verts, vec=(0, 0, z))
        tmp = bpy.data.meshes.new("t"); m2.to_mesh(tmp); m2.free()
        bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    ob = mesh_obj(name, bm)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    ob.rotation_mode = "QUATERNION"; ob.rotation_quaternion = q; ob.location = p0
    bpy.context.view_layer.update()
    me = ob.data; me.transform(ob.matrix_world); ob.matrix_world = Matrix.Identity(4); ob.rotation_mode = "XYZ"
    return ob


HAND_ROT = 25.0                                               # derajat: tangan berputar ke dalam agar punggung tangan terlihat dari depan
WRIST = (264.0, -12.0)


def hand_pt(side, x, y, z):
    """titik pada tangan (bingkai asal, tangan lurus) -> setelah diputar HAND_ROT derajat di sekitar sumbu tegak melalui pergelangan."""
    th = math.radians(-side * HAND_ROT)
    px, py = side * WRIST[0], WRIST[1]
    dx, dy = x - px, y - py
    return (px + dx * math.cos(th) - dy * math.sin(th), py + dx * math.sin(th) + dy * math.cos(th), z)


def build_body(voxel=2.6, smooth_iter=14):
    parts = [loft_torso()]
    # otot dada (pektoralis), bahu (deltoid) dan trapezius
    for s in (-1, 1):
        parts.append(ellipsoid(f"delt{s}", (s * 197, 2, 362), (57, 60, 64), (0, 0, 0)))
        parts.append(ellipsoid(f"trap{s}", (s * 112, 20, 420), (108, 48, 38), (0, s * 20, 0)))
        parts.append(ellipsoid(f"trap2{s}", (s * 60, 22, 452), (60, 42, 34), (0, s * 22, 0)))
        parts.append(ellipsoid(f"lat{s}", (s * 130, 40, 205), (62, 38, 124), (0, 0, s * 7)))
        parts.append(capsule(f"klav_a{s}", (s * 12, -71, 421), (s * 80, -66, 417), 6.5, 6.3))          # klavikula (tonjolan halus)
        parts.append(capsule(f"klav_b{s}", (s * 80, -66, 417), (s * 150, -38, 409), 6.3, 6.0))
        # lengan atas, lengan bawah, tangan (otot: biceps, triceps, brachioradialis; tangan sedikit berputar ke dalam)
        sh = (s * 197, 2, 362); el = (s * 248, 8, 98); wr = (s * 264, -12, -128)
        parts.append(capsule(f"lengan_atas{s}", sh, el, 50, 38))
        parts.append(ellipsoid(f"biceps{s}", (s * 228, -14, 262), (30, 36, 80), (0, 0, s * 6)))
        parts.append(ellipsoid(f"triceps{s}", (s * 234, 22, 250), (30, 30, 84), (0, 0, s * 6)))
        parts.append(capsule(f"lengan_bawah{s}", el, wr, 39, 26))
        parts.append(ellipsoid(f"brakioradialis{s}", (s * 252, -6, 48), (30, 33, 68), (0, 0, s * 3)))
        hp = lambda x, y, z: hand_pt(s, x, y, z)
        parts.append(ellipsoid(f"telapak{s}", hp(s * 266, -16, -166), (17, 40, 50), (0, 0, -s * HAND_ROT)))
        for k, (yo, ln) in enumerate(((-33, 92), (-12, 72), (9, 66), (29, 56))):
            parts.append(capsule(f"jari{s}_{k}", hp(s * 266, yo - 16, -205), hp(s * 266, yo - 16 + (3 if k == 0 else 0), -205 - ln), 9.0, 6.8, 16))
        parts.append(capsule(f"jempol{s}", hp(s * 257, -60, -150), hp(s * 257, -78, -205), 11.0, 7.8, 16))
    # leher
    parts.append(capsule("leher", (0, 16, 466), (0, 20, 560), 57, 53))
    # gabungkan lalu voxel remesh
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = "tubuh"
    me = ob.data
    rm = ob.modifiers.new("remesh", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = voxel; rm.adaptivity = 0.0
    bpy.ops.object.modifier_apply(modifier="remesh")
    sm = ob.modifiers.new("smooth", "SMOOTH"); sm.factor = 0.6; sm.iterations = smooth_iter
    bpy.ops.object.modifier_apply(modifier="smooth")
    sculpt_front(ob)
    for p in ob.data.polygons: p.use_smooth = True
    return ob


def build_trousers(voxel=2.4, smooth_iter=8):
    """celana panjang: pinggang sampai ujung bawah, dua kaki terpisah mulai selangkangan; kain dengan kerutan halus."""
    parts = [loft_torso("celana_loft", z0=-250, z1=-20, dz=6, fns=prof_fn_tr())]
    for s in (-1, 1):
        c0 = (s * LEG["c0"][0], LEG["c0"][1], LEG["c0"][2]); c1 = (s * LEG["c1"][0], LEG["c1"][1], LEG["c1"][2])
        parts.append(capsule(f"kaki{s}", c0, c1, LEG["r0"] + TR, LEG["r1"] + TR, 40))
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = "celana"
    rm = ob.modifiers.new("remesh", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = voxel; rm.adaptivity = 0.0
    bpy.ops.object.modifier_apply(modifier="remesh")
    sm = ob.modifiers.new("smooth", "SMOOTH"); sm.factor = 0.6; sm.iterations = smooth_iter
    bpy.ops.object.modifier_apply(modifier="smooth")
    # kerutan kain: gelombang lunak di sekitar pinggul dan lutut, alur kancing, lipatan depan kaki
    me = ob.data; n = len(me.vertices)
    co = np.zeros(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    nr = np.zeros(n * 3); me.vertices.foreach_get("normal", nr); nr = nr.reshape(-1, 3)
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    front = np.clip((-nr[:, 1] - 0.15) / 0.5, 0, 1)
    d = 1.1 * np.sin(z * 0.075 + x * 0.05) * np.cos(x * 0.045 - z * 0.03 + 0.8)
    d += 0.9 * np.sin(z * 0.19 + np.abs(x) * 0.11 + 1.2) * np.exp(-((z + 330) / 130) ** 2)            # kerutan di lutut
    d += 1.3 * np.exp(-((z + 140) / 70) ** 2) * np.sin(np.hypot(x, y) * 0.09 + z * 0.05)
    for s_ in (-1, 1):
        zz = np.clip((z + 215) / -325.0, 0, 1)
        xc = s_ * (LEG["c0"][0] + (LEG["c1"][0] - LEG["c0"][0]) * zz)
        d -= 1.7 * front * np.exp(-((x - xc) / 2.6) ** 2) * ((z < -230) & (z > -520))                  # lipatan setrika
    d -= 1.4 * front * np.exp(-(x / 2.2) ** 2) * ((z > -190) & (z < -22))                               # alur kancing
    co2 = co + nr * d[:, None]
    me.vertices.foreach_set("co", co2.reshape(-1)); me.update()
    for p_ in ob.data.polygons: p_.use_smooth = True
    return ob


def sculpt_front(ob):
    """relief anatomi halus pada sisi depan (<= 3,5 mm): otot dada, alur tulang dada, linea alba, perut. Mengganti vertex sepanjang normal."""
    me = ob.data
    n = len(me.vertices)
    co = np.zeros(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    nr = np.zeros(n * 3); me.vertices.foreach_get("normal", nr); nr = nr.reshape(-1, 3)
    x, z = co[:, 0], co[:, 2]
    front = np.clip((-nr[:, 1] - 0.25) / 0.5, 0.0, 1.0)                  # hanya sisi depan
    d = np.zeros(n)

    def g(cx, cz, sx, sz, amp):
        return amp * np.exp(-0.5 * (((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2))
    for s_ in (-1, 1):
        d += g(s_ * 86, 262, 62, 44, 5.4 * (1 + 0.05 * s_))               # pektoralis mayor (menonjol; sedikit tidak simetris)
        d += g(s_ * 92, 218, 60, 5.0, -3.2)                               # tepi bawah pektoralis (tegas, tanpa lipatan payudara)
        d += g(s_ * 150, 300, 22, 50, -1.6)                               # alur dada-deltoid
        d += g(s_ * 128, 330, 30, 40, 1.4)                                # tepi pektoralis ke aksila
        for zc in (-5, 45, 95, 145):                                      # blok rektus abdominis (six-pack)
            d += g(s_ * 28, zc + 20, 20, 18, 2.6)
        for zc in (170, 130, 90):                                         # serratus anterior
            d += g(s_ * 135, zc, 11, 6, 1.0)
        d += g(s_ * 150, 90, 14, 70, 1.0)                                 # oblik
    d += g(0, 285, 7, 72, -2.6)                                           # alur tulang dada
    d += g(0, 60, 4, 110, -2.0)                                           # linea alba
    for zc in (15, 65, 115):
        d += g(0, zc, 54, 3.2, -1.5)                                      # alur melintang perut
    d += g(0, 420, 40, 8, -1.2)                                           # takik suprasternal
    d += 0.45 * (np.sin(x * 0.045 + 1.3) * np.cos(z * 0.037 + 0.4) + 0.6 * np.sin(x * 0.11 + z * 0.07))   # undulasi halus: permukaan tidak sempurna
    co2 = co + nr * (1.8 * d * front)[:, None]
    me.vertices.foreach_set("co", co2.reshape(-1))
    me.update()


def surface_point(ob, x, z, origin_y=-1500.0):
    """titik permukaan depan tubuh pada (x, z): ray cast dari -Y; mengembalikan (titik dunia, normal dunia)."""
    deps = bpy.context.evaluated_depsgraph_get()
    ok, loc, nrm, idx = ob.ray_cast(Vector((x, origin_y, z)), Vector((0, 1, 0)))
    if not ok: raise RuntimeError(f"ray cast gagal di x={x}, z={z}")
    return loc, nrm
