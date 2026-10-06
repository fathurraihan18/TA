"""Model komponen yang dibuat prosedural (lebih realistis daripada kotak perkiraan): cable gland PG7 putih + mur, saklar rocker KCD11.
Koordinat model casing (+X Kiri, +Y Atas, +Z Depan). Ukuran dari summary.json casing (parameter yang sama dengan make_case.py).
"""
import math
import bpy, bmesh
from mathutils import Vector, Matrix
from lib import *


def lathe_x(name, profile, y0, z0, n=96, flute=None, material=None):
    """benda putar terhadap sumbu sejajar X melalui (y0, z0). profile = [(x, r), ...] dari sisi satu ke sisi lain (r>=0).
    flute = (jumlah, kedalaman_fraksi): alur memanjang pada jari-jari (untuk tutup gland)."""
    bm = bmesh.new()
    rings = []
    for (x, r) in profile:
        ring = []
        for k in range(n):
            a = 2 * math.pi * k / n
            rr = r
            if flute and r > 0.01:
                cnt, dep = flute
                rr = r * (1 - dep * 0.5 * (1 + math.cos(cnt * a)))
            ring.append(bm.verts.new((x, y0 + rr * math.cos(a), z0 + rr * math.sin(a))))
        rings.append(ring)
    for ra, rb in zip(rings[:-1], rings[1:]):
        for k in range(n):
            kk = (k + 1) % n
            bm.faces.new([ra[k], ra[kk], rb[kk], rb[k]])
    if profile[0][1] > 0.01: bm.faces.new(rings[0][::-1])
    if profile[-1][1] > 0.01: bm.faces.new(rings[-1])
    ob = mesh_obj(name, bm, material)
    smooth(ob, 40)
    return ob


def hex_prism_x(name, y0, z0, af, x0, x1, material=None, bevel=0.35):
    """prisma segi enam sepanjang X (AF = jarak antarsisi); sudut dipecah dengan bevel agar tidak terlalu tajam."""
    R = af / math.sqrt(3)
    bm = bmesh.new()
    pts = [(y0 + R * math.cos(math.radians(30 + 60 * k)), z0 + R * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
    lo = [bm.verts.new((x0, p, q)) for p, q in pts]
    hi = [bm.verts.new((x1, p, q)) for p, q in pts]
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    for i in range(6):
        j = (i + 1) % 6
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
    ob = mesh_obj(name, bm, material)
    m = ob.modifiers.new("bev", "BEVEL"); m.width = bevel; m.segments = 2; m.limit_method = "ANGLE"
    smooth(ob, 40)
    return ob


def make_gland(S, material_body=None, material_seal=None):
    """Cable gland PG7 (nilon putih): kepala segi enam + tutup bergelombang + ulir + mur + cincin seal. Sumbu = X, keluar ke -X."""
    gl = S["gland"]; HX = S["outer"][0] / 2
    y0, z0 = gl["y"], gl["zc"]
    U = gl["out"]
    gxu = lambda u: -(HX + u)
    W = material_body or mat("gland_putih", (0.93, 0.93, 0.91), 0.42, 0.0, **{"Coat Weight": 0.15})
    K = material_seal or mat("gland_seal", (0.03, 0.03, 0.035), 0.6, 0.0)
    objs = []
    # ulir: silinder dengan alur kecil (cincin) dari muka boss ke dalam rongga
    xt0, xt1 = gxu(U), gxu(U - 8.0)                                   # -57.3 .. -49.3
    prof = [(xt0, 0.0), (xt0, 5.85)]
    for i in range(8):
        xi = xt0 + i * 1.0
        prof += [(xi + 0.1, 6.25), (xi + 0.5, 6.25), (xi + 0.8, 5.85)]
    prof += [(xt1, 5.85), (xt1, 0.0)]
    objs.append(lathe_x("gl_ulir", prof, y0, z0, 48, None, W))
    # mur segi enam di kantong dinding
    objs.append(hex_prism_x("gl_mur", y0, z0, gl["nut_af"] - 0.4, gxu(gl["pocket"] - 3.0), gxu(gl["pocket"] - 3.0 - gl["nut_h"]), W))
    # cincin seal hitam di bawah kepala
    objs.append(lathe_x("gl_seal", [(gxu(U), 0.0), (gxu(U), 7.0), (gxu(U + 0.8), 7.0), (gxu(U + 0.8), 0.0)], y0, z0, 64, None, K))
    # kepala segi enam
    objs.append(hex_prism_x("gl_kepala", y0, z0, 15.0, gxu(U + 0.8), gxu(U + 5.0), W, 0.4))
    # tutup (dome) bergalur: dari kepala ke ujung masuk kabel, lubang kabel di tengah
    xa = gxu(U + 5.0)
    capprof = [(xa, 7.35), (xa - 1.4, 7.4), (xa - 3.5, 7.0), (xa - 6.5, 6.3), (xa - 9.0, 5.6), (xa - 10.6, 4.9), (xa - 11.6, 4.1), (xa - 12.0, 3.2), (xa - 12.0, 2.45)]
    objs.append(lathe_x("gl_tutup", capprof, y0, z0, 120, (14, 0.035), W))
    return objs


def make_saklar(S, tag="sw"):
    """Saklar rocker KCD11 datar: badan hitam di balik dinding, bezel (flens) di muka luar dinding Atas, rocker merah miring."""
    sw = S["switch"]; HY = S["outer_y"][1]
    swc, swz = sw["x"], sw["zc"]
    yin = HY - sw["panel"]
    blk = mat("sw_hitam", (0.025, 0.025, 0.03), 0.4, 0.0)
    red = mat("sw_merah", (0.80, 0.04, 0.03), 0.28, 0.0, **{"Coat Weight": 0.4})
    steel = mat("sw_logam", (0.80, 0.80, 0.82), 0.25, 1.0)
    objs = []

    def box(name, x0, x1, y0, y1, z0, z1, m, bev=0.0):
        bm = bmesh.new()
        vs = [bm.verts.new((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        bmesh.ops.convex_hull(bm, input=vs)
        ob = mesh_obj(name, bm, m)
        if bev > 0:
            md = ob.modifiers.new("bev", "BEVEL"); md.width = bev; md.segments = 3
        smooth(ob, 40)
        return ob
    objs.append(box(f"{tag}_badan", swc - 6.9, swc + 6.9, yin - sw["depth"], HY, swz - 4.5, swz + 4.5, blk, 0.3))
    objs.append(box(f"{tag}_bezel", swc - 7.4, swc + 7.4, HY, HY + 1.5, swz - 5.15, swz + 5.15, blk, 0.45))
    # rocker: profil (z,y) miring, diekstrusi sepanjang X
    bm = bmesh.new()
    prof = [(-4.0, HY + 1.5), (4.0, HY + 1.5), (4.0, HY + 4.6), (-4.0, HY + 2.2)]
    lo = [bm.verts.new((swc - 6.0, y, swz + z)) for z, y in prof]
    hi = [bm.verts.new((swc + 6.0, y, swz + z)) for z, y in prof]
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
    ob = mesh_obj(f"{tag}_rocker", bm, red)
    md = ob.modifiers.new("bev", "BEVEL"); md.width = 0.6; md.segments = 4
    smooth(ob, 40); objs.append(ob)
    # kaki solder
    for k, dx in enumerate((-3.0, 3.0)):
        objs.append(box(f"{tag}_kaki{k}", swc + dx - 0.4, swc + dx + 0.4, yin - sw["depth"] - 5.0, yin - sw["depth"], swz - 2.4, swz + 2.4, steel))
    return objs
