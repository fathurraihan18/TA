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
sc = setup_cycles((RW, RH), SAMP, transparent=True, world_strength=0.42)
# cahaya: kunci hangat dan agak sempit dari kiri-atas-depan (membentuk otot dada dan perut), pengisi dingin lemah dari kanan, kontur dari belakang-atas
add_area((-1250, -2000, 1700), (0, 0, 150), 950, 1.25e7, color=(1.0, 0.93, 0.84))
add_area((1700, -1500, 300), (0, 0, 100), 1800, 1.6e6, color=(0.86, 0.91, 1.0))
add_area((0, 1300, 1500), (0, 0, 200), 900, 1.6e6)

# ----------------------------------------------------------------- tubuh
body = build_body(voxel=VOX, smooth_iter=12)
def make_skin():
    """kulit: variasi warna skala besar (kemerahan di bahu dan dada atas), noise kekasaran, bump pori halus, subsurface scattering."""
    m = bpy.data.materials.new("kulit"); m.use_nodes = True
    nt = m.node_tree; nd = nt.nodes; lk = nt.links
    b = nd["Principled BSDF"]
    tc = nd.new("ShaderNodeTexCoord")
    n1 = nd.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 0.006; n1.inputs["Detail"].default_value = 3
    n2 = nd.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 0.035; n2.inputs["Detail"].default_value = 6
    cr = nd.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.74, 0.52, 0.42, 1); cr.color_ramp.elements[1].color = (0.86, 0.66, 0.55, 1)
    cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[1].position = 0.65
    lk.new(tc.outputs["Object"], n1.inputs["Vector"]); lk.new(tc.outputs["Object"], n2.inputs["Vector"])
    mx = nd.new("ShaderNodeMath"); mx.operation = "ADD"; mx.inputs[1].default_value = 0.0
    mix = nd.new("ShaderNodeMixRGB"); mix.blend_type = "MIX"; mix.inputs[0].default_value = 0.22
    lk.new(n1.outputs["Fac"], cr.inputs["Fac"])
    lk.new(cr.outputs["Color"], mix.inputs[1])
    mix.inputs[2].default_value = (0.82, 0.58, 0.48, 1)
    lk.new(n2.outputs["Fac"], mix.inputs[0])
    # kemerahan: gradien tinggi (bahu, dada atas lebih merah) dan sisi samping sedikit lebih gelap
    sep = nd.new("ShaderNodeSeparateXYZ"); lk.new(tc.outputs["Object"], sep.inputs["Vector"])
    mr = nd.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 230; mr.inputs["From Max"].default_value = 470
    mr.inputs["To Min"].default_value = 0.0; mr.inputs["To Max"].default_value = 0.30
    lk.new(sep.outputs["Z"], mr.inputs["Value"])
    red = nd.new("ShaderNodeMixRGB"); red.blend_type = "MIX"
    lk.new(mr.outputs["Result"], red.inputs[0]); lk.new(mix.outputs["Color"], red.inputs[1]); red.inputs[2].default_value = (0.80, 0.46, 0.40, 1)
    lk.new(red.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.46
    rg = nd.new("ShaderNodeMapRange"); rg.inputs["To Min"].default_value = 0.38; rg.inputs["To Max"].default_value = 0.58
    lk.new(n2.outputs["Fac"], rg.inputs["Value"]); lk.new(rg.outputs["Result"], b.inputs["Roughness"])
    b.inputs["Subsurface Weight"].default_value = 0.35
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.38, 0.25)
    b.inputs["Subsurface Scale"].default_value = 2.4
    b.inputs["Specular IOR Level"].default_value = 0.42
    b.inputs["Coat Weight"].default_value = 0.06; b.inputs["Coat Roughness"].default_value = 0.35
    # bump: pori (voronoi) + kerutan halus (noise)
    vo = nd.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 0.9; lk.new(tc.outputs["Object"], vo.inputs["Vector"])
    n3 = nd.new("ShaderNodeTexNoise"); n3.inputs["Scale"].default_value = 0.22; n3.inputs["Detail"].default_value = 10; lk.new(tc.outputs["Object"], n3.inputs["Vector"])
    hm = nd.new("ShaderNodeMixRGB"); hm.blend_type = "MIX"; hm.inputs[0].default_value = 0.55
    lk.new(vo.outputs["Distance"], hm.inputs[1]); lk.new(n3.outputs["Fac"], hm.inputs[2])
    bp = nd.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.10; bp.inputs["Distance"].default_value = 1.0
    lk.new(hm.outputs["Color"], bp.inputs["Height"]); lk.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


