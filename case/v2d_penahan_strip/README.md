# Cover ECG + PPG v2d: penahan STRIP (plate v2 dan 4 sekrup dari belakang TIDAK berubah)

Pengembangan dari `../v2c_penahan_sekrup/` (4 blok) menjadi **3 strip/batang** yang memanjang di sepanjang dinding Atas dan Bawah, seperti bentuk jig bor.
Berkas: `3_Penahan_Sekrup_siap_cetak.stl` (3 bagian dalam satu berkas, dicetak terbalik: puncak di meja, tanpa support).

| Bagian | Posisi | Fungsi |
|---|---|---|
| Strip Atas | dinding Atas, x = -31 ... +31 mm | menampung 2 sekrup (x = +-23), luas lem 197 mm2 |
| Strip Bawah | dinding Bawah, x = -35 ... -11 mm | 1 sekrup (x = -23), luas lem 82 mm2 |
| Blok Bawah | dinding Bawah, x = 18 ... 28 mm | 1 sekrup (x = +23), luas lem 48 mm2 (dibatasi kaki soket ESP32 di x = 15,6) |

Bentuk: batang setinggi 2,4 mm (Z 1,9 ... 4,3) yang **melintas di atas rim plate** (celah 0,4 mm) dan **kaki** setinggi 4,8 mm tepat di celah rim plate di tiap sekrup. Strip tidak bisa dibuat menerus penuh karena kaki PCB (soket ESP32 di x = 15,6 sisi Bawah, kaki header saklar di x = -38 sisi Atas) dan rim plate.
Plate v2 dan sekrup flat head dari belakang sama persis dengan v2 (md5 identik). Cara pasang, urutan, dan peringatan sama dengan v2c (lihat `../v2c_penahan_sekrup/README.md`).

## Logika (lihat `Gambar_Logika_Penahan.png`)
- Sekrup dari belakang menarik plate ke atas dan penahan ke bawah: keduanya saling menjepit, **bukan** menahan plate ke shell.
- Agar plate tertahan di shell, penahan harus terikat ke shell. Dinding dalam rata (tidak ada tonjolan untuk dikait) dan penahan di bawah PCB, jadi ikatan hanya bisa lewat **epoxy** (atau lewat lubang di dinding: sekrup samping, `../v2b_sekrup_samping/`).
- Beban pelepasan plate yang sesungguhnya (guncangan, tarikan sabuk) kecil dibanding kekuatan bidang lem 326 mm2 (perkiraan geser epoxy 2-4 MPa, belum diuji pada printer Anda). Amplas muka lem, bersihkan alkohol, oles epoxy tipis di muka yang menghadap dinding.
- Penahan tidak menutup port: jarak ke bukaan jack AD8232 7,1 mm, saklar 11,1 mm, micro-USB 8,6 mm, USB-C 15 mm (lebih), gland 15 mm; penahan hanya setinggi 4,3 mm dari tepi belakang, bukaan paling rendah mulai 7,4 mm.

## Hasil verifikasi (`python verify_penahan.py v2d_penahan_strip .`): SEMUA LOLOS
Plate identik v2; shell hanya kehilangan 4 boss; strip tidak menabrak komponen (puncak 0,7 mm di bawah PCB, ke kaki PCB terdekat 1,92 mm); batang melintas di atas rim plate dengan celah 0,40 mm; ulir M3 menggigit 5,0 mm; plate + penahan (dipasang dengan sekrup) masuk lurus ke shell berisi tumpukan tanpa tabrakan.

**Akibat dilem:** tumpukan tidak bisa ditarik keluar dari belakang tanpa memotong penahan. Alternatif tanpa lem: `../v2b_sekrup_samping/`.

Membuat ulang: `python make_case.py -- v2d_penahan_strip --penahan --strip`, `python verify_penahan.py v2d_penahan_strip .`, `python render_pemasangan.py -- v2d_penahan_strip v3_baterai/_ref/asm v2d_penahan_strip/render`, `python gambar_pemasangan.py ...`, `python gambar_logika_penahan.py ...`.
