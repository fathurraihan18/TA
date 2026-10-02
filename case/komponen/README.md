# Model 3D komponen elektronik (dipakai gambar perakitan v3)

Semua dalam **mm**, sumbu sama dengan model asalnya (diselaraskan ke koordinat casing oleh `perakitan/make_assembly.py`, mode `REAL=1`).

| Komponen | Folder | Sumber model | Penyesuaian |
|---|---|---|---|
| ESP32 DevKit C V4 (ESP32-WROOM-32, 38 pin) | `esp32/` | STEP unggahan pengguna (`esp32-wroom-30pin-c-type`) | 30 pin diubah menjadi 19 pin per baris (jarak baris 25,4 mm), konektor USB-C diganti micro-USB, PCB dinaikkan 2,55 mm. `konversi_esp32.py` |
| Modul AD8232 (SparkFun) + jack 3,5 mm | `ad8232/` | Thingiverse #5330841 (`.blend` unggahan pengguna) | meter menjadi mm, pin logam dipotong pada kedalaman header PCB (Z = 6,6 mm). `konversi_ad8232.py` |
| Papan MAX30102 HW-605 | `hw605/` | dimodelkan ulang dari foto dan datasheet (`SENSOR_DE_LA_PULSERA.sldprt` format SolidWorks tertutup, tidak terbaca di sini) | papan 13,5 x 18,0 x 1,6 mm, tinggi total 3,2 mm; **ukur papan asli lalu sesuaikan `make_hw605.py`**. |

`render_komponen.py` membuat pratinjau `render/*_iso.png` dan `*_top.png` (tampak atas: +X ke kanan, +Y ke atas) untuk halaman 3 gambar perakitan:
`PX=1400,1400 python render_komponen.py -- esp32/render_parts.json render/esp32 80` (ortho 80 / 60 / 30 mm untuk ESP32 / AD8232 / HW-605).