skin = make_skin()
body.data.materials.append(skin)

deps = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(body, deps)

# ----------------------------------------------------------------- celana panjang (dibuat setelah BVH kulit, supaya elektroda dan perangkat tetap mengikuti kulit)
trousers = build_trousers(voxel=2.4 if VOX < 3 else 3.2)
fab = bpy.data.materials.new("kain_celana"); fab.use_nodes = True
fb_ = fab.node_tree.nodes["Principled BSDF"]
fb_.inputs["Base Color"].default_value = (0.07, 0.085, 0.125, 1); fb_.inputs["Roughness"].default_value = 0.82
for nm_, v_ in (("Sheen Weight", 0.5), ("Sheen Roughness", 0.5)):
    if nm_ in fb_.inputs: fb_.inputs[nm_].default_value = v_
nz_ = fab.node_tree.nodes.new("ShaderNodeTexNoise"); nz_.inputs["Scale"].default_value = 3.2; nz_.inputs["Detail"].default_value = 3
bp_ = fab.node_tree.nodes.new("ShaderNodeBump"); bp_.inputs["Strength"].default_value = 0.25; bp_.inputs["Distance"].default_value = 0.5
fab.node_tree.links.new(nz_.outputs["Fac"], bp_.inputs["Height"]); fab.node_tree.links.new(bp_.outputs["Normal"], fb_.inputs["Normal"])
trousers.data.materials.append(fab)


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


