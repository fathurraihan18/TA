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
    (-480, 128, 84, 8), (-400, 142, 88, 8), (-300, 156, 94, 8), (-170, 170, 100, 8), (-90, 172, 100, 8), (-30, 158, 96, 4), (30, 146, 94, 2), (100, 150, 99, 0),
    (170, 160, 108, -1), (240, 171, 118, -3), (300, 177, 116, -3), (355, 182, 102, 0), (400, 170, 84, 6),
    (440, 120, 70, 12), (468, 70, 62, 14), (520, 58, 58, 18),
]
EXP_SUP = 2.35                                                # eksponen superellipse (sedikit lebih "kotak" daripada elips)


def prof_fn():
    z = np.array([p[0] for p in PROF], float)
    return (PchipInterpolator(z, [p[1] for p in PROF]), PchipInterpolator(z, [p[2] for p in PROF]), PchipInterpolator(z, [p[3] for p in PROF]))


def loft_torso(name="torso_loft", z0=-480, z1=520, dz=8, nseg=96):
    fa, fb, fc = prof_fn()
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


def build_body(voxel=2.6, smooth_iter=14):
    parts = [loft_torso()]
    # otot dada (pektoralis), bahu (deltoid) dan trapezius
    for s in (-1, 1):
        parts.append(ellipsoid(f"delt{s}", (s * 190, 2, 366), (52, 56, 60), (0, 0, 0)))
        parts.append(ellipsoid(f"trap{s}", (s * 112, 20, 420), (108, 48, 38), (0, s * 20, 0)))
        parts.append(ellipsoid(f"trap2{s}", (s * 60, 22, 452), (60, 42, 34), (0, s * 22, 0)))
        parts.append(ellipsoid(f"lat{s}", (s * 122, 40, 215), (60, 38, 118), (0, 0, s * 6)))
        parts.append(capsule(f"klav_a{s}", (s * 12, -71, 421), (s * 80, -66, 417), 6.5, 6.3))          # klavikula (tonjolan halus)
        parts.append(capsule(f"klav_b{s}", (s * 80, -66, 417), (s * 150, -38, 409), 6.3, 6.0))
        # lengan atas, lengan bawah, tangan
        sh = (s * 190, 2, 366); el = (s * 244, 8, 98); wr = (s * 262, -12, -128)
        parts.append(capsule(f"lengan_atas{s}", sh, el, 48, 36))
        parts.append(capsule(f"lengan_bawah{s}", el, wr, 36, 25))
        parts.append(ellipsoid(f"telapak{s}", (s * 266, -16, -166), (19, 42, 52), (0, 0, 0)))
        for k, (yo, ln) in enumerate(((-33, 92), (-12, 72), (9, 66), (29, 56))):
            parts.append(capsule(f"jari{s}_{k}", (s * 266, yo - 16, -205), (s * 266, yo - 16 + (3 if k == 0 else 0), -205 - ln), 9.4, 7.2, 16))
        parts.append(capsule(f"jempol{s}", (s * 257, -60, -150), (s * 257, -78, -205), 11.5, 8.2, 16))
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
        d += g(s_ * 90, 272, 58, 40, 3.2)                                 # otot dada
        d += g(s_ * 92, 230, 52, 5.5, -1.6)                               # tepi bawah otot dada
        d += g(s_ * 150, 300, 22, 50, -1.1)                               # alur dada-deltoid
        for zc in (-5, 45, 95, 145):                                      # blok rektus abdominis
            d += g(s_ * 27, zc + 20, 19, 17, 1.5)
        d += g(s_ * 150, 90, 14, 70, 0.8)                                 # oblik
    d += g(0, 285, 7, 72, -1.9)                                           # alur tulang dada
    d += g(0, 60, 4, 105, -1.5)                                           # linea alba
    for zc in (15, 65, 115):
        d += g(0, zc, 50, 3.0, -0.9)                                      # alur melintang perut
    co2 = co + nr * (1.7 * d * front)[:, None]
    me.vertices.foreach_set("co", co2.reshape(-1))
    me.update()


def surface_point(ob, x, z, origin_y=-1500.0):
    """titik permukaan depan tubuh pada (x, z): ray cast dari -Y; mengembalikan (titik dunia, normal dunia)."""
    deps = bpy.context.evaluated_depsgraph_get()
    ok, loc, nrm, idx = ob.ray_cast(Vector((x, origin_y, z)), Vector((0, 1, 0)))
    if not ok: raise RuntimeError(f"ray cast gagal di x={x}, z={z}")
    return loc, nrm
