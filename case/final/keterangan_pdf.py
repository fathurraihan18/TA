"""PDF keterangan (A4 portrait, huruf besar): menggabungkan berkas ket_*.json dari skrip lembar menjadi satu dokumen.
python keterangan_pdf.py <keluaran.pdf> <ket1.json> [ket2.json ...]
Bagian tetap (catatan umum, verifikasi, gambar jurnal) ditulis di sini.
"""
import sys, os, json
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import CondPageBreak, BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, ListFlowable, ListItem
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = sys.argv[1]
JS = sys.argv[2:]
FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", FD + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DV-B", FD + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DV-I", FD + "DejaVuSans.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-B")

BASE = 10.5
ST = dict(
    title=ParagraphStyle("t", fontName="DV-B", fontSize=21, leading=26, spaceAfter=6),
    subtitle=ParagraphStyle("st", fontName="DV", fontSize=11.5, leading=16, textColor=colors.HexColor("#444444"), spaceAfter=14),
    h1=ParagraphStyle("h1", fontName="DV-B", fontSize=15, leading=19, spaceBefore=4, spaceAfter=3, textColor=colors.HexColor("#111111"), keepWithNext=1),
    h2=ParagraphStyle("h2", fontName="DV-B", fontSize=11.5, leading=15, spaceBefore=9, spaceAfter=3, textColor=colors.HexColor("#222222"), keepWithNext=1),
    body=ParagraphStyle("b", fontName="DV", fontSize=BASE, leading=15, spaceAfter=5),
    small=ParagraphStyle("s", fontName="DV", fontSize=9.5, leading=13, textColor=colors.HexColor("#555555"), spaceAfter=6, keepWithNext=1),
    cell=ParagraphStyle("c", fontName="DV", fontSize=9.6, leading=12.6),
    cellc=ParagraphStyle("cc", fontName="DV", fontSize=9.6, leading=12.6, alignment=TA_CENTER),
    cellh=ParagraphStyle("ch", fontName="DV-B", fontSize=9.6, leading=12.6),
    cellhc=ParagraphStyle("chc", fontName="DV-B", fontSize=9.6, leading=12.6, alignment=TA_CENTER),
    item=ParagraphStyle("i", fontName="DV", fontSize=BASE, leading=14.6, spaceAfter=2),
)
W = A4[0] - 40 * mm


def P(t, st="body"):
    return Paragraph(escape(str(t)).replace("\n", "<br/>"), ST[st])


def block(b):
    out = []
    k = b["kind"]
    if k == "para":
        out.append(P(b["text"]))
    elif k == "sub":
        out.append(P(b["text"], "h2"))
    elif k == "items":
        its = [ListItem(P(t, "item"), leftIndent=16) for t in b["lines"]]
        out.append(ListFlowable(its, bulletType="1" if b.get("numbered") else "bullet", bulletFontName="DV", bulletFontSize=BASE - 0.5, leftIndent=16, bulletDedent=14,
                                start="1" if b.get("numbered") else "•"))
        out.append(Spacer(1, 3))
    elif k == "table":
        hdr, rows = b["header"], b["rows"]
        wr = b.get("widths") or [1] * len(hdr)
        tot = float(sum(wr))
        cw = [W * w / tot for w in wr]
        al = b.get("align") or ["l"] * len(hdr)
        data = [[Paragraph(escape(h), ST["cellhc" if a == "c" else "cellh"]) for h, a in zip(hdr, al)]]
        for r in rows:
            data.append([Paragraph(escape(c), ST["cellc" if a == "c" else "cell"]) for c, a in zip(r, al)])
        t = Table(data, colWidths=cw, repeatRows=1)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#888888")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                               ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
        out.append(t); out.append(Spacer(1, 6))
    return out


