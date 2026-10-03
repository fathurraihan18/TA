# Cover ECG + PPG v3b: baterai tanpa menumpuk + dapat dirakit (sekrup samping)

Gabungan v3 (`--bay`: rongga Bawah diperlebar 6,75 mm, baterai PALO 103450 tidak menumpuk modul, rusuk dan stopper penyangga) dan perbaikan
urutan rakit v2b (`--rakit`: tanpa boss di dinding, 4 sekrup M3 x 8 kepala bulat dari samping ke lug di back plate, alur konektor).
Penjelasan masalah, urutan rakit, dan hasil verifikasi: lihat `../v2b_sekrup_samping/README.md` (berlaku sama). Perbedaan v3b:
- Posisi sekrup: Atas x = +-23 dan Bawah x = +-23 (rongga Bawah lebar: micro-USB tidak menjorok ke dinding, jadi **tanpa alur micro-USB**; alur hanya untuk hidung jack dan USB-C).
- Lug Bawah berada di y = -35,25 ... -28,85, tidak menyentuh rusuk (x = -37, -12, +3) maupun stopper baterai.
- `verify_case.py`: SEMUA LOLOS; `verify_insert.py`: tumpukan termasuk baterai masuk lurus tanpa irisan; plate masuk lurus.
- **v3 lama (`../v3_baterai/`) tidak bisa dirakit** (baterai, PCB, TFT, kaca, jack, micro-USB, USB-C menabrak boss/dinding pada jalur masuk). Gunakan v3b.

`python make_case.py -- v3b_sekrup_samping --bay --rakit`, `python verify_case.py v3b_sekrup_samping`, `python verify_insert.py v3b_sekrup_samping`.
Gambar teknik A3 dan gambar perakitan v3b belum diperbarui (masih berlaku untuk v3 dengan boss).
