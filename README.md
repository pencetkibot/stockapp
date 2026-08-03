# StockApp - Aplikasi Stock Taking (Flask)

Aplikasi web sederhana untuk membantu proses stock taking dari file Excel.
Alur utama: upload file, pilih kolom yang diedit, isi nilai per baris, lalu unduh hasil akhir dalam format Excel.

## Fitur Saat Ini

- Upload file Excel dengan format `.xlsx` atau `.xls`.
- Validasi kolom target (harus ada di file Excel).
- Dukungan kolom tampilan (display columns) untuk informasi referensi selama input.
- Jika kolom tampilan dikosongkan, aplikasi otomatis menampilkan semua kolom selain kolom target.
- Halaman edit mobile-friendly dengan progress bar.
- Pengisian data dilakukan per baris dan menyimpan perubahan secara bertahap.
- Baris kosong otomatis dilewati saat proses edit.
- Setelah semua baris selesai, file hasil langsung diexport dan diunduh otomatis.
- Urutan kolom pada file hasil mengikuti urutan kolom file asli.

## Alur Penggunaan

1. Buka halaman upload.
2. Pilih file Excel.
3. Isi nama kolom target yang ingin diupdate.
4. (Opsional) Isi daftar kolom tampilan, dipisahkan koma.
5. Klik **Mulai Edit Data**.
6. Isi nilai kolom target untuk setiap baris, lalu klik **Simpan & Lanjut**.
7. Saat selesai, file hasil `.xlsx` otomatis terunduh.

## Menjalankan Aplikasi

Install dependensi:

```bash
pip install -r requirements.txt
```

Jalankan aplikasi (mode default production dengan Waitress):

```bash
python app.py
```

Jalankan mode development Flask (auto-reload):

```bash
set FLASK_DEBUG=1
python app.py
```

## Konfigurasi Environment Variable

- `HOST` (default: `0.0.0.0`)
- `PORT` (default: `5000`)
- `FLASK_DEBUG` (`1/true/yes` untuk mode debug)

Contoh:

```bash
set HOST=127.0.0.1
set PORT=8000
python app.py
```

## Penanganan File Sementara

- Setiap upload menggunakan nama file unik (UUID) untuk mencegah bentrok antar user/sesi.
- Data sementara disimpan sebagai JSON di folder `uploads` selama proses edit.
- Setelah export selesai, file upload awal, file JSON sementara, dan file export sesi aktif langsung dihapus.
- File lama di folder `uploads` dibersihkan otomatis jika usianya lebih dari 24 jam.

## Struktur Proyek

```text
app.py
requirements.txt
templates/
	upload.html
	edit.html
uploads/
```
