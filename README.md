# Contoh Halaman Pendaftaran Event ACTVENTURE X

Aplikasi web pendaftaran tim untuk event ACTVENTURE X berbasis Flask.

## Fitur
- Form pendaftaran tim dengan upload KTM/KTA (jpg/png/pdf) untuk tiap anggota
- Pilihan kategori Mapala/Umum
- Tampilan modern, responsif, dan mudah digunakan
- Halaman admin untuk:
  - Melihat daftar pendaftar
  - Melihat detail anggota dan file KTM/KTA
  - Ekspor data ke CSV dan PDF (beserta gambar KTM/KTA)
  - Hapus satu tim atau reset semua pendaftar (termasuk file media)
- Data pendaftar disimpan dalam file JSON
- File media tersimpan di folder `uploads/`

## Instalasi
1. **Clone repository**
   ```bash
   git clone https://github.com/HulwanulAzkaP/form_pendaftaran_sa
   cd pendaftaran
   ```
2. **Install dependencies**
   ```bash
   pip install flask pillow reportlab
   ```
3. **Siapkan folder**
   - Pastikan ada folder `static/` (berisi `logo.png`, `background.png`, `style.css`)
   - Pastikan ada folder `uploads/` (akan dibuat otomatis jika belum ada)

## Menjalankan Aplikasi
```bash
python app.py
```
Akses di browser:
- Form pendaftaran: [http://localhost:5000/](http://localhost:5000/)
- Admin: [http://localhost:5000/admin](http://localhost:5000/admin)

## Login Admin
- Password default: `admin123`

## Struktur Folder
```
pendaftaran/
├── app.py
├── registrations.json
├── static/
│   ├── logo.png
│   ├── background.png
│   └── style.css
├── templates/
│   ├── index.html
│   ├── success.html
│   ├── admin.html
│   └── admin_login.html
├── uploads/
└── README.md
```

## Library
- Python 3
- Flask
- Bootstrap 5 (CDN)
- Pillow (PIL)
- ReportLab

## Lisensi
Bebas digunakan untuk keperluan event, edukasi, dan pengembangan lebih lanjut. 
