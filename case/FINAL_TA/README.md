# FINAL_TA: gambar komponen, gambar teknik, perakitan, dan ilustrasi untuk draf TA

Perangkat: implementasi LightGBM ke ESP32 berbasis sinyal ECG dan PPG (layar TFT 3,5" ILI9488, PCB custom hijau, ESP32 DevKit C V4, AD8232, modul powerbank,
baterai PALO 103450, cable gland PG7, saklar KCD11, klip pulse oximeter MAX30102 HW-605, tiga elektroda EKG). Gambar bertanggal 05-10-2026, satuan mm, lembar A3 landscape.

## Dua berkas utama
- `00_Gambar_Lengkap/Gambar_Lengkap_ECG_PPG_A3.pdf`: semua gambar dalam satu PDF, 16 halaman (daftar, perakitan, komponen, gambar teknik cover, gambar teknik klip, penempatan elektroda), dengan penanda bab.
- `00_Gambar_Lengkap/Keterangan_Gambar_ECG_PPG_A4.pdf`: semua teks yang dulu menumpuk di lembar gambar (daftar komponen, spesifikasi, catatan, langkah, tabel), dengan huruf besar.
  Kolom judul tiap lembar menyebut bagian yang sesuai, misalnya "Keterangan: bagian K-3".

Tulisan pada lembar gambar sekarang 1,5 sampai 1,8 kali lebih besar dan hanya memuat label, nomor, dan dimensi.

## Folder
| Folder | Isi |
|---|---|
| `01_Gambar_Komponen/` | K-1 ESP32, K-2 AD8232, K-3 MAX30102 HW-605, K-4 elektroda 3 lead + plug 3,5 mm, K-5 gland PG7 + saklar KCD11, K-6 TFT, PCB utama, powerbank, baterai. |
| `02_Gambar_Teknik_Cover/` | T-1 sampai T-4: tampak 6 arah, back plate, isometrik, skema sabuk, potongan A-A sampai D-D, denah penahan. |
| `03_Gambar_Teknik_Klip/` | C-1 potongan dan dimensi, C-2 eksplode dan pemakaian klip pulse oximeter. |
| `04_Gambar_Perakitan/` | P-1 eksplode bernomor, P-2 sistem lengkap dan penempatan pada pengguna. |
| `05_Render_3D/` | Render PNG siap pakai (latar transparan kecuali `Sistem_Lengkap.png`). |
| `08_Jurnal_Satu_Per_Satu/` | 16 gambar jurnal terpisah, label bahasa Inggris, huruf 8 sampai 12 pt pada ukuran cetak, lebar 88 mm (satu kolom) atau 180 mm (dua kolom). Masing-masing PNG 600 dpi + PDF. Caption: `Captions_EN.txt` dan `Figure_Captions_EN.pdf`. |
| `09_Foto_Latar_Polos/` | Dua foto alat tampak atas dengan latar polos (putih dan abu muda), lembar perbandingan dengan foto asli, dan `Catatan.txt`. Skrip di `case/final/foto_latar/`. |
| `07_STL_siap_cetak/` | Casing (shell, back plate, penahan) dan klip (A, B, C, D) beserta `MD5.txt`. |
| `VERIFIKASI.txt` | Hasil uji mesh, plate v2, celah penahan, dan tabrakan rakitan. |
| `_render/` | Sumber render yang dipakai lembar. |

## Konvensi warna
Putih = bagian cetak 3D, hijau = PCB custom, merah = PCB layar dan modul AD8232, biru = modul powerbank, kuning = baterai dan standoff, hitam dan abu = ESP32, header, saklar.
Elektroda: merah = RA, kuning = LA, hijau = RL. RA di bawah klavikula kanan, LA di bawah klavikula kiri, RL di perut kanan bawah. Sisi kanan pasien ada di kiri gambar.

## Yang perlu dicek
1. Elektroda tidak memakai model Sketchfab asli. Situs skfb.ly/oM96r tidak bisa dibuka dari lingkungan kerja saya, jadi bentuknya dibuat ulang dari tangkapan layar dan foto kabel yang dipakai
   (modelnya "ECG Electrode Dot (single, sticky, wire)" oleh RescueFit VLE). Kirim berkas .glb atau .obj-nya kalau ingin bentuk yang persis.
2. File .sldprt HW-605 hanya berisi papan polos, jadi kemasan sensor dan pad dimodelkan ulang dari foto dan datasheet.
3. Ukuran mur gland (AF 15,4 x 4,4 mm) dan tonjolan rocker saklar adalah perkiraan. Ukur yang asli.
4. Baterai 34 mm lebih panjang dari ruang kosong 27,8 mm. Digambar rebah dan menumpuk 6,1 mm di atas modul. Di rakitan nyata baterai miring dan perlu isolasi atau busa 1 mm.
5. Torso adalah model 3D laki-laki untuk ilustrasi (otot, kulit, rambut dada, tahi lalat, celana panjang), bukan model medis. Label gambar jurnal berbahasa Inggris, kecuali teks pada layar alat yang memang berbahasa Indonesia. Nomor gambar pada caption (Fig. 1 sampai 16) perlu disesuaikan dengan naskah.

## Membangun ulang
Render (butuh Blender `bpy`, di `case/final/`): `r_komponen.py`, `r_elektroda.py`, `r_manusia.py`, `render_sistem.py`, `r_klip.py`, lalu `post_alpha.py 28 <png>` untuk membersihkan alfa lantai.
Gambar jurnal: `jurnal_gambar.py <FINAL_TA>` (pustaka `jfig.py`) dan `jurnal_caption.py`.
Lembar dan PDF: `bash bangun_pdf.sh <python>` (butuh matplotlib, pillow, trimesh, shapely, reportlab, pypdf).
Uji: `verify_perakitan.py` dan `../verify_penahan.py`.
