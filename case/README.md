# Cover alat ECG + PPG (ESP32 + TFT ILI9488 3,5" + PCB custom)  -  v2 (+ varian v3 baterai di `v3_baterai/`)

Rumah 2 bagian: **Shell depan** (jendela layar + semua lubang) dan **Back plate** (penutup belakang + 4 tiang penyangga PCB + 2 sayap slot sabuk).
Dibuat parametrik dengan Blender (`bpy` 5.0.1). Satuan **mm**.

## Isi folder
| File | Fungsi |
|---|---|
| `ECG_PPG_Cover.blend` | Model Blender. Koleksi **Rumah** (shell + back plate) dan **Referensi_Komponen** (PCB, TFT, spacer, konektor, sekrup, gland, saklar tampil sebagai kerangka kawat) |
| `1_Shell_Depan_siap_cetak.stl` | Shell, sudah diputar: **layar menghadap meja** |
| `2_BackPlate_siap_cetak.stl` | Back plate, sisi luar menghadap meja |
| `gambar_teknik/` | **Gambar teknik A3 untuk draf TA** (PDF 2 halaman + PNG) dan skrip pembuatnya |
| `v3_baterai/` | **v3: casing yang memuat baterai tanpa menumpuk modul** (STL siap cetak, .blend, gambar teknik A3, gambar eksplode + penempatan baterai, pratinjau). Lihat `v3_baterai/README.md` |
| `perakitan/` | **Gambar eksplode berwarna + daftar komponen + penempatan baterai** (PDF A3 2 halaman, PNG, render) dan skrip pembuatnya |
| `make_case.py` | Generator parametrik (semua ukuran di bagian `PARAMETER`) |
| `verify_case.py` | Verifikasi otomatis |
| `data/pcb_holes.json` | Lubang bor PCB dari Gerber (untuk uji tabrakan kaki komponen) |
| `preview/` | Render tampak luar, dalam, dan potongan penampang |

Di Blender: **Numpad 7 (Top)** = tampak depan layar seperti foto 1.
Sumbu model: **+X = Kiri, +Y = Atas, +Z = Depan**; **Z = 0 = ujung ekor baut belakang**; (0,0) = pusat 4 lubang baut M3.

## Gambar perakitan, daftar komponen, dan penempatan baterai (`perakitan/`)
- `Gambar_Perakitan_Komponen_A3.pdf` (2 halaman, juga PNG per halaman):
  - **Hal. 1**: tampak eksplode bernomor (A = tumpukan utama; B = komponen di atas PCB diangkat; C = rakitan jadi) + tabel *ITEM / NAMA / JML / KETERANGAN* 14 komponen.
  - **Hal. 2**: denah penempatan baterai (tampak depan PCB, bersatuan mm), tampak jadi depan/belakang berlabel, potongan samping X = -10 mm dengan tinggi tiap lapisan, dan penjelasan tertulis.
- Baterai **PALO 103450 Li-ion 3,7 V 2000 mAh (10 x 34 x 50 mm, JST 2-pin)** diletakkan **di sisi Bawah**, rebah di atas PCB, rapat ke dinding Bawah (celah 0,4 mm):
  X = 7,5 mm dari tepi Kanan PCB s.d. 40,5 mm dari tepi Kiri; Y = -28,4 ... +5,6 mm; Z = 6,6 ... 16,6 mm. Puncak baterai masih 10,0 mm di bawah PCB TFT (Z 26,6).
- **Catatan fisik penting**: area PCB yang kosong di sisi Bawah hanya 27,8 mm, sedangkan baterai 34 mm. Baterai **menumpuk 6,1 mm** di atas tepi Bawah modul AD8232 dan powerbank
  (sesuai keputusan pengguna). Digambar rebah penuh (irisan 303 mm3 dengan AD8232, 182 mm3 dengan powerbank, 147 mm3 dengan header AD8232 = diketahui, bukan kesalahan);
  pada rakitan nyata tepi baterai bertumpu di atas modul (Z >= 12,0), baterai miring sekitar 11 derajat, puncaknya sekitar 22,9 mm (celah 3,7 mm ke PCB TFT 26,6). Beri isolasi/busa 1 mm; casing tidak berubah. Ilustrasi PPG, kapasitor, dan konektor kecil adalah perkiraan dari foto dan Gerber.
