# Cover alat ECG + PPG (ESP32 + TFT ILI9488 3,5" + PCB custom)

Rumah 2 bagian: **Shell depan** (jendela layar + semua lubang) dan **Back plate** (penutup belakang + 4 tiang penyangga PCB).
Dibuat parametrik dengan Blender (`bpy` 5.0.1). Satuan **mm**.

## Isi folder
| File | Fungsi |
|---|---|
| `ECG_PPG_Cover.blend` | Model Blender. Koleksi **Rumah** (shell + back plate) dan **Referensi_Komponen** (PCB, TFT, spacer, konektor, gland, saklar tampil sebagai kerangka kawat) |
| `1_Shell_Depan_siap_cetak.stl` | Shell, sudah diputar: **layar menghadap meja** (cetak tanpa dibalik) |
| `2_BackPlate_siap_cetak.stl` | Back plate, sisi luar menghadap meja |
| `make_case.py` | Generator parametrik (semua ukuran di bagian `PARAMETER`) |
| `verify_case.py` | Verifikasi otomatis (mesh rapat, posisi lubang, tabrakan komponen) |
| `preview/` | Gambar tampak luar, dalam, dan potongan penampang |

Di Blender: **Numpad 7 (Top)** = tampak depan layar seperti foto 1 (Kiri di sisi kanan layar, Atas di atas).
Sumbu model: **+X = Kiri, +Y = Atas, +Z = Depan**; **Z = 0 = ujung ekor baut belakang**; (0,0) = pusat 4 lubang baut M3.

## Ukuran utama
- Rongga dalam **99,0 × 57,5 mm** (celah ≥ 0,4 mm ke PCB 98,03 × 56,16 dan TFT 98,00 × 56,34); dinding **3 mm**.
- Luar **105,0 × 63,5 × 37,4 mm** (tonjolan: saklar +9,6 mm di sisi Atas, gland +6 mm di sisi Kanan).
- Tumpukan: ekor baut 5 + PCB 1,6 + spacer 20 + PCB TFT 1,6 + kaca/kepala baut 3 = **31,2 mm**; celah ke pelat depan 0,3 mm.
- Jendela layar **79 × 52 mm** (area aktif 73,44 × 48,96 mm, margin ±2,8 mm kiri-kanan dan ±1,5 mm atas-bawah; kaca 85 × 55 mm tertahan bibir 3 mm / 1,5 mm).

## Lubang (jarak diukur dari tepi PCB hijau; Z dari ujung ekor baut)
| Sisi | Fitur | Posisi | Ukuran lubang |
|---|---|---|---|
| **Bawah** | micro-USB ESP32 | pusat **20,7 mm dari Kiri** (77,3 dari Kanan); Z 12,9 – 21,1 | 12,2 × 8,2 |
| **Atas** | kabel jack AD8232 | pusat **61,3 mm dari Kiri** (36,7 dari Kanan); Z = 15,0 | Ø 7,2 |
| **Atas** | saklar rocker KCD11 (snap-in) | pusat 9,0 mm dari Kanan; Z = 18,5 | 13,7 × 9,2 (panel 1,6 mm) |
| **Kanan** | USB-C powerbank | pusat **18,1 mm dari Atas** (38,1 dari Bawah); Z 7,35 – 11,95 | 10,4 × 4,6 |
| **Kanan** | gland PG11 (kabel 5–10 mm) | pusat 16,1 mm dari Bawah; Z = 15,0 | Ø 19,0 + kantong mur segi-enam AF 24,6 |

Semua lubang sudah +0,2 mm untuk kompensasi cetak. Posisi jack, USB-C, dan micro-USB diturunkan dari Gerber
(footprint) dan file desain SparkFun AD8232, karena angka ukur manual saling bertentangan (lihat percakapan).

## Keputusan desain
- **Back plate** diikat **4 sekrup M3 × 8 (flat head)** dari belakang ke boss di dinding Atas/Bawah (lubang pilot Ø2,7, ulir sendiri).
  Rim penengah 0,2 mm celah menjaga posisi. Plate menekan PCB lewat **4 tiang berongga** (Ø7,2 untuk ekor baut + mur).
- **Gland PG11**: mur 24 mm tidak muat di dalam (menabrak tepi PCB), jadi dinding di sana dibuat tebal 9 mm dengan
  **kantong mur segi-enam** dari dalam. Gland dipasang dari luar; mur tidak perlu ditahan dengan kunci.
- **Saklar**: bagian dalam sisi Atas dekat Kanan penuh (kapasitor/konektor SW1), jadi badan saklar masuk ke **pod** di luar dinding.
- Semua tonjolan miring 45° di sisi atas cetak, sehingga tanpa support.

## Perakitan
1. Pasang saklar (snap-in) dan gland (mur masuk kantong, badan gland diputar dari luar), sambungkan kabel.
2. Masukkan tumpukan TFT+PCB dari belakang (kaca menghadap jendela).
3. Pasang back plate (tiang masuk ke ekor baut), kencangkan 4 sekrup M3 × 8.

## Pengaturan cetak (PLA/PETG)
- Layer 0,2 mm, dinding 3 perimeter, infill 20 %.
- **Support hanya di:** ruang dalam pod saklar, atas lubang gland (Ø19 + kantong segi-enam). Lubang micro-USB/USB-C/jack kecil cukup *bridging*.
- Back plate tanpa support. Shell dicetak dengan layar di bed (STL sudah dalam orientasi itu).

## Hasil verifikasi otomatis (`python verify_case.py .`)
- Shell dan back plate: mesh rapat (*watertight*), satu badan utuh, tanpa fitur < 0,9 mm.
- 7 lubang diuji posisi dan ukuran; 10 referensi komponen (PCB, TFT, kaca, spacer + ekor + kepala baut, konektor micro-USB/USB-C, plug jack, badan saklar, gland + mur) **tidak menabrak** (irisan 0,000 mm³).
- Jarak bebas: PCB hijau 0,41 mm, TFT 0,50 mm, kaca 0,30 mm, ekor baut ke tiang 0,40 mm.

## Cek fisik sebelum cetak final (belum bisa saya ukur dari foto)
1. Ukur jack: dari tepi Kiri PCB hijau ke pusat colokan harus ≈ **61 mm**.
2. Ukur mur gland PG11 Anda: lebar sisi (AF) harus ≤ **24 mm**; panjang ulir ≥ 9 mm. (Ubah `nut_af` di `make_case.py` bila beda.)
3. Pastikan area aktif layar ada di dalam jendela 79 × 52 mm (nyalakan layar putih, lihat dari depan).
4. Cetak dulu shell saja dengan infill rendah, uji pasang tumpukan, baru cetak final.

## Mengubah parameter
Edit bagian `PARAMETER` di `make_case.py`, lalu: `pip install bpy trimesh manifold3d scipy` (Python 3.11) dan
`python make_case.py -- <folder>` kemudian `python verify_case.py <folder>`.
