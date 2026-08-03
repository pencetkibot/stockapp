Aplikasi untuk stock taking menggunakan python dan flask
tampilan mobile friendly
tinggal upload file stock dalam file excel, tentukan kolom yang mau diisi dan kolom-kolom yang perlu tampil selama pengisian
klik mulai edit, lalu akan tampil halaman edit sesuai kriteria dihalama updload
isi hingga selesai lalu simpan hasil stock taking

## Menjalankan aplikasi

Install dependensi:

```bash
pip install -r requirements.txt
```

Mode default memakai Waitress agar lebih aman untuk multi-user:

```bash
python app.py
```

Jika ingin mode development Flask dengan auto-reload:

```bash
set FLASK_DEBUG=1
python app.py
```

## Perilaku file sementara

Setiap upload, file JSON sementara, dan hasil export memakai nama unik agar tidak bentrok antar user meskipun nama file upload sama.
File milik sesi aktif akan dibersihkan setelah export selesai, dan file lama di folder `uploads` akan dibersihkan otomatis setelah melewati masa simpan 24 jam.