- Regenerasi: `python perakitan/make_assembly.py -- <folder case> perakitan/render assembled back expA expB layout` (butuh `bpy`; mode `stl` mengekspor STL per komponen untuk `verify_assembly.py`),
  lalu `python perakitan/susun_perakitan.py <folder case> perakitan/render perakitan` (butuh matplotlib, pillow).

## Ukuran utama
- Shell **105,0 × 63,5 × 34,4 mm** (+ tonjolan gland 4,8 mm di sisi Kanan); dengan back plate dan sayap: **133,0 × 63,5 × 37,4 mm**.
- Rongga dalam **99,0 × 57,5 mm** (celah ≥ 0,4 mm ke PCB 98,03 × 56,16 dan TFT 98,00 × 56,34); dinding 3 mm; sudut luar R5; chamfer 1,2 mm di sisi depan dan belakang.
- Tumpukan: ekor baut 5 + PCB 1,6 + spacer 20 + PCB TFT 1,6 + kaca/kepala baut 3 = **31,2 mm**; celah ke pelat depan 0,3 mm.
- Jendela layar **79 × 52 mm** (area aktif 73,44 × 48,96 mm).
- Estimasi massa cover ± **43 g** (PETG, infill 20 %), belum termasuk elektronik.

## Lubang (jarak dari tepi PCB hijau; Z dari ujung ekor baut). Ukuran = sudah +0,2 mm kompensasi cetak
| Sisi | Fitur | Posisi | Lubang |
|---|---|---|---|
| **Bawah** | micro-USB ESP32 | pusat 20,7 mm dari Kiri; Z 12,9 – 21,1 | 12,2 × 8,2 |
| **Atas** | kabel jack AD8232 | pusat 61,3 mm dari Kiri; Z = 15,0 | Ø 7,2 |
| **Atas** | saklar KCD11 mini (datar, snap-in) | pusat 46,0 mm dari Kiri; Z = 21,0 | 14,1 × 9,1 (panel 1,6 mm) |
| **Kanan** | USB-C powerbank | pusat 18,1 mm dari Atas; Z 7,25 – 12,05 | 10,6 × 4,8 |
| **Kanan** | gland **PG7** (kabel 3–6,5 mm) | pusat 16,1 mm dari Bawah; Z = 13,2 | Ø 12,8 + kantong mur segi-enam AF 15,4 |
| **Belakang** | 2 slot sabuk di sayap | X = ±59,0 dari pusat | 6,0 × 44,0 |

## Keputusan desain
- **Back plate** diikat **4 sekrup M3 × 8 flat head** dari belakang, menembus plate 3 mm lalu mengulir sendiri ke **boss** di dinding Atas/Bawah
  (ulir menggigit ≈ 4,8 mm material, celah ujung sekrup ke PCB 0,5 mm, celah boss ke PCB 0,7 mm). Rim penengah (celah 0,2 mm) menahan geser, sehingga sekrup hanya menahan tarikan.
  Plate menekan PCB lewat **4 tiang berongga** (ekor baut + mur masuk ke dalam rongga, tidak dipakai untuk mengikat).
- **Saklar** datar tanpa tonjolan: lubang panel 14 × 9 mm (spesifikasi KCD11 10 × 15 mm), dinding dipertipis dari dalam jadi 1,6 mm agar kait snap-in menjepit.
  Badan saklar butuh ruang bebas 14 × 9 × 12,5 mm di balik dinding Atas pada Z 16,5 – 25,5 (di atas modul AD8232, di bawah PCB TFT).
