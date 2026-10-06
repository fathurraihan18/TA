# FINAL_TA - gambar komponen, gambar teknik, perakitan, dan ilustrasi untuk draf TA

Perangkat: **Implementasi LightGBM ke ESP32 berbasis sinyal ECG dan PPG** (layar TFT 3,5" ILI9488, PCB custom hijau, ESP32 DevKit C V4, AD8232, modul powerbank,
baterai PALO 103450, cable gland PG7, saklar KCD11, klip pulse oximeter MAX30102 HW-605, tiga elektroda EKG).
Semua gambar bertanggal 05-10-2026, satuan mm, lembar A3 landscape (PNG 200 dpi + PDF vektor/halaman).

| Folder | Isi |
|---|---|
| `01_Gambar_Komponen/` | K-1 ESP32 DevKit C V4, K-2 AD8232, K-3 MAX30102 HW-605, K-4 elektroda EKG 3 lead + plug 3,5 mm, K-5 gland PG7 + saklar KCD11, K-6 TFT / PCB utama / powerbank / baterai. Tiap lembar: render 3D realistis, tampak atas dan depan berdimensi, spesifikasi, keterangan bagian, sumber model. |
| `02_Gambar_Teknik_Cover/` | 4 halaman cover final (v2 tanpa boss + 3 penahan kecil): tampak 6 arah berdimensi, belakang + skema sabuk + tabel lubang, potongan A-A/B-B/C-C/D-D (skala 2,1:1), denah dan tabel penahan. |
| `03_Gambar_Teknik_Klip/` | 2 halaman klip pulse oximeter (A rahang bawah, B rahang atas, C tutup bawah, D shim): potongan, dimensi, eksplode bernomor, daftar komponen, langkah rakit, gaya jepit. |
| `04_Gambar_Perakitan/` | Hal. 1 tampak eksplode bernomor (A lapisan cover, B modul elektronik) + daftar 17 komponen + keterangan warna. Hal. 2 sistem lengkap (perangkat, klip, kabel lead, 3 elektroda), penempatan pada pengguna, tabel lead dan jalur sambungan. |
| `05_Render_3D/` | Render PNG siap pakai (latar transparan kecuali `Sistem_Lengkap.png` dan `Penempatan_Pengguna.png`). |
| `06_Gambar_Jurnal/` | Gambar gaya jurnal (RA/LA/RL pada torso 3D): 1 kolom (88 mm) dan 2 kolom (180 mm), PDF/SVG/TIFF/PNG 600 dpi, `Caption_Fig_Elektroda.txt` (EN + ID). |
| `07_STL_siap_cetak/` | Casing (shell, back plate, penahan) dan klip (A, B, C, D) + `MD5.txt`. |
| `VERIFIKASI.txt` | Hasil uji: mesh rapat, identitas plate v2, celah penahan, tabrakan rakitan. |
| `_render/` | Sumber render yang dipakai lembar (komponen, elektroda, sistem, cover, klip, garis, bagian). |

## Konvensi warna (sama di semua gambar)
Putih = bagian cetak 3D; hijau = PCB custom; merah = PCB layar TFT dan modul AD8232; biru = modul powerbank; kuning = baterai dan standoff;
hitam/abu = ESP32, header, saklar. Elektroda: **merah = RA, kuning = LA, hijau = RL**.
Penempatan: RA di bawah klavikula kanan, LA di bawah klavikula kiri, RL di perut kanan bawah; sisi kanan pasien di kiri gambar; klip PPG di jari telunjuk kanan.

## Catatan dan asumsi (periksa sebelum dicantumkan di draf)
1. **Elektroda**: situs Sketchfab (skfb.ly/oM96r) tidak dapat diakses dari lingkungan kerja ini, sehingga model elektroda dibuat ulang secara prosedural mengikuti tangkapan layar dan foto kabel Anda
   (pad busa Ø45, gel biru, snap krom, konektor berkode warna dengan relief tarik, kawat abu-abu). Model asli "ECG Electrode Dot (single, sticky, wire)" oleh RescueFit VLE (Sketchfab);
   bila ingin geometri persis, unggah berkas `.glb/.obj/.fbx`-nya dan model dapat diganti tanpa mengubah tata letak lembar. Ukuran Ø45 mm dan tinggi konektor 8,8 mm adalah ukuran model, bukan hasil ukur.
2. **HW-605 (MAX30102)**: berkas `.sldprt` hanya berisi papan polos; kemasan sensor, pad, dan komponen kecil dimodelkan ulang dari foto dan datasheet.
3. **Gland dan saklar**: mur gland AF 15,4 x 4,4 mm dan tonjolan rocker saklar adalah perkiraan; ukur komponen asli (jika berbeda ubah `nut_af`, `nut_h` di `make_case.py`).
4. **Baterai** (34 mm) lebih panjang dari ruang kosong sisi Bawah (27,8 mm): digambar rebah sehingga menembus tepi modul 6,1 mm; pada rakitan nyata miring ~11 derajat bertumpu di atas modul (beri isolasi/busa 1 mm). Baterai tidak digambar pada potongan.
5. **Layar LCD** pada render mengikuti dua foto layar alat (ARMOR - Aritmia Monitoring v1.0); sinyal ECG dan PPG digambar bersih (HR 74 bpm, SpO2 97 %, PR 76 bpm), bukan salinan derau foto.
6. Ilustrasi manusia adalah mannequin 3D untuk menunjukkan penempatan elektroda (bukan model medis); label berbahasa Inggris agar langsung dapat dipakai pada jurnal. Ganti "Fig. X" pada caption sesuai penomoran naskah.
7. Konektor kabel PPG, kapasitor, dan konektor kecil pada PCB adalah ilustrasi dari foto dan Gerber.

## Regenerasi (skrip di `case/final/`, butuh Blender `bpy`, trimesh, matplotlib, pillow)
`r_komponen.py`, `r_elektroda.py`, `r_manusia.py`, `render_sistem.py`, `r_klip.py` (Cycles) -> `post_alpha.py 28 <png...>` (membersihkan alfa lantai) ->
`lembar_komponen.py`, `gt_cover.py`, `gt_klip.py`, `lembar_perakitan.py`, `gambar_jurnal_elektroda.py`; uji: `verify_perakitan.py`, `../verify_penahan.py`.
