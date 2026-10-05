# Cover ECG + PPG v2c: penahan sekrup terpisah (plate v2 dan 4 sekrup dari belakang TIDAK berubah)

Untuk shell v2 yang bossnya sudah dipotong. Back plate v2 yang sudah dicetak (`2_BackPlate_siap_cetak.stl`, byte-demi-byte sama dengan v2) dan 4 sekrup
M3 x 8 flat head dari belakang dipertahankan: kepala sekrup rata dengan sisi luar plate, jadi lubang plate tertutup dan PCB / solder tidak terlihat atau tersentuh kulit.
Yang baru hanya **4 penahan sekrup** (`3_Penahan_Sekrup_x4_siap_cetak.stl`): blok 10 x 6 x 4,8 mm berlubang pilot Ø2,7, sama dengan boss v2, tetapi
dicetak terpisah dan **dilem ke dinding sesudah tumpukan masuk**. (Shell di folder ini = shell v2 tanpa boss; jika shell Anda sudah dipotong, tidak perlu dicetak ulang.)

## Cara memasang (plate dipakai sebagai jig supaya sekrup pas dengan lubang plate)
1. Tumpukan (TFT + standoff + PCB + modul + kabel) sudah di dalam shell, semua sambungan beres.
2. Amplas halus muka penahan yang menghadap dinding dan area dinding bekas boss (x = +-18 ... +-28 mm, sampai 4,3 mm dari tepi belakang), bersihkan dengan alkohol.
3. Letakkan 4 penahan di atas plate (di celah rim, `pratinjau_penahan_di_plate.png`), pasang 4 sekrup dari belakang plate hingga menggigit penahan, cukup menempel (tidak keras). Beri selembar plastik/kertas minyak di bawah tiap penahan supaya tidak melekat ke plate.
4. Oleskan **lem epoxy dua komponen** (bukan lem tembak) tipis **hanya pada muka penahan yang menghadap dinding** (celah 0,3 mm menampung lem; jangan sampai ke sisi lain atau ke plate).
5. Masukkan plate + penahan ke shell (tiang plate melingkupi ekor baut, penahan menyusur dinding di bawah PCB), tekan rata, ikat dengan karet/selotip, biarkan mengeras sesuai epoxy (disarankan jenis 30 menit, 24 jam kekuatan penuh).
6. Setelah keras: lepas 4 sekrup dan plate. Penahan tetap melekat di shell. Pasang kembali plate dengan 4 sekrup seperti v2.

## PERHATIAN: akibat dilem
Penahan berada di bawah PCB (celah 0,7 mm) pada footprint PCB. Sesudah dilem, **tumpukan tidak bisa ditarik keluar lagi dari belakang** (PCB menabrak penahan).
Untuk servis (ganti baterai, ganti PCB) penahan harus dipotong lalu diganti dengan penahan baru (cetak lagi, lem lagi). Bila ingin bisa dibongkar bebas tanpa merusak apa pun,
pakai `../v2b_sekrup_samping/` (sekrup dari samping, lug di plate, tumpukan bisa ditarik keluar setelah plate dibuka).

## Hasil verifikasi (`python verify_penahan.py v2c_penahan_sekrup .`): SEMUA LOLOS
- Plate dan sekrup identik dengan v2 (md5 sama). Shell hanya kehilangan 4 boss.
- Penahan tidak menabrak komponen mana pun (PCB, TFT, kaca, standoff, micro-USB, USB-C, jack); puncak 0,7 mm di bawah PCB; ke kaki/lubang PCB terdekat 1,92 mm.
- **Lubang port tidak tertutup** (jarak penahan ke bukaan dinding): jack AD8232 8,6 mm; saklar 13,1 mm; micro-USB 8,6 mm; USB-C 23,0 mm; gland PG7 22,3 mm. Ke badan konektor: micro-USB 12,2 mm; USB-C 17,4 mm; laras jack 9,0 mm. Penahan hanya setinggi 4,3 mm dari tepi belakang, sedangkan lubang paling rendah (USB-C) mulai 7,4 mm.
- Ulir M3 menggigit penahan 5,0 mm; ujung sekrup 0,5 mm di bawah PCB.
- Plate + 4 penahan (terpasang dengan sekrup) masuk lurus ke shell berisi tumpukan tanpa tabrakan, jadi prosedur "plate sebagai jig" layak.
- Catatan: uji simulasi jalur masuk (`verify_insert.py`) untuk shell tanpa alur melaporkan konektor micro-USB, USB-C, dan hidung jack menyangkut dinding; pada rakitan fisik Anda tumpukan sudah berhasil masuk, jadi alur tidak diperlukan.

Membuat ulang: `python make_case.py -- v2c_penahan_sekrup --penahan`, `python verify_penahan.py v2c_penahan_sekrup .`, `python render_penahan.py -- ...`.
