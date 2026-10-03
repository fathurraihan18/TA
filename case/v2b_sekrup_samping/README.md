# Cover ECG + PPG v2b: dapat dirakit (sekrup samping)

**Mengapa ada versi ini.** Pada v2 dan v3 (versi dengan boss di dinding) tumpukan TFT + PCB **tidak bisa dimasukkan dari belakang**:
4 boss sekrup di dinding Atas/Bawah (10 mm lebar, menjorok 6 mm, tinggi sampai Z = 4,3) berada tepat di jalur PCB (lebar 56,16 mm) dan TFT
(56,34 mm); celah di antara boss hanya sekitar 45 mm. Selain itu soket micro-USB ESP32, hidung jack AD8232, dan port USB-C powerbank menjorok
sekitar 1,5 / 0,9 / 0,6 mm ke dalam dinding sehingga ikut menyangkut bila tumpukan digeser lurus. Kesalahan ini ada pada desain saya:
verifikasi sebelumnya hanya memeriksa **posisi akhir**, bukan **jalur pemasangan**. `verify_insert.py` sekarang menguji jalur itu.

## Yang berubah (hanya opsi `--rakit` di `make_case.py`)
| | v2 (lama) | v2b |
|---|---|---|
| Boss sekrup di dinding | 4 boss | **tidak ada** (dinding dalam rata) |
| Penguncian back plate | 4 sekrup M3 x 8 kepala rata dari belakang | **4 sekrup M3 x 8 kepala bulat dari SAMPING**, menembus dinding Atas/Bawah masuk ke **lug** di back plate |
| Lug | - | 4 blok 9 x 6,4 mm di plate, tinggi sampai Z = 4,4 (0,6 mm di bawah PCB), pilot Ø2,6 |
| Konektor yang menjorok | tertahan dinding | **alur** di sisi dalam dinding (kulit luar tetap >= 1,2 mm): jack, micro-USB, USB-C |
| Posisi sekrup | Atas dan Bawah x = +-23 | Atas x = +-23, Bawah x = +-9 (alur micro-USB terlalu dekat ke x = 23) |
| Ukuran luar, jendela, lubang lain | - | **tidak berubah** |

Sekrup: **M3 x 8 kepala bulat (pan / button / cheese head)**, 4 buah, bukan kepala rata. Kepala duduk di permukaan dinding (menonjol 2,3 mm), melewati celah antara shell dan plate.

## Urutan rakit (disarankan)
1. Pasang mur gland PG7 ke kantong segi-enam dari dalam, lalu gland dari luar; lewatkan kabel PPG. Pasang saklar dari luar.
2. Rakit tumpukan di luar shell: TFT + standoff 20 mm + PCB + ESP32 + AD8232 + powerbank (+ baterai). Sambungkan kabel saklar dan kabel PPG ke PCB **sebelum** tumpukan masuk (setelah masuk celah ke dinding hanya 0,4 mm).
3. Masukkan tumpukan **lurus dari belakang**, layar menghadap jendela. Konektor menyelip ke alur, tidak ada yang menyangkut.
4. Pasang back plate: tiang melingkupi ekor baut + mur, lug masuk di bawah PCB menempel dinding Atas/Bawah.
5. Kunci dengan 4 sekrup samping (ulir sendiri ke lug, tertanam 4,75 mm). Pilot Ø2,6 / lubang dinding Ø3,4; jangan dikencangkan berlebihan (PETG).

## Hasil verifikasi
- `python verify_case.py v2b_sekrup_samping`: **SEMUA LOLOS** (termasuk boss tidak ada, lubang samping, lug, alur, ulir menggigit lug 33 mm3 untuk 4 sekrup, jarak lug ke kaki komponen PCB 1,66 mm).
- `python verify_insert.py v2b_sekrup_samping`: tumpukan (TFT, kaca, PCB, standoff, micro-USB, USB-C, hidung jack) digeser lurus dari luar sampai posisi akhir **tanpa irisan** dengan shell; plate masuk lurus tanpa menabrak. Pada v2 lama: 6 komponen menabrak (PCB di d = 6,7 mm, USB-C 11,7, jack 17,7, micro-USB 18,7, TFT 27,7, kaca 30,7).

## Jika shell v2 SUDAH tercetak: `perbaikan_v2_tercetak/`
Shell tidak perlu dicetak ulang, tetapi **back plate harus dicetak baru** (`2_BackPlate_siap_cetak.stl` di folder ini; plate lama berlubang sekrup dari belakang dan tidak punya lug).
Bagian yang dibuang dari shell v2 persis `bagian_dibuang_dari_shell_v2.stl` (1507 mm3, tidak ada material yang ditambah; lihat `pratinjau_dibuang.png`, bagian merah):
1. **Potong 4 boss rata dengan dinding** (pemotong kawat/cutter tajam lalu kikir). Dinding dalam harus rata, selisih <= 0,2 mm (celah PCB ke dinding cuma 0,4 mm).
2. **Bor 4 lubang Ø3,4** (mata bor 3,5 mm) menembus dinding Atas/Bawah, 2,5 mm di atas tepi belakang shell (Z sumbu = 2,0 dari ujung ekor baut), memakai jig cetak:
   `jig_bor_ATAS.stl` (lubang x = +-23) dan `jig_bor_BAWAH.stl` (lubang x = +-9). Jig: flange rata di tepi belakang dinding, pelat menempel muka luar, dua tab masuk ke sudut rongga (posisi X). Cetak dengan flange di meja, tanpa support (`pratinjau_jig.png`).
3. **Buat 3 alur** di sisi dalam dinding dengan pahat/mata gerinda kecil (dari tepi belakang sampai lubang konektor), kedalaman diukur dari muka dalam dinding:
   - Atas, jack AD8232: x dari -15,6 sampai -9,0 mm, **dalam 1,2 mm**, naik sampai Z = 15 (pusat lubang jack).
   - Bawah, micro-USB: x dari 24,1 sampai 32,5 mm, **dalam 1,7 mm**, naik sampai Z = 17 (menyatu dengan lubang micro-USB).
   - Kanan, USB-C: y dari 5,2 sampai 14,7 mm, **dalam 0,8 mm**, naik sampai Z = 9,65 (menyatu dengan lubang USB-C).
   Sisakan kulit luar dinding >= 1,2 mm. (Koordinat memakai sumbu model: +X = Kiri, +Y = Atas, Z dari ujung ekor baut; tepi belakang shell di Z = -0,5.)
4. Bila ragu dengan pekerjaan tangan, cetak ulang shell dari `1_Shell_Depan_siap_cetak.stl` (folder ini): lebih bersih.
Alat: `alat_perbaikan_v2.py` (jig), `render_perbaikan.py` (pratinjau).

## Membuat ulang
`python make_case.py -- v2b_sekrup_samping --rakit`, `python verify_case.py v2b_sekrup_samping`, `python verify_insert.py v2b_sekrup_samping`,
`python render_previews.py -- v2b_sekrup_samping ext int sec`, `python alat_perbaikan_v2.py v2b_sekrup_samping`.

Catatan: gambar teknik A3 dan gambar perakitan **belum** diperbarui untuk varian ini (masih menggambarkan boss dan sekrup dari belakang).
