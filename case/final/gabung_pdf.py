"""Gabungkan semua lembar A3 menjadi satu PDF (dengan penanda bab).
python gabung_pdf.py <keluaran.pdf> <daftar.pdf> <perakitan.pdf> <komponen.pdf> <cover.pdf> <klip.pdf> <jurnal.pdf>
"""
import sys
from pypdf import PdfReader, PdfWriter

OUT = sys.argv[1]
SRC = sys.argv[2:]
NAMES = ["Daftar gambar", "Perakitan", "Gambar komponen", "Gambar teknik cover", "Gambar teknik klip PPG", "Gambar jurnal"]
w = PdfWriter()
for path, name in zip(SRC, NAMES):
    r = PdfReader(path)
    first = len(w.pages)
    for p in r.pages:
        w.add_page(p)
    w.add_outline_item(name, first)
w.add_metadata({"/Title": "Gambar alat ECG + PPG (perakitan, komponen, gambar teknik, gambar jurnal)"})
w.compress_identical_objects()
with open(OUT, "wb") as f:
    w.write(f)
print("OK", OUT, len(w.pages), "halaman")
