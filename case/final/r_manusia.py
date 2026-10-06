"""Render adegan manusia (Cycles): torso + elektroda RA/LA/RL (menempel mengikuti kontur kulit) + kabel + perangkat di sabuk + klip PPG di jari.
python r_manusia.py -- <out_png> [samples] [lebar] [tinggi]
Keluaran juga <out_png>.json: koordinat proyeksi piksel (RA, LA, RL, perangkat, klip, z-level untuk fade).
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
from manusia import *
import sistem

A = sys.argv[sys.argv.index("--") + 1:]
OUTP = A[0]
SAMP = int(A[1]) if len(A) > 1 else 48
RW = int(A[2]) if len(A) > 2 else 1500
RH = int(A[3]) if len(A) > 3 else 2100
VOX = float(os.environ.get("VOX", "2.6"))

reset()
sc = setup_cycles((RW, RH), SAMP, transparent=True, world_strength=0.55)
# cahaya: kunci besar dari kiri-atas-depan, pengisi lembut dari kanan, kontur dari belakang-atas
add_area((1000, -1900, 1500), (0, 0, 120), 1400, 6.5e6)
add_area((-1500, -1500, 400), (0, 0, 100), 1800, 1.6e6)
add_area((0, 1200, 1400), (0, 0, 200), 900, 1.2e6)

# ----------------------------------------------------------------- tubuh
body = build_body(voxel=VOX, smooth_iter=12)
skin = mat("kulit", (0.86, 0.68, 0.57), 0.48, 0.0, **{"Subsurface Weight": 0.22, "Subsurface Scale": 3.0, "Specular IOR Level": 0.35})
# bump halus (pori / ketidakteraturan kulit)
nt = skin.node_tree
b = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexNoise"); tex.inputs["Scale"].default_value = 0.35; tex.inputs["Detail"].default_value = 8
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08; bump.inputs["Distance"].default_value = 1.0
nt.links.new(tex.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
body.data.materials.append(skin)

deps = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(body, deps)


def surf(origin, direction):
    loc, nrm, idx, dist = bvh.ray_cast(Vector(origin), Vector(direction))
    return (loc, nrm) if loc is not None else (None, None)


def skin_at(x, z):
    loc, n = surf((x, -1800.0, z), (0, 1, 0))
    if loc is None: raise RuntimeError(f"permukaan tidak ditemukan di x={x} z={z}")
    n = n.normalized()
    if n.y > 0: n = -n
    return loc, n


def frame(p, n, up=(0, 0, 1)):
    """kerangka singgung: u searah +X dunia (disingkirkan komponen n), v = n x u."""
    u = (Vector((1, 0, 0)) - n * n.x).normalized()
    v = n.cross(u).normalized()
    return u, v


# tanda anatomi: puting dan pusar (cakram gelap tipis mengikuti kulit)
dark = mat("areola", (0.66, 0.44, 0.38), 0.6, 0.0)


def decal(name, x, z, r, sy=1.0, thick=0.5, material=dark):
    p, n = skin_at(x, z)
    u, v = frame(p, n)
    bm = bmesh.new(); nseg = 40
    top = [bm.verts.new(tuple(p + u * (r * math.cos(2 * math.pi * k / nseg)) + v * (r * sy * math.sin(2 * math.pi * k / nseg)) + n * thick)) for k in range(nseg)]
    bm.faces.new(top)
    ob = mesh_obj(name, bm, material)
    return ob


decal("puting_r", -92, 268, 9.0); decal("puting_l", 92, 268, 9.0)
decal("pusar", 0, 0, 5.5, 1.5, 0.3)

# ----------------------------------------------------------------- sabuk (pita melingkar di sekitar pinggang)
fa, fb, fc = prof_fn()
bm = bmesh.new()
zlev = [-66, -56, -46, -36, -26, -18]
ro, ri = [], []
nseg = 120
for z in zlev:
    a_, b_, c_ = float(fa(z)), float(fb(z)), float(fc(z))
    r_out, r_in = [], []
    for k in range(nseg):
        t = 2 * math.pi * k / nseg; ct, st = math.cos(t), math.sin(t)
        xo = (a_ + 4.5) * math.copysign(abs(ct) ** (2 / EXP_SUP), ct); yo = c_ + (b_ + 4.5) * math.copysign(abs(st) ** (2 / EXP_SUP), st)
        xi_ = (a_ + 0.2) * math.copysign(abs(ct) ** (2 / EXP_SUP), ct); yi_ = c_ + (b_ + 0.2) * math.copysign(abs(st) ** (2 / EXP_SUP), st)
        r_out.append(bm.verts.new((xo, yo, z))); r_in.append(bm.verts.new((xi_, yi_, z)))
    ro.append(r_out); ri.append(r_in)
for R_ in (ro, ri):
    for r0, r1 in zip(R_[:-1], R_[1:]):
        for k in range(nseg):
            kk = (k + 1) % nseg
            bm.faces.new([r0[k], r0[kk], r1[kk], r1[k]])
for k in range(nseg):
    kk = (k + 1) % nseg
    bm.faces.new([ro[0][k], ri[0][k], ri[0][kk], ro[0][kk]])
    bm.faces.new([ro[-1][k], ro[-1][kk], ri[-1][kk], ri[-1][k]])
belt = mesh_obj("sabuk", bm, mat("kulit_sabuk", (0.07, 0.04, 0.03), 0.45, 0.0, **{"Coat Weight": 0.2}))
smooth(belt, 40)
bpy.context.view_layer.update()

# ----------------------------------------------------------------- perangkat di sabuk (sisi kanan pasien = kiri gambar)
sistem.build(table=False, elektroda=False)
DEVK = [k for k in sistem.G if k not in ("klip", "kabel_ppg_luar")]
xd, zd = -62.0, -42.0
pd, nd = skin_at(xd, zd)
yv = (Vector((0, 0, 1)) - nd * nd.z).normalized()
xv = yv.cross(nd).normalized()
Rm = Matrix(((xv.x, yv.x, nd.x), (xv.y, yv.y, nd.y), (xv.z, yv.z, nd.z)))
t_dev = pd + nd * 4.7 - Rm @ Vector((0, 0, -3.5))                 # sisi belakang plate (z = -3,5) di atas sabuk
DEV = bpy.data.objects.new("PERANGKAT", None); bpy.context.scene.collection.objects.link(DEV)
DEV.matrix_world = Matrix.Translation(t_dev) @ Rm.to_4x4()
for k in DEVK:
    sistem.G[k]["empty"].parent = DEV
bpy.context.view_layer.update()
dev_centre = DEV.matrix_world @ Vector((0, 0, 14))
jack_local = Vector((sistem.S["jack"]["x"], 31.75, sistem.S["jack"]["zc"]))
jack_world = DEV.matrix_world @ jack_local

# ----------------------------------------------------------------- elektroda yang menempel pada kulit
PADR = PAD_D / 2


def conform_disc(name, p, n, u, v, cxy, rad, t_lo, t_hi, material, rings=12, nseg=64):
    """cakram solid yang mengikuti permukaan kulit: titik pada bidang singgung diproyeksikan ke kulit, lalu digeser t_lo/t_hi sepanjang n."""
    bm = bmesh.new()

    def pt(r, k):
        a = 2 * math.pi * k / nseg
        q = p + u * (cxy[0] + r * math.cos(a)) + v * (cxy[1] + r * math.sin(a))
        loc, nn = surf(q + n * 60.0, -n)
        if loc is None: loc = q
        return loc
    grid = []
    for ri_ in range(1, rings + 1):
        r = rad * ri_ / rings
        grid.append([pt(r, k) for k in range(nseg)])
    ctr = pt(0.0, 0)
    top = [[bm.verts.new(tuple(g + n * t_hi)) for g in ring] for ring in grid]
    bot = [[bm.verts.new(tuple(g + n * t_lo)) for g in ring] for ring in grid]
    tc = bm.verts.new(tuple(ctr + n * t_hi)); bc = bm.verts.new(tuple(ctr + n * t_lo))
    for k in range(nseg):
        kk = (k + 1) % nseg
        bm.faces.new([tc, top[0][k], top[0][kk]])
        bm.faces.new([bc, bot[0][kk], bot[0][k]])
    for ri_ in range(rings - 1):
        for k in range(nseg):
            kk = (k + 1) % nseg
            bm.faces.new([top[ri_][k], top[ri_ + 1][k], top[ri_ + 1][kk], top[ri_][kk]])
            bm.faces.new([bot[ri_][k], bot[ri_][kk], bot[ri_ + 1][kk], bot[ri_ + 1][k]])
    for k in range(nseg):
        kk = (k + 1) % nseg
        bm.faces.new([bot[-1][k], bot[-1][kk], top[-1][kk], top[-1][k]])
    ob = mesh_obj(name, bm, material)
    smooth(ob, 60)
    return ob


JUNC = (0.0, 150.0)                                          # titik sambung kabel (x, z) di tulang dada bagian bawah
EL = {"RA": (-108.0, 350.0), "LA": (108.0, 350.0), "RL": (-120.0, 78.0)}
el_world = {}
wires = []
for lb, (ex, ez) in EL.items():
    p, n = skin_at(ex, ez)
    u, v = frame(p, n)
    conform_disc(f"{lb}_pad", p, n, u, v, (0, 0), PADR, 0.15, 0.15 + PAD_T, mat_pad(), 14, 80)
    conform_disc(f"{lb}_gel1", p, n, u, v, (-1.5, -2.0), 17.0, 0.15 + PAD_T - 0.02, 0.15 + PAD_T + 0.22, mat_gel(), 10, 64)
    conform_disc(f"{lb}_gel2", p, n, u, v, SNAP_XY, 9.5, 0.15 + PAD_T - 0.02, 0.15 + PAD_T + 0.20, mat_gel(), 6, 48)
    # arah ekor konektor: menuju titik sambung di bidang singgung
    jp, jn = skin_at(*JUNC)
    d = jp - p
    ang_t = math.degrees(math.atan2(d.dot(v), d.dot(u)))
    roll = ang_t - 35.0
    em, objs, out = electrode(lb, loc=(0, 0, 0), rot_z=0.0, tail_deg=35.0, tag=lb.lower() + "_k", with_pad=False)
    cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
    ur = u * cr + v * sr
    vr = n.cross(ur).normalized()
    Mw = Matrix(((ur.x, vr.x, n.x, p.x), (ur.y, vr.y, n.y, p.y), (ur.z, vr.z, n.z, p.z), (0, 0, 0, 1)))
    em.matrix_world = Mw
    bpy.context.view_layer.update()
    exit_w = Mw @ Vector(out)
    el_world[lb] = dict(p=p, n=n, exit=exit_w, em=em)

# kawat dari tiap konektor ke titik sambung
wire_m = mat_wire()


def skin_path(xz_pts, off):
    out = []
    for (x, z) in xz_pts:
        p, n = skin_at(x, z)
        out.append(tuple(p + n * off))
    return out


jx0, jz0 = JUNC
for lb in ("RA", "LA", "RL"):
    e = el_world[lb]; ex, ez = EL[lb]
    sx = (jx0 - ex); sz = (jz0 - ez)
    # lintasan tidak lurus: sedikit melengkung
    nrm = np.array([-sz, sx]) / math.hypot(sx, sz)
    bend = {"RA": 26.0, "LA": -26.0, "RL": -16.0}[lb]
    xzs = []
    for t_ in (0.10, 0.32, 0.60, 0.85, 1.0):
        bb = bend * math.sin(math.pi * t_)
        xzs.append((ex + sx * t_ + nrm[0] * bb, ez + sz * t_ + nrm[1] * bb))
    sk = [skin_at(x_, z_) for (x_, z_) in xzs]
    offs = [3.4, 2.0, 1.2, 1.0, 1.0]
    pts = [tuple(e["exit"])] + [tuple(pp + nn * o_) for (pp, nn), o_ in zip(sk, offs)]
    wires.append(tube(f"kawat_{lb}", pts, 0.85, wire_m, 14))
# selongsong sambungan
jp, jn = skin_at(jx0, jz0)
sl = disc("sambungan", 2.8, 16.0, 0.0, mat("selongsong", (0.15, 0.15, 0.17), 0.5), 24)
# kabel utama: dari titik sambung ke colokan (plug) di sisi Atas perangkat
plug_dir = DEV.matrix_world.to_3x3() @ Vector((0, 1, 0))             # arah +Y_model = ke atas tubuh
plug_p0 = DEV.matrix_world @ Vector((sistem.S["jack"]["x"], 29.7, sistem.S["jack"]["zc"]))
plug_g, plug_objs, plug_end_l = trs_plug(loc=(0, 0, 0), tag="plug")
# plug: sumbu +Y lokal; ujung barel masuk ke jack -> letakkan agar badan mulai di y=29.7 (barel 14 mm di dalam jack)
Mplug = DEV.matrix_world @ Matrix.Translation((sistem.S["jack"]["x"], 29.7 - 14.0, sistem.S["jack"]["zc"]))
plug_g.matrix_world = Mplug
bpy.context.view_layer.update()
plug_exit = Mplug @ Vector(plug_end_l)
mid = []
for t_ in (0.2, 0.5, 0.8, 1.0):
    pass
main_pts = [tuple(plug_exit)]
# turun-naik mengikuti kulit dari plug ke titik sambung
px_, pz_ = plug_exit.x, plug_exit.z
for t_ in (0.2, 0.45, 0.7, 0.9, 1.0):
    x_ = px_ + (jx0 - px_) * t_ + 14.0 * math.sin(math.pi * t_)
    z_ = pz_ + (jz0 - pz_) * t_
    main_pts.append(None)
    main_pts[-1] = (x_, z_)
mp3 = [main_pts[0]] + skin_path([q for q in main_pts[1:]], 2.1)
main = tube("kabel_utama", mp3, 1.9, wire_m, 16)

# ----------------------------------------------------------------- klip PPG pada jari telunjuk tangan KANAN pasien (kiri gambar)
G = sistem.G
tip_asm = Vector((-100.0, -65.99, 28.15))                      # ujung jari referensi pada klip (bingkai asm)
neck_asm = Vector((-100.0, -34.2, 19.2))
M3 = Matrix(((0, 0, -1), (1, 0, 0), (0, -1, 0)))               # X_a -> +y, Y_a -> -z (arah jari ke bawah), Z_a -> -x (rahang atas di sisi lateral)
tip_scene = Vector((-266.0, -47.0, -303.8))
M_clip = Matrix.Translation(tip_scene) @ M3.to_4x4() @ Matrix.Translation(-tip_asm)
G["klip"]["empty"].matrix_world = M_clip
neck_w = M_clip @ neck_asm
gl_exit = DEV.matrix_world @ Vector((-75.0, sistem.S["gland"]["y"], sistem.S["gland"]["zc"]))
kb = [tuple(gl_exit), tuple(gl_exit + Vector((-18, -4, -4))), (-175.0, gl_exit.y - 6, -88.0), (-205.0, -20.0, -170.0), (-222.0, -2.0, -265.0),
      (neck_w.x + 34.0, neck_w.y + 10.0, neck_w.z - 52.0), (neck_w.x + 10.0, neck_w.y + 4.0, neck_w.z - 26.0), tuple(neck_w)]
kab = tube("kabel_ppg_luar", kb, 2.0, mat("kabel_putih", (0.92, 0.92, 0.90), 0.5, 0.0), 16)
for o in G["kabel_ppg_luar"]["objs"]:
    o.hide_render = True                                         # kabel luar bawaan (bingkai meja) diganti lintasan di atas

# ----------------------------------------------------------------- kamera
_cd = float(os.environ.get("CAMD", "3600")); _ct = [float(v) for v in os.environ.get("CAMT", "0,80").split(",")]
cam = camera((_ct[0], -_cd, _ct[1]), (_ct[0], 0, _ct[1]), lens=120)
bpy.context.view_layer.update()
render(OUTP)

# koordinat proyeksi untuk label
def proj(p):
    co = world_to_camera_view(sc, cam, Vector(p))
    return [co.x * RW, (1.0 - co.y) * RH]


info = dict(size=[RW, RH], RA=proj(el_world["RA"]["p"]), LA=proj(el_world["LA"]["p"]), RL=proj(el_world["RL"]["p"]),
            device=proj(dev_centre), junction=proj(jp), clip=proj(M_clip @ Vector((-100.0, -66.0, 28.0))), plug=proj(plug_exit), z_levels={str(z): proj((0, -100, z))[1] for z in (560, 520, 480, 100, -300, -380, -400, -430, -450)})
json.dump(info, open(OUTP + ".json", "w"), indent=1)
print(json.dumps(info))
