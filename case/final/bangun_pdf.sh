#!/bin/bash
# Bangun semua lembar A3, PDF gambar gabungan, dan PDF keterangan dari render yang sudah ada di FINAL_TA/_render.
# Pemakaian: bash bangun_pdf.sh [python]
PY=${1:-python3}
H=$(cd "$(dirname "$0")" && pwd)
C=$H/..
F=$C/FINAL_TA
cd "$H"
$PY jurnal_gambar.py $F
$PY jurnal_caption.py $F/08_Jurnal_Satu_Per_Satu
J=$F/08_Jurnal_Satu_Per_Satu
$PY lembar_perakitan.py $F/_render/sistem $F/04_Gambar_Perakitan $J/Fig04_Electrode_placement_male_torso.png
$PY lembar_komponen.py $F/_render $F/01_Gambar_Komponen
$PY gt_cover.py $C/v2d_penahan_strip $F/_render/garis $F/_render/cover $F/02_Gambar_Teknik_Cover
$PY gt_klip.py $C/sensor_ppg/klip_v2 $F/_render/klip $F/03_Gambar_Teknik_Klip
mkdir -p $F/00_Gambar_Lengkap/bagian
$PY lembar_depan.py $J/Fig04_Electrode_placement_male_torso.png $F/00_Gambar_Lengkap/bagian
$PY gabung_pdf.py $F/00_Gambar_Lengkap/Gambar_Lengkap_ECG_PPG_A3.pdf \
  $F/00_Gambar_Lengkap/bagian/00_Daftar_A3.pdf $F/04_Gambar_Perakitan/Gambar_Perakitan_ECG_PPG_A3.pdf $F/01_Gambar_Komponen/Gambar_Komponen_A3.pdf \
  $F/02_Gambar_Teknik_Cover/Gambar_Teknik_Cover_ECG_PPG_A3.pdf $F/03_Gambar_Teknik_Klip/Gambar_Teknik_Klip_PPG_A3.pdf $F/00_Gambar_Lengkap/bagian/99_Jurnal_A3.pdf
$PY keterangan_pdf.py $F/00_Gambar_Lengkap/Keterangan_Gambar_ECG_PPG_A4.pdf $F/04_Gambar_Perakitan/ket_perakitan.json $F/01_Gambar_Komponen/ket_komponen.json \
  $F/02_Gambar_Teknik_Cover/ket_teknik_cover.json $F/03_Gambar_Teknik_Klip/ket_teknik_klip.json