# --------------------------------------------------------------------- bagian tetap
def fixed_sections():
    G = dict(code="U", title="Catatan umum dan asumsi", blocks=[])
    G["blocks"] = [
        dict(kind="items", numbered=True, lines=[
            "Elektroda. Situs Sketchfab (skfb.ly/oM96r) tidak bisa dibuka dari lingkungan kerja saya, jadi model elektroda dibuat ulang mengikuti tangkapan layar dan foto kabel yang dipakai: "
            "pad busa Ø45 mm, gel biru, snap krom, konektor berkode warna dengan relief tarik, kawat abu-abu. Modelnya sendiri adalah \"ECG Electrode Dot (single, sticky, wire)\" oleh RescueFit VLE. "
            "Untuk bentuk yang persis sama, model asli (.glb atau .obj) bisa dipakai menggantikannya.",
            "HW-605 (MAX30102). Berkas .sldprt hanya berisi papan polos, jadi kemasan sensor, pad, dan komponen kecil dimodelkan ulang dari foto dan datasheet.",
            "Gland dan saklar. Ukuran mur gland (AF 15,4 x 4,4 mm) dan tonjolan rocker saklar adalah perkiraan. Ukur komponen aslinya.",
            "Baterai 34 mm lebih panjang dari ruang kosong sisi Bawah (27,8 mm). Digambar rebah sehingga menumpuk 6,1 mm di atas modul. Pada rakitan nyata baterai miring sekitar 11 derajat dan perlu isolasi atau busa 1 mm. "
            "Baterai tidak digambar pada potongan.",
            "Layar LCD pada render mengikuti dua foto layar alat (ARMOR - Aritmia Monitoring v1.0). Sinyal ECG dan PPG digambar bersih (HR 74 bpm, SpO2 97 %, PR 76 bpm), bukan salinan derau foto.",
            "Torso pada gambar penempatan adalah model 3D laki-laki untuk ilustrasi, bukan model medis. Label gambar jurnal berbahasa Inggris supaya bisa langsung dipakai pada jurnal.",
            "Warna lead: merah RA, kuning LA, hijau RL. Penempatan RA dan LA di bawah klavikula, RL di perut kanan bawah. Sisi kanan pasien berada di kiri gambar.",
            "Konektor kabel PPG, kapasitor, dan konektor kecil pada PCB adalah ilustrasi dari foto dan Gerber."]),
    ]
    J = dict(code="J-1", title="Gambar jurnal satu per satu", blocks=[
        dict(kind="para", text="Folder 08_Jurnal_Satu_Per_Satu berisi 16 gambar terpisah (PNG 600 dpi dan PDF), semua berlabel bahasa Inggris dengan huruf 8 sampai 12 pt pada ukuran cetak. "
                               "Lebar gambar 88 mm (satu kolom) atau 180 mm (dua kolom). Caption lengkap ada di Captions_EN.txt dan Figure_Captions_EN.pdf."),
        dict(kind="table", header=["Gambar", "Isi", "Lebar (mm)"], widths=[3.2, 7.0, 1.4], align=["l", "l", "c"], rows=[
            ["Fig01", "Tampak eksplode casing", "180"], ["Fig02", "Tampak eksplode elektronik", "180"], ["Fig03", "Sistem lengkap", "180"],
            ["Fig04", "Penempatan elektroda pada torso laki-laki", "88"], ["Fig05", "Detail elektroda (atas dan samping)", "88"], ["Fig06", "Kabel 3 lead dan plug 3,5 mm", "180"],
            ["Fig07", "Kode warna lead", "180"], ["Fig08", "ESP32 DevKit C V4", "180"], ["Fig09", "Modul AD8232", "180"], ["Fig10", "Modul MAX30102 HW-605", "180"],
            ["Fig11", "Cable gland PG7 dan saklar KCD11", "180"], ["Fig12", "Casing tampak depan dan belakang", "180"], ["Fig13", "Dimensi casing", "180"],
            ["Fig14", "Tampak eksplode klip jari", "180"], ["Fig15", "Klip jari saat dipakai", "180"], ["Fig16", "Tampilan layar", "180"]]),
        dict(kind="para", text="Teks pada tampilan layar (Fig03, Fig16) berbahasa Indonesia karena itu tampilan asli alat."),
    ])
    V = dict(code="V", title="Verifikasi", blocks=[
        dict(kind="sub", text="Berkas cetak (semua mesh rapat)"),
        dict(kind="table", header=["Berkas", "Ukuran (mm)", "Volume (mm3)", "md5"], widths=[3.4, 2.2, 1.4, 3.4], align=["l", "l", "l", "l"], rows=[
            ["1_Shell_Depan", "109,80 x 63,50 x 34,40", "36271", "3576a517d843216abd4d644ad57a4426"],
            ["2_BackPlate", "133,00 x 63,50 x 8,50", "24190", "ed9ea8f1ebb3438d57badf2640d37651"],
            ["3_Penahan_Sekrup (3 bagian)", "62,00 x 30,00 x 4,80", "1849", "f32c5ea793b30cf642aeeed32744a32b"],
            ["A_RahangBawah", "67,00 x 26,00 x 19,45", "11979", "065e787a11e6ff51427cae19d7f888b3"],
            ["B_RahangAtas", "67,00 x 26,00 x 17,50", "10017", "8e5f61a74a27906b6988973a0deb0b36"],
            ["C_TutupBawah", "51,10 x 21,50 x 3,30", "2149", "00285f4c1a7ec8c8b615b42b306c1351"],
            ["D_ShimPegas", "5,60 x 5,60 x 1,00", "17", "2c26491922a3f057c82028100e652c7c"]]),
        dict(kind="para", text="Klip A, B, C identik byte demi byte dengan berkas STL klip yang diunggah. Back plate identik dengan plate v2 yang sudah dicetak."),
        dict(kind="sub", text="Casing final (uji penahan: semua lolos)"),
        dict(kind="items", lines=[
            "Back plate dan 4 lubang sekrup M3 x 8 flat head sama dengan v2 (selisih 0 mm3). Shell hanya kehilangan 4 boss (1043 mm3 dibuang, 0 mm3 ditambah).",
            "Penahan: strip 62 mm (Atas), strip 24 mm dan blok 10 mm (Bawah), semuanya berlubang pilot Ø2,7 mm, dicetak rata di meja tanpa support.",
            "Celah: batang strip 0,40 mm di atas rim plate, puncak penahan 0,70 mm di bawah PCB utama, ujung sekrup 0,50 mm dari PCB, penahan ke lubang atau kaki PCB terdekat 1,92 mm, ke dinding shell 0,30 mm.",
            "Irisan penahan dengan plate, shell, dan semua komponen adalah 0 mm3. Ulir sekrup menggigit penahan 5,0 mm.",
            "Jarak penahan ke bukaan: jack AD8232 7,2 mm, saklar 11,1 mm, micro-USB 8,6 mm, USB-C 14,9 mm, gland 15,4 mm. Tidak ada bukaan yang tertutup.",
            "Plate bersama 4 penahan masuk lurus ke shell berisi tumpukan tanpa tabrakan."]),
        dict(kind="sub", text="Tabrakan rakitan lengkap (79 bagian)"),
        dict(kind="para", text="Tidak ada irisan antara shell, plate, atau penahan dengan komponen elektronik. Irisan yang ada, semuanya diketahui:"),
        dict(kind="items", lines=[
            "Baterai dengan AD8232 (296 mm3), powerbank (182 mm3), dan header PCB (147 mm3): baterai digambar rebah penuh, lihat catatan 4 di bagian U.",
            "Sekrup dengan penahan (48 mm3): ulir M3 menggigit lubang pilot Ø2,7 mm, disengaja.",
            "Baut standoff dengan PCB layar (337 mm3): lubang PCB layar tidak dimodelkan pada model sederhana.",
            "AD8232 dengan PCB (9 mm3) dan standoff dengan PCB (2 mm3): pin header masuk soket dan baut menyentuh PCB."]),
    ])
    return G, J, V


