"""Pengumpul keterangan: teks panjang (daftar komponen, spesifikasi, catatan, langkah, tabel) dipisah dari lembar gambar A3 dan ditulis ke berkas JSON.
Dipakai oleh skrip lembar; keterangan_pdf.py menggabungkan semua JSON menjadi satu PDF keterangan yang mudah dibaca.

    import ket
    ket.begin("K-1", "ESP32 DevKit C V4")           # satu bagian per lembar
    ket.para("teks ...")                           # paragraf
    ket.items(["butir 1", "butir 2"], numbered=True)
    ket.table(["ITEM", "NAMA"], [[1, "..."]], widths=[1, 5])    # lebar relatif kolom
    ket.sub("Judul anak bagian")                    # judul kecil
    ket.save("folder/ket_k1.json")
"""
import json

_SEC = []


def begin(code, title):
    _SEC.append(dict(code=code, title=title, blocks=[]))


def _b(kind, **kw):
    _SEC[-1]["blocks"].append(dict(kind=kind, **kw))


def para(text):
    _b("para", text=text)


def sub(text):
    _b("sub", text=text)


def items(lines, numbered=False):
    _b("items", lines=list(lines), numbered=numbered)


def table(header, rows, widths=None, align=None):
    _b("table", header=list(header), rows=[[str(c) for c in r] for r in rows], widths=widths, align=align)


def save(path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_SEC, f, ensure_ascii=False, indent=1)
    _SEC.clear()
