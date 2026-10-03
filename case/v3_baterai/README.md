# Cover v3: baterai PALO 103450 muat tanpa menumpuk

> **PERHATIAN**: versi ini memakai boss di dinding sehingga tumpukan TFT + PCB + baterai tidak bisa dimasukkan dari belakang. Pakai `../v3b_sekrup_samping/` (ukuran luar sama, sekrup dari samping).

Dibuat dari generator yang sama dengan v2 (`../make_case.py -- <folder> --bay`). Semua yang sudah Anda setujui di v2 **tidak berubah**:
posisi dan ukuran semua lubang terhadap PCB (micro-USB Bawah, jack + saklar KCD11 Atas, USB-C + gland PG7 Kanan), jendela layar, 4 sekrup M3 x 8, 4 tiang penyangga PCB, sayap + 2 slot sabuk, sudut R5, chamfer, tebal dinding 3 mm.

## Apa yang berubah dari v2
| | v2 | v3 |
|---|---|---|
| Rongga dalam | 99,0 x 57,5 mm | **99,0 x 64,25 mm** (hanya sisi **Bawah** +6,75 mm) |
| Shell | 105,0 x 63,5 x 34,4 | **105,0 x 70,25 x 34,4** |
| Back plate + sayap | 133,0 x 63,5 | **133,0 x 70,25** (slot sabuk dipusatkan ulang pada outline baru) |
| Baterai | menumpuk 6,1 mm di tepi AD8232 / powerbank | **tidak menumpuk**: celah 0,6 mm ke tepi Bawah modul |
| Back plate | polos | + **3 rusuk penyangga** (X = -37 / -12 / +3) dan **2 stopper** di ujung baterai |
| Massa cover | sekitar 43 g | sekitar 47 g (PETG, infill 20 %) |

Baterai 10 x 34 x 50 mm rebah di atas PCB. Area PCB yang kosong di sisi Bawah hanya 27,8 mm, jadi **6,8 mm sisi baterai menjorok keluar tepi Bawah PCB**,
dan rongga Bawah diperlebar untuk menampungnya. Bagian yang menjorok ditopang rusuk dari back plate (puncak rusuk 0,15 mm di bawah alas baterai, jarak ke PCB 0,5 mm).
Koordinat (mm, sumbu model): X -41,5 ... +8,5, Y -35,1 ... -1,1, Z 6,6 ... 16,6. Celah ke dinding Bawah 0,4 mm, ke PCB TFT 10 mm.

## Isi
| File | Fungsi |
|---|---|
| `1_Shell_Depan_siap_cetak.stl` | Shell, layar menghadap meja |
| `2_BackPlate_siap_cetak.stl` | Back plate (rusuk dan stopper menghadap atas), sisi luar menghadap meja |
| `ECG_PPG_Cover.blend` | Model Blender (Referensi_Komponen sudah memuat baterai) |
| `gambar_teknik/` | Gambar teknik A3 untuk draf TA (2 halaman, PDF + PNG), sudah memuat ukuran baru |
| `perakitan/` | Gambar eksplode bernomor + daftar komponen, penempatan komponen dan baterai (denah, tampak jadi, potongan), **komponen elektronik dengan ukuran (hal. 3)**; memakai model 3D nyata ESP32 DevKit C V4, AD8232, HW-605 (MAX30102) + klip PPG v2; PDF A3 3 halaman, PNG, render, `hasil_verifikasi.txt` |
| `preview/` | Render luar, dalam, penyangga baterai, dan potongan melalui baterai (`9_potongan_baterai_X-12.png`) |
| `_ref/` | STL desain, `summary.json`, dan STL tiap komponen perakitan (model nyata) untuk uji tabrakan |

## Perakitan
1. Pasang saklar dan gland ke shell seperti v2.
2. Masukkan tumpukan TFT + PCB dari belakang.
3. Rekatkan baterai ke PCB dengan double tape tipis (tepi Atas baterai 0,6 mm dari modul AD8232/powerbank); lapisi kapton bila ada pad atau jalur terbuka di bawahnya. Sambungkan kabel ke JST 2-pin (X +11,7).
4. Pasang back plate (tiang masuk ke ekor baut, rusuk berada di bawah bagian baterai yang menjorok), kencangkan 4 sekrup M3 x 8.

## Cetak (PETG)
Sama seperti v2: layer 0,2 mm, 3 perimeter, infill 20 %. Shell dengan layar di bed + support tree (4 boss sekrup dan atas lubang gland); back plate dengan sisi luar di bed, **tanpa support** (rusuk dan stopper tegak lurus bed).

## Hasil verifikasi otomatis
`python ../verify_case.py .` : **SEMUA LOLOS**. Mesh rapat, satu badan, tanpa fitur < 0,9 mm, semua lubang diuji posisi dan ukuran, boss sekrup ada, ulir M3 menggigit, shell dan plate tidak saling menembus.
Khusus v3: baterai tidak menyentuh shell (jarak 0,40 mm) maupun back plate (0,15 mm); celah 0,6 mm ke tepi modul; rusuk tidak menyentuh PCB (0,5 mm); puncak baterai 10 mm di bawah PCB TFT.
`python ../perakitan/verify_assembly.py .` : irisan baterai dengan AD8232, powerbank, dan header PCB = **0 mm3** (di v2 303 / 182 / 147 mm3). Sisa yang diketahui: ulir sekrup M3 di boss (5,8 mm3 per sekrup, memang mengulir sendiri), gland dengan kabel PPG, serta pin ESP32 dan AD8232 yang menancap ke soket/header PCB (memang bertemu). Dengan model nyata (`perakitan/hasil_verifikasi.txt`) tidak ada komponen yang menabrak shell atau back plate selain sekrup tadi.

## Yang perlu Anda cek sebelum cetak final
1. **Colokan micro-USB**: soket ESP32 sekarang 8,3 mm dari muka luar dinding (v2: 1,5 mm), jadi badan konektor (overmold) kabel harus muat melewati lubang 12,2 x 8,2 mm. Cek colokan Anda, atau ubah `MICRO` di `make_case.py`.
2. Ukuran fisik baterai (tebal bisa 10,5 mm bila menggembung); ruang di atasnya masih 10 mm.
3. Mur gland PG7 (AF dan tebal) dan ruang saklar, sama seperti v2.
4. Cetak dulu shell dengan infill rendah untuk uji pasang.

## Membuat ulang
`python ../make_case.py -- . --bay`, lalu `python ../verify_case.py .`, `python ../render_previews.py -- . ext int sec`,
`REAL=1 python ../perakitan/make_assembly.py -- <case> <case>/perakitan/render assembled back expA expB layout stl` (lalu `expB` lagi dengan `SCB=400` agar semua komponen masuk bingkai) dan `python ../perakitan/susun_perakitan.py <case> <case>/perakitan/render <case>/perakitan real`,
`python ../gambar_teknik/gambar_render.py -- <case> <case>/gambar_teknik/garis` dan `python ../gambar_teknik/gambar_lembar.py <case> <case>/gambar_teknik/garis <case>/preview <case>/gambar_teknik`.
