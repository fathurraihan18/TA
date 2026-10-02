# Klip jari sensor PPG MAX30102 (modul HW-605)  -  desain ulang v2

Dibuat dari foto klip yang sudah Anda cetak (kabel mudah keluar, penjepit kurang kuat, kurang nyaman) dan referensi `PalseOX_Clip_A/B.stl`.
Satuan mm. Semua ukuran adalah parameter di `make_clip.py`.

## Masalah klip lama dan perbaikannya
| Masalah (dari foto) | Perbaikan v2 |
|---|---|
| Kabel keluar lewat celah terbuka di belakang, tanpa penahan, mudah tercabut | Terowongan **tertutup** di rahang A, **leher sempit 4,3 mm**, jalur kabel **berkelok (S)**, dua **rib penjepit** di tutup C. Tarikan bertumpu pada rumah, bukan pada solder |
| PCB sensor terbuka di permukaan jari, diikat selotip | Modul dipasang dari **bawah** ke kantong, sensor di **jendela** 6,8 x 4,9 mm, permukaan jari halus; tutup C menutup modul dan kabel |
| Pegas hanya berdiri di antara rahang, miring, gaya kurang | **Dudukan pegas**: pin di A + kantong di B, **2 posisi** (lembut / kuat) + **ring shim** 1 mm (x4); gaya nominal 2 s.d. 3,5 N untuk pegas perkiraan |
| Bentuk kotak, tepi tajam, jari tidak terkunci | Lekuk jari **R15,6** (lebar 18,4), mulut dan tepi membulat, **bahu penahan ujung jari**, bantalan busa 1 mm, permukaan atas rata |
| Sekrup engsel dan kabel dililit selotip | Lug engsel 2,4 mm di A + tab tengah 6 mm di B (sekrup M3, mengulir sendiri), tidak perlu selotip |

Tetap bisa disolder: kabel dilewatkan dan kawat disolder ke 4 pad modul **sebelum** modul dimasukkan dari bawah (lihat langkah di gambar halaman 2).

## Isi
| File | Fungsi |
|---|---|
| `klip_v2/A_RahangBawah_siap_cetak.stl` | rahang bawah (sisi bawah di meja, tanpa support) |
| `klip_v2/B_RahangAtas_siap_cetak.stl` | rahang atas (sisi atas di meja, tanpa support) |
| `klip_v2/C_TutupBawah_siap_cetak.stl` | tutup bawah (rata) |
| `klip_v2/D_ShimPegas_siap_cetak.stl` | ring shim 1 mm (cetak 4) |
| `klip_v2/Klip_PPG.blend` | model Blender (komponen referensi tampil kerangka) |
| `klip_v2/gambar/` | **Gambar teknik A3** 2 halaman (PDF + PNG): potongan, tampak atas, dimensi, eksplode, BOM, perakitan, gaya pegas |
| `klip_v2/render/`, `klip_v2/preview/` | render berwarna dan potongan |
| `klip_v2/hasil_verifikasi.txt` | keluaran `verify_clip.py` |
| `make_clip.py`, `verify_clip.py`, `render_klip.py`, `gambar_klip.py`, `sections.py` | generator, verifikasi, render, gambar |

## Ukuran utama
Klip 67,0 x 26,0 x 25,0 mm, jarak bantalan nominal 15,0 mm (jari 14 mm + busa 1 mm), sensor 22,0 mm dari mulut, engsel 46,0 mm dari mulut, massa sekitar 18 g.
Gerak engsel bebas tabrakan -6 s.d. +16 derajat (jarak bantalan sekitar 12 s.d. 22 mm).

## Gaya jepit dan cara mengatur
Gaya pada jari = k x (L0 - s) x Ls / Lf (k kekakuan pegas, L0 panjang bebas, s jarak dudukan, Ls jarak dudukan dari engsel, Lf = 24 mm).
Dengan pegas perkiraan (OD 4,2 mm, kawat 0,45 mm, L0 12 mm, k sekitar 1,3 N/mm): dudukan 1 = 2,0 N, dudukan 2 = 3,5 N; tiap shim menambah sekitar 0,3 N (dudukan 1) atau 0,6 N (dudukan 2).
Tabel untuk k = 0,4 s.d. 2,0 N/mm ada di gambar halaman 2. Sasaran nyaman untuk PPG ujung jari: 1,5 s.d. 3 N.

## Yang perlu Anda ukur lalu kirim (parameter di `make_clip.py`)
1. **Pegas**: diameter luar, diameter kawat, panjang bebas, jumlah lilitan (nilai sekarang perkiraan dari foto).
2. **Sekrup engsel**: diameter ulir dan panjang (nilai sekarang M3 x 14).
3. **Kabel 4 inti AWG**: diameter luar jaket (sekarang 4,0 mm).
4. **Modul HW-605**: panjang x lebar x tebal PCB dan jarak sensor dari tepi (sekarang 18,0 x 13,5 x 1,6 dan sensor di tengah).

## Membuat ulang
`python make_clip.py -- klip_v2`, `python verify_clip.py klip_v2`, `python render_klip.py -- klip_v2 klip_v2/render`, `python gambar_klip.py klip_v2 klip_v2/render klip_v2/gambar`
(butuh `bpy`, `trimesh`, `manifold3d`, `shapely`, `matplotlib`).