- **Gland PG7**: ulir 12,5 mm, panjang ulir 8 mm. Mur ditanam di kantong segi-enam di dinding (tidak menabrak PCB), tonjolan luar hanya 4,8 mm.
- **Sling**: 2 **slot sabuk** (6 × 44 mm) di sayap back plate. Sabuk turun lewat slot, melintas di belakang plate, naik lewat slot lain
  (pinggang: sabuk lebar ≤ 40 mm, tebal ≤ 4,5 mm; bahu: tali yang sama dipasang melintang lewat kedua slot). Tidak ada lubang tali di sisi Atas.
- Tonjolan gland dibuat miring 45° di sisi cetak (self-supporting). Boss sekrup menggantung 6 mm dari dinding, jadi perlu support saat cetak (lihat di bawah).

## Perakitan
1. Pasang saklar (snap-in dari dalam) dan gland (mur masuk kantong, badan gland diputar dari luar), sambungkan kabel.
2. Masukkan tumpukan TFT + PCB dari belakang (kaca menghadap jendela).
3. Pasang back plate (tiang masuk ke ekor baut), kencangkan 4 sekrup M3 × 8.

## Pengaturan cetak (PETG)
- Layer 0,2 mm, 3 perimeter, infill 20 %. Shell dicetak dengan layar di bed, back plate dengan sisi luar di bed (STL sudah dalam orientasi itu).
- **Aktifkan support otomatis (tree) hanya untuk shell**: dibutuhkan di bawah 4 boss sekrup (dinding Atas/Bawah, menggantung 6 mm) dan di atas lubang gland (Ø12,8 + kantong segi-enam).
  Lubang persegi kecil (micro-USB, USB-C, saklar) cukup *bridging*. **Back plate tanpa support.**

## Hasil verifikasi otomatis (`python verify_case.py .`)
Mesh rapat (*watertight*), satu badan, tanpa fitur < 0,9 mm; 9 lubang/fitur diuji posisi dan ukuran; boss sekrup benar-benar ada dan berlubang pilot;
boss ≥ 1,5 mm dari kaki komponen PCB (terdekat 1,9 mm); ulir M3 tertanam ≈ 25 mm³ per 4 sekrup (cengkeraman nyata);
semua komponen referensi (PCB, TFT, kaca, spacer, konektor, plug jack, sekrup, gland + mur, badan saklar) tidak menabrak (irisan 0 mm³).

**Catatan koreksi:** versi pertama (commit `9ba01d5`) punya bug: boss sekrup ikut terhapus saat rongga dipotong, jadi sekrup penutup tidak punya
material untuk dicengkeram. Pengujian lama hanya memeriksa lubang pilot, bukan keberadaan boss. Sudah diperbaiki di v2 dan diuji.

## Yang masih perlu Anda cek sebelum cetak final (tidak bisa saya ukur dari foto)
1. **Mur gland PG7**: ukur lebar sisi (AF) dan tebalnya. Default AF 15,4 / tebal ≤ 4,4. Jika beda, ubah `nut_af`, `nut_h` di `make_case.py`.
2. **Ruang saklar**: pastikan ada ruang kosong 14 × 9 × 12,5 mm di balik dinding Atas, 46 mm dari tepi Kiri PCB, di atas modul AD8232.
3. Jack: dari tepi Kiri PCB ke pusat colokan ≈ 61 mm.
4. Cetak dulu shell saja dengan infill rendah untuk uji pasang tumpukan.

## Mengubah parameter
Edit bagian `PARAMETER` di `make_case.py`, lalu: `pip install bpy trimesh manifold3d scipy` (Python 3.11) dan
`python make_case.py -- <folder>` kemudian `python verify_case.py <folder>`.
Gambar teknik: `gambar_teknik/gambar_render.py` lalu `gambar_teknik/gambar_lembar.py` (butuh matplotlib, pillow).
