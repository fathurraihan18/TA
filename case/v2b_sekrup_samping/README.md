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
| Lug | - | 4 blok 9 x 6,4 mm di plate, tinggi sampai Z = 4,8 (0,2 mm di bawah PCB), pilot Ø2,6 |
| Konektor yang menjorok | tertahan dinding | **alur** di sisi dalam dinding (kulit luar tetap >= 1,2 mm): jack, micro-USB, USB-C |
| Posisi sekrup | Atas dan Bawah x = +-23 | Atas x = +-23, Bawah x = +-9 (alur micro-USB terlalu dekat ke x = 23) |
| Ukuran luar, jendela, lubang lain | - | **tidak berubah** |

Sekrup: **M3 x 8 kepala bulat (pan / button / cheese head)**, 4 buah, bukan kepala rata, **ditambah 4 ring (washer) M3**. Lubang di dinding Ø4,0 (sengaja longgar, menampung selisih posisi plate-shell sampai sekitar +-0,5 mm); kepala + ring menutupnya. Kepala duduk di permukaan dinding (menonjol 2,3 mm + ring).

## Urutan rakit (disarankan)
1. Pasang mur gland PG7 ke kantong segi-enam dari dalam, lalu gland dari luar; lewatkan kabel PPG. Pasang saklar dari luar.
2. Rakit tumpukan di luar shell: TFT + standoff 20 mm + PCB + ESP32 + AD8232 + powerbank (+ baterai). Sambungkan kabel saklar dan kabel PPG ke PCB **sebelum** tumpukan masuk (setelah masuk celah ke dinding hanya 0,4 mm).
3. Masukkan tumpukan **lurus dari belakang**, layar menghadap jendela. Konektor menyelip ke alur, tidak ada yang menyangkut.
4. Pasang back plate: tiang melingkupi ekor baut + mur, lug masuk di bawah PCB menempel dinding Atas/Bawah.
5. Kunci dengan 4 sekrup samping (ulir sendiri ke lug, tertanam 4,75 mm). Pilot Ø2,6 di lug / lubang dinding Ø4,0; jangan dikencangkan berlebihan (PETG).

## Hasil verifikasi
- `python verify_case.py v2b_sekrup_samping`: **SEMUA LOLOS** (termasuk boss tidak ada, lubang samping, lug, alur, ulir menggigit lug 33 mm3 untuk 4 sekrup, jarak lug ke kaki komponen PCB 1,66 mm).
- `python verify_insert.py v2b_sekrup_samping`: tumpukan (TFT, kaca, PCB, standoff, micro-USB, USB-C, hidung jack) digeser lurus dari luar sampai posisi akhir **tanpa irisan** dengan shell; plate masuk lurus tanpa menabrak. Pada v2 lama: 6 komponen menabrak (PCB di d = 6,7 mm, USB-C 11,7, jack 17,7, micro-USB 18,7, TFT 27,7, kaca 30,7).

## Jika shell v2 SUDAH tercetak (dan boss sudah Anda potong sendiri)
Shell tidak perlu dicetak ulang. Yang dibutuhkan: **back plate baru**, **4 lubang** di dinding, **4 sekrup + 4 ring**. Tanpa lem tembak dan tanpa mengebor PCB.
1. **Cetak back plate baru** `2_BackPlate_siap_cetak.stl` (folder ini; sisi luar di meja, tanpa support). Plate v2 lama tidak bisa dipakai: lubang sekrupnya dari belakang dan tidak punya lug.
2. **Periksa sisa boss yang Anda potong**: dinding dalam Atas/Bawah harus rata, sisa <= 0,2 mm (lug plate hanya berjarak 0,25 mm dari dinding). Kikir bila perlu. Uji dulu dengan memasang plate baru tanpa sekrup: plate harus duduk rata dengan tepi belakang shell.
3. **Bor 4 lubang Ø4,0 mm** (mata bor 4 mm, bor pelan, PETG mudah meleleh) menembus dinding Atas/Bawah, memakai jig cetak:
   - `jig_bor_ATAS.stl`: dua lubang di x = +-23 mm dari tengah shell.
   - `jig_bor_BAWAH.stl`: dua lubang di x = +-9 mm.
   Jig dipasang seperti pelana pada tepi belakang dinding: flange rata di atas tepi belakang, pelat menempel muka luar dinding, dua tab masuk ke sudut rongga (menentukan posisi X). Sumbu lubang 2,9 mm di atas tepi belakang shell (`pratinjau_jig.png`). Cetak dengan flange di meja, tanpa support.
   Atas = sisi dengan lubang jack dan saklar; Bawah = sisi dengan lubang micro-USB.
4. **Pasang**: masukkan plate (tiang melingkupi ekor baut, lug masuk di bawah PCB menempel dinding), lalu **4 sekrup M3 x 8 kepala bulat + ring M3** dari luar. Sekrup mengulir sendiri ke lug (tertanam 4,75 mm). Kencangkan secukupnya (PETG), cukup sampai plate rapat.
5. **Alur konektor** (hanya bila tumpukan Anda ternyata menyangkut saat dimasukkan, atau ingin bisa dilepas-pasang berulang): bagian yang dibuang persis `bagian_dibuang_dari_shell_v2.stl` (merah di `pratinjau_dibuang.png`). Alur di sisi dalam dinding, dari tepi belakang sampai lubang konektor, kedalaman dari muka dalam dinding:
   - Atas, jack AD8232: x dari -15,6 sampai -9,0 mm, **dalam 1,2 mm**, naik sampai Z = 15 (pusat lubang jack).
   - Bawah, micro-USB: x dari 24,1 sampai 32,5 mm, **dalam 1,7 mm**, naik sampai Z = 17 (menyatu dengan lubang micro-USB).
   - Kanan, USB-C: y dari 5,2 sampai 14,7 mm, **dalam 0,8 mm**, naik sampai Z = 9,65 (menyatu dengan lubang USB-C).
   Sisakan kulit luar dinding >= 1,2 mm. (Koordinat memakai sumbu model: +X = Kiri, +Y = Atas, Z dari ujung ekor baut; tepi belakang shell di Z = -0,5.)
6. Bila ragu dengan pekerjaan tangan, cetak ulang shell dari `1_Shell_Depan_siap_cetak.stl` (folder ini): lubang dan alur sudah ada.

**Mengapa bukan lem tembak atau mengebor PCB.** Lem tembak: tidak bisa dibongkar (baterai, kabel PPG, dan pemrograman ulang butuh akses), lemah menempel pada PETG, dan melunak oleh panas badan/saku. PCB: 4 lubang M3-nya sudah dipakai standoff; lubang baru pada PCB yang sudah jadi berisiko memutus jalur/ground dan PCB bukan titik tumpu yang baik untuk menahan plate (tertekan di antara TFT dan plate). Sekrup samping memakai bahan yang memang bisa diganti: plate dan shell.
Alat: `alat_perbaikan_v2.py` (jig), `render_perbaikan.py` (pratinjau).

## Membuat ulang
`python make_case.py -- v2b_sekrup_samping --rakit`, `python verify_case.py v2b_sekrup_samping`, `python verify_insert.py v2b_sekrup_samping`,
`python render_previews.py -- v2b_sekrup_samping ext int sec`, `python alat_perbaikan_v2.py v2b_sekrup_samping`.

Catatan: gambar teknik A3 dan gambar perakitan **belum** diperbarui untuk varian ini (masih menggambarkan boss dan sekrup dari belakang).