# --------------------------------------------------------------------- dokumen
PAGEMAP = {"P-1": 2, "P-2": 3, "K-1": 4, "K-2": 5, "K-3": 6, "K-4": 7, "K-5": 8, "K-6": 9, "T-1": 10, "T-2": 11, "T-3": 12, "T-4": 13, "C-1": 14, "C-2": 15, "J-1": 16}


def on_page(c, doc):
    c.saveState()
    c.setFont("DV", 8.5); c.setFillColor(colors.HexColor("#666666"))
    c.drawString(20 * mm, 11 * mm, "Keterangan gambar: alat ECG + PPG (ESP32, TFT 3,5\", AD8232, MAX30102)")
    c.drawRightString(A4[0] - 20 * mm, 11 * mm, f"Halaman {doc.page}")
    c.restoreState()


def main():
    secs = []
    for f in JS:
        secs += json.load(open(f, encoding="utf-8"))
    G, J, V = fixed_sections()
    order = ["P-1", "P-2", "K-1", "K-2", "K-3", "K-4", "K-5", "K-6", "T-1", "T-2", "T-3", "T-4", "C-1", "C-2"]
    by = {s["code"]: s for s in secs}
    seq = [by[c] for c in order if c in by] + [J, V, G]
    seq = [G] + [s for s in seq if s is not G]
    story = [P("Keterangan gambar", "title"), P("Alat ECG + PPG: implementasi LightGBM ke ESP32 berbasis sinyal ECG dan PPG", "subtitle"),
             P("Berkas ini berisi semua teks keterangan yang dipisahkan dari lembar gambar: daftar komponen, spesifikasi, catatan, langkah, dan tabel. "
               "Kode di kolom judul tiap lembar (misalnya \"Keterangan: bagian K-3\") menunjuk ke bagian di sini.", "body"), Spacer(1, 8), P("Isi", "h1")]
    toc = [["Bagian", "Judul", "Lembar gambar (hal. pada PDF gambar)"]]
    for s in seq:
        pg = PAGEMAP.get(s["code"])
        toc.append([s["code"], s["title"], f"hal. {pg}" if pg else "-"])
    t = Table([[Paragraph(escape(c), ST["cellh" if i == 0 else "cell"]) for c in r] for i, r in enumerate(toc)], colWidths=[W * 0.12, W * 0.62, W * 0.26], repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#888888")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]))
    story += [t, PageBreak()]
    for i, s in enumerate(seq):
        story.append(CondPageBreak(70 * mm))
        story.append(P(f"{s['code']}   {s['title']}", "h1"))
        pg = PAGEMAP.get(s["code"])
        if pg: story.append(P(f"Lembar gambar: halaman {pg} pada PDF gambar.", "small"))
        for b in s["blocks"]:
            story += block(b)
        if i < len(seq) - 1:
            story.append(Spacer(1, 10))
    doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
                          title="Keterangan gambar alat ECG + PPG", author="")
    doc.addPageTemplates([PageTemplate(id="a", frames=[Frame(20 * mm, 20 * mm, W, A4[1] - 38 * mm, id="f")], onPage=on_page)])
    doc.build(story)
    print("OK", OUT)


main()