def soft_mat(name, color, rough=0.6):
    """bahan bertepi lembut: alfa dibaca dari atribut warna titik 'a' (R) lalu dicampur dengan transparan."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nd = nt.nodes; lk = nt.links
    b = nd["Principled BSDF"]; b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Subsurface Weight"].default_value = 0.2
    at = nd.new("ShaderNodeVertexColor"); at.layer_name = "a"
    tr = nd.new("ShaderNodeBsdfTransparent")
    mx = nd.new("ShaderNodeMixShader")
    out = nd["Material Output"]
    lk.new(at.outputs["Color"], mx.inputs[0]) if False else None
    sp = nd.new("ShaderNodeSeparateColor"); lk.new(at.outputs["Color"], sp.inputs["Color"])
    lk.new(sp.outputs["Red"], mx.inputs[0])
    lk.new(tr.outputs["BSDF"], mx.inputs[1]); lk.new(b.outputs["BSDF"], mx.inputs[2])
    lk.new(mx.outputs["Shader"], out.inputs["Surface"])
    return m


def decal_soft(name, x, z, r, material, power=1.6, thick=0.35, rings=6, nseg=48, sy=1.0):
    """bercak berbentuk cakram dengan tepi memudar (areola, tahi lalat) yang mengikuti kulit."""
    p, n = skin_at(x, z)
    u, v = frame(p, n)
    bm = bmesh.new()
    lay = bm.loops.layers.color.new("a")
    verts = [[bm.verts.new(tuple(p + n * thick))]]
    for ri in range(1, rings + 1):
        rr = r * ri / rings
        ring = []
        for k in range(nseg):
            a = 2 * math.pi * k / nseg
            q = p + u * (rr * math.cos(a)) + v * (rr * sy * math.sin(a))
            loc, nn = surf(q + n * 40.0, -n)
            ring.append(bm.verts.new(tuple((loc if loc is not None else q) + n * thick)))
        verts.append(ring)
    def setcol(face, fn):
        for lp in face.loops:
            rr_ = (lp.vert.co - Vector(p + n * thick)).length / max(r, 1e-6)
            al = max(0.0, 1.0 - min(rr_, 1.0)) ** power if rr_ < 0.999 else 0.0
            lp[lay] = (al, al, al, 1.0)
    for k in range(nseg):
        kk = (k + 1) % nseg
        f = bm.faces.new([verts[0][0], verts[1][k], verts[1][kk]]); setcol(f, None)
    for ri in range(1, rings):
        for k in range(nseg):
            kk = (k + 1) % nseg
            f = bm.faces.new([verts[ri][k], verts[ri + 1][k], verts[ri + 1][kk], verts[ri][kk]]); setcol(f, None)
    ob = mesh_obj(name, bm, material)
    smooth(ob, 80)
    return ob, p, n


areola_m = soft_mat("areola", (0.55, 0.34, 0.28), 0.55)
mole_m = soft_mat("tahi_lalat", (0.22, 0.12, 0.08), 0.55)
for sx_, nm in ((-1, "r"), (1, "l")):
    ob_, p_, n_ = decal_soft(f"areola_{nm}", sx_ * 97, 244, 11.0, areola_m, power=0.55, thick=0.30)
    # puting kecil
    bmn = bmesh.new(); bmesh.ops.create_uvsphere(bmn, u_segments=24, v_segments=14, radius=2.5)
    tip_ = mesh_obj(f"puting_{nm}", bmn, mat("puting", (0.50, 0.30, 0.25), 0.55, 0.0, **{"Subsurface Weight": 0.2}))
    tip_.scale = (1.0, 1.0, 0.6)
    q_ = n_.cross(Vector((0, 0, 1))) if abs(n_.z) < 0.99 else Vector((1, 0, 0))
    rot_ = n_.to_track_quat("Z", "Y")
    tip_.rotation_euler = rot_.to_euler(); tip_.location = p_ + n_ * 0.9
    smooth(tip_, 80)
# tahi lalat dan bintik kecil (tidak simetris, jauh dari area elektroda)
for k_, (mx_, mz_, mr_) in enumerate(((-40, 300, 1.7), (62, 198, 1.3), (-132, 150, 1.1), (30, 38, 1.5), (122, 262, 2.3), (-18, 336, 1.0), (96, 140, 1.4),
                                      (-72, 246, 1.2), (44, 112, 0.9), (-60, 175, 1.6), (140, 320, 1.1), (8, 215, 0.9))):
    decal_soft(f"tahi_lalat_{k_}", mx_, mz_, mr_ * 1.6, mole_m, power=0.8, thick=0.28, rings=3, nseg=24)
decal("pusar", 0, 0, 5.5, 1.5, 0.3)

# ----------------------------------------------------------------- sabuk (pita melingkar di sekitar pinggang)
fa, fb, fc = prof_fn_tr()
bm = bmesh.new()
zlev = [-66, -56, -46, -36, -26, -20]
ro, ri = [], []
nseg = 120
for z in zlev:
    a_, b_, c_ = float(fa(z)), float(fb(z)), float(fc(z))
    r_out, r_in = [], []
    for k in range(nseg):
        t = 2 * math.pi * k / nseg; ct, st = math.cos(t), math.sin(t)
        xo = (a_ + 4.5) * math.copysign(abs(ct) ** (2 / EXP_SUP), ct); yo = c_ + (b_ + 4.5) * math.copysign(abs(st) ** (2 / EXP_SUP), st)
        xi_ = (a_ + 0.1) * math.copysign(abs(ct) ** (2 / EXP_SUP), ct); yi_ = c_ + (b_ + 0.1) * math.copysign(abs(st) ** (2 / EXP_SUP), st)
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
t_dev = pd + nd * (4.7 + TR) - Rm @ Vector((0, 0, -3.5))                 # sisi belakang plate (z = -3,5) di atas sabuk
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


def add_body_hair(body):
    """rambut dada, tulang dada, garis tengah perut, dan lengan bawah: helai pendek yang rebah ke bawah mengikuti kulit; kosong di area elektroda dan sabuk."""
    me = body.data; n_ = len(me.vertices)
    co = np.zeros(n_ * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    nr = np.zeros(n_ * 3); me.vertices.foreach_get("normal", nr); nr = nr.reshape(-1, 3)
    x, z = co[:, 0], co[:, 2]

    def sstep(a, b, v):
        t = np.clip((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
    front = sstep(-0.05, -0.45, nr[:, 1])
    chest = sstep(190, 232, z) * (1 - sstep(372, 400, z)) * np.exp(-(x / 98.0) ** 2)
    abd = 0.55 * np.exp(-(x / 30.0) ** 2) * sstep(30, 70, z) * (1 - sstep(200, 215, z)) + 0.12 * (np.abs(x) < 90) * sstep(30, 70, z) * (1 - sstep(190, 215, z))
    low = 0.8 * np.exp(-(x / 16.0) ** 2) * sstep(-16, 4, z) * (1 - sstep(30, 60, z))
    arm = 0.30 * sstep(205, 222, np.abs(x)) * (1 - sstep(285, 305, np.abs(x))) * sstep(-130, -90, z) * (1 - sstep(70, 95, z))
    w = front * (chest + abd + low) + arm * (nr[:, 1] < 0.4)
    for lb_, (ex_, ez_) in EL.items():
        dd = np.hypot(x - ex_, z - ez_)
        w *= sstep(34, 52, dd)
    w *= 0.55 + 0.45 * (np.sin(x * 0.09 + 0.7) * np.cos(z * 0.075 + 1.9) * 0.5 + 0.5)       # berbercak, bukan merata
    w = np.clip(w, 0, 1)
    vg = body.vertex_groups.new(name="pelo")
    q = np.round(w * 20).astype(int)
    for lv in range(1, 21):
        idx = np.nonzero(q == lv)[0]
        if len(idx): vg.add(idx.tolist(), lv / 20.0, "REPLACE")
    bpy.context.view_layer.objects.active = body
    for o_ in bpy.context.selected_objects: o_.select_set(False)
    body.select_set(True)
    bpy.ops.object.particle_system_add()
    ps = body.particle_systems[-1]
    st = bpy.data.particles.new("rambut")
    ps.settings = st
    st.type = "HAIR"; st.count = int(os.environ.get("HAIRN", "26000")); st.hair_length = 5.5; st.hair_step = 4
    st.normal_factor = 0.30; st.object_align_factor = (0.0, 0.0, -1.0)
    st.root_radius = 1.0; st.tip_radius = 0.35; st.radius_scale = 0.09
    st.child_type = "NONE"; st.use_advanced_hair = False
    st.roughness_1 = 0.12; st.roughness_1_size = 0.6; st.roughness_endpoint = 0.05
    st.render_step = 3
    ps.vertex_group_density = "pelo"
    hm = bpy.data.materials.new("rambut"); hm.use_nodes = True
    nt_ = hm.node_tree; nt_.nodes.clear()
    ho = nt_.nodes.new("ShaderNodeOutputMaterial"); hb = nt_.nodes.new("ShaderNodeBsdfHairPrincipled")
    hb.inputs["Color"].default_value = (0.065, 0.038, 0.024, 1); hb.inputs["Roughness"].default_value = 0.34
    nt_.links.new(hb.outputs["BSDF"], ho.inputs["Surface"])
    body.data.materials.append(hm)
    st.material = len(body.data.materials)


add_body_hair(body)
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
    for t_ in (0.06, 0.15, 0.27, 0.42, 0.58, 0.74, 0.88, 1.0):
        bb = bend * math.sin(math.pi * t_)
        xzs.append((ex + sx * t_ + nrm[0] * bb, ez + sz * t_ + nrm[1] * bb))
    sk = [skin_at(x_, z_) for (x_, z_) in xzs]
    offs = [3.6, 2.8, 2.4, 2.2, 2.1, 2.0, 2.0, 2.0]
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
for t_ in (0.1, 0.2, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0):
    x_ = px_ + (jx0 - px_) * t_ + 14.0 * math.sin(math.pi * t_)
    z_ = pz_ + (jz0 - pz_) * t_
    main_pts.append(None)
    main_pts[-1] = (x_, z_)
mp3 = [main_pts[0]] + skin_path([q for q in main_pts[1:]], 2.7)
main = tube("kabel_utama", mp3, 1.9, wire_m, 16)

# ----------------------------------------------------------------- klip PPG pada jari telunjuk tangan KANAN pasien (kiri gambar)
G = sistem.G
tip_asm = Vector((-100.0, -65.99, 28.15))                      # ujung jari referensi pada klip (bingkai asm)
neck_asm = Vector((-100.0, -34.2, 19.2))
M3 = Matrix(((0, 0, -1), (1, 0, 0), (0, -1, 0)))               # X_a -> +y, Y_a -> -z (arah jari ke bawah), Z_a -> -x (rahang atas di sisi lateral)
tip_scene = Vector(hand_pt(-1, -266.0, -47.0, -303.8))              # ujung telunjuk kanan setelah tangan berputar ke dalam
M_clip = Matrix.Translation(tip_scene) @ Matrix.Rotation(math.radians(HAND_ROT), 4, "Z") @ M3.to_4x4() @ Matrix.Translation(-tip_asm)
G["klip"]["empty"].matrix_world = M_clip
neck_w = M_clip @ neck_asm
gl_exit = DEV.matrix_world @ Vector((-75.0, sistem.S["gland"]["y"], sistem.S["gland"]["zc"]))
kb = [tuple(gl_exit), tuple(gl_exit + Vector((-18, -4, -4))), (-175.0, gl_exit.y - 6, -88.0), (-200.0, -20.0, -170.0), (-212.0, 0.0, -262.0),
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
