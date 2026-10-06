"""Caption gambar jurnal (Inggris) -> Captions_EN.txt dan Figure_Captions_EN.pdf (A4, huruf 11 pt).
python jurnal_caption.py <folder_keluaran>
"""
import sys, os
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = sys.argv[1]
CAP = [
    ("Fig01_Exploded_view_enclosure", 180, "Exploded view of the enclosure. The TFT display (4) and the main PCB (6) sit on four M3 standoffs (5) inside the front shell (1). "
     "Three small retainers (7) take the screws that close the back plate (8), four M3 x 8 flat-head screws (9) in total. The rocker switch (2) and the PG7 cable gland (3) are fitted in the shell walls."),
    ("Fig02_Exploded_view_electronics", 180, "Exploded view of the electronics. The ESP32 DevKit C V4 (1) and the AD8232 module (2) plug into sockets and headers on the main PCB (5). "
     "The charger and boost module (3) feeds the board from the Li-ion battery (4). The PPG cable (6) ends in a connector on the PCB. "
     "The battery is drawn flat. In the assembled device it tilts slightly and rests on the two modules, with a 1 mm layer of insulation between them."),
    ("Fig03_System_overview", 180, "The complete system on a table: the wearable device, the finger-clip PPG sensor and the three-lead ECG cable with its 3.5 mm plug. "
     "The display text is in Indonesian."),
    ("Fig04_Electrode_placement_male_torso", 88, "Electrode placement and device position, anterior view (patient's right on the reader's left). RA (red) goes below the right clavicle, "
     "LA (yellow) below the left clavicle and RL (green, reference) on the right lower abdomen. The three leads join one cable that plugs into the AD8232 jack on top of the device, which is clipped to the belt. "
     "The MAX30102 finger clip is worn on the right index finger."),
    ("Fig05_Electrode_details", 88, "Disposable snap electrode: (a) top view, (b) side view. The foam pad is 45 mm in diameter and 1.2 mm thick, the hydrogel is blue, and the colour-coded connector snaps onto the stud. "
     "Total height is 8.8 mm."),
    ("Fig06_Lead_cable_and_plug", 180, "Three-lead ECG cable. (a) The leads join at a small sleeve and continue as one cable to a 3.5 mm TRS plug. (b) Plug dimensions in mm."),
    ("Fig07_Lead_colour_code", 180, "Lead colour code and electrode positions used in this work."),
    ("Fig08_ESP32_DevKit_C_V4", 180, "ESP32 DevKit C V4 (ESP32-WROOM-32, 38 pins): (a) isometric view, (b) top view, (c) side view. The pin rows are 25.4 mm apart."),
    ("Fig09_AD8232_ECG_module", 180, "AD8232 ECG module with a 3.5 mm TRS jack and a 6-pin header: (a) isometric view, (b) top view, (c) side view."),
    ("Fig10_MAX30102_HW605_module", 180, "MAX30102 HW-605 sensor module: (a) isometric view, (b) top view, (c) side view. Four of the edge pads are soldered to the 4-core cable."),
    ("Fig11_Cable_gland_and_rocker_switch", 180, "PG7 cable gland with nut (a, b) and KCD11 rocker switch (c, d). The gland passes the PPG cable through the right wall of the enclosure. The switch snaps into the top wall."),
    ("Fig12_Enclosure_front_and_rear", 180, "Enclosure: (a) front shell with the display window, rocker switch and cable gland, (b) back plate with two belt slots and four countersunk screw holes."),
    ("Fig13_Enclosure_dimensions", 180, "Enclosure dimensions in mm: (a) front view, (b) side view. The back plate with its belt wings is 133.0 mm wide, the shell is 105.0 mm wide."),
    ("Fig14_Exploded_view_finger_clip", 180, "Exploded view of the finger clip. The HW-605 module (5) is soldered to the cable (6) and slides into the lower jaw (1) from below. The cover (3) closes the underside. "
     "A spring (7), optionally with shim rings (4), presses the upper jaw (2) down, and an M3 screw (8) forms the hinge. A foam pad (9) lines the upper jaw."),
    ("Fig15_Finger_clip_in_use", 180, "The finger clip (a) on a fingertip and (b) with the bottom cover removed. The cable runs along the side channel and is clamped by two ribs in the cover."),
    ("Fig16_Display_user_interface", 180, "Display layout: ECG trace (1), PPG trace (2), heart rate (3), SpO2 and pulse rate (4), rhythm status (5), and a status line with RR interval and SDNN (6). "
     "The interface text is in Indonesian (DETAK JANTUNG: heart rate, STATUS IRAMA: rhythm status, Irama Teratur: regular rhythm)."),
]

with open(os.path.join(OUT, "Captions_EN.txt"), "w", encoding="utf-8") as f:
    for i, (name, w, c) in enumerate(CAP, 1):
        f.write(f"Fig. {i}. {c}\n   [{name}, width {w} mm]\n\n")

pdfmetrics.registerFont(TTFont("LS", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("LS-B", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"))
pdfmetrics.registerFontFamily("LS", normal="LS", bold="LS-B", italic="LS", boldItalic="LS-B")
t = ParagraphStyle("t", fontName="LS-B", fontSize=18, leading=22, spaceAfter=10)
b = ParagraphStyle("b", fontName="LS", fontSize=11.5, leading=16, spaceAfter=3)
n = ParagraphStyle("n", fontName="LS", fontSize=9.5, leading=13, textColor=colors.HexColor("#555555"), spaceAfter=12)
story = [Paragraph("Figure captions", t)]
for i, (name, w, c) in enumerate(CAP, 1):
    story.append(Paragraph(f"<b>Fig. {i}.</b> {escape(c)}", b))
    story.append(Paragraph(f"File: {name} ({w} mm wide, PNG 600 dpi and PDF)", n))
doc = SimpleDocTemplate(os.path.join(OUT, "Figure_Captions_EN.pdf"), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm, title="Figure captions")
doc.build(story)
print("OK captions", len(CAP))
