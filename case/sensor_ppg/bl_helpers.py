"""Helper bpy untuk generator klip sensor PPG (disalin dari make_case.py, tanpa parameter rumah)."""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

# ============================================================ HELPER BLENDER ==
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 0.001
scene.unit_settings.length_unit = "MILLIMETERS"
COL_MAIN = bpy.data.collections.new("Klip")
COL_GHOST = bpy.data.collections.new("Referensi_Komponen")
scene.collection.children.link(COL_MAIN)
scene.collection.children.link(COL_GHOST)


def _obj(name, bm, coll):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _map(axis, p, q, a):
    if axis == "Z": return (p, q, a)
    if axis == "Y": return (p, a, q)
    if axis == "X": return (a, p, q)


def prism(name, pts, a0, a1, axis="Z", coll=None):
    """poligon (p,q) di-ekstrusi sepanjang `axis` dari a0 ke a1."""
    coll = coll or COL_MAIN
    bm = bmesh.new()
    lo = [bm.verts.new(_map(axis, p, q, a0)) for p, q in pts]
    hi = [bm.verts.new(_map(axis, p, q, a1)) for p, q in pts]
    n = len(pts)
    bm.faces.new(lo)
    bm.faces.new(hi[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return _obj(name, bm, coll)


def loft(name, rings, coll=None):
    """rings = [(pts, z), ...] dengan jumlah titik sama; menghasilkan benda tertutup (untuk chamfer)."""
    coll = coll or COL_MAIN
    bm = bmesh.new()
    vr = [[bm.verts.new((p, q, z)) for p, q in pts] for pts, z in rings]
    n = len(rings[0][0])
    bm.faces.new(vr[0])
    bm.faces.new(vr[-1][::-1])
    for a, b in zip(vr[:-1], vr[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([a[i], a[j], b[j], b[i]])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return _obj(name, bm, coll)


def rrect(cx, cy, hx, hy, r, n=12):
    r = min(r, hx, hy)
    if r <= 1e-6:
        return [(cx + hx, cy + hy), (cx - hx, cy + hy), (cx - hx, cy - hy), (cx + hx, cy - hy)]
    pts = []
    for (sx, sy, a0) in [(1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)]:
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((cx + sx * (hx - r) + r * math.cos(a), cy + sy * (hy - r) + r * math.sin(a)))
    return pts


def circle(cx, cy, r, n=64):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def hexagon(cx, cy, af, corners_on_q=True):
    R = af / math.sqrt(3)
    off = 90 if corners_on_q else 0
    return [(cx + R * math.cos(math.radians(off + 60 * k)), cy + R * math.sin(math.radians(off + 60 * k))) for k in range(6)]


def box(name, x0, x1, y0, y1, z0, z1, coll=None):
    return prism(name, [(x1, y1), (x0, y1), (x0, y0), (x1, y0)], z0, z1, "Z", coll)


def cyl(name, c1, c2, r, a0, a1, axis, n=64, coll=None):
    """silinder sumbu `axis`; (c1,c2) = koordinat dua sumbu lain ( Z:(x,y)  Y:(x,z)  X:(y,z) )."""
    return prism(name, circle(c1, c2, r, n), a0, a1, axis, coll)


def frustum(name, cx, cy, r0, r1, z0, z1, n=48):
    bm = bmesh.new()
    lo = [bm.verts.new((cx + r0 * math.cos(2 * math.pi * k / n), cy + r0 * math.sin(2 * math.pi * k / n), z0)) for k in range(n)]
    hi = [bm.verts.new((cx + r1 * math.cos(2 * math.pi * k / n), cy + r1 * math.sin(2 * math.pi * k / n), z1)) for k in range(n)]
    bm.faces.new(lo)
    bm.faces.new(hi[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
    return _obj(name, bm, COL_MAIN)


def _select_only(ob):
    for o in list(bpy.context.scene.objects):
        if o is not None:
            o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)


def bop(target, cutter, op="DIFFERENCE"):
    mod = target.modifiers.new("b", "BOOLEAN")
    mod.operation = op
    mod.object = cutter
    mod.solver = "MANIFOLD"
    _select_only(target)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return target


def union_all(target, parts):
    for p in parts:
        bop(target, p, "UNION")


def cut_all(target, parts):
    for p in parts:
        bop(target, p, "DIFFERENCE")




def loft_x(name, rings, coll=None):
    """rings = [(x, [(y, z), ...]), ...]; jumlah titik sama; benda tertutup dengan bidang ring tegak lurus sumbu X."""
    coll = coll or COL_MAIN
    bm = bmesh.new()
    vr = [[bm.verts.new((x, y, z)) for y, z in pts] for x, pts in rings]
    n = len(rings[0][1])
    bm.faces.new(vr[0][::-1])
    bm.faces.new(vr[-1])
    for a_, b_ in zip(vr[:-1], vr[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([a_[j], a_[i], b_[i], b_[j]])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return _obj(name, bm, coll)
