# Dokumentasi API Taman Kehati

Dokumen ini memberikan ringkasan fungsionalitas dari setiap endpoint API yang tersedia.

## Data Utama

### Taman Kehati (`/api/taman`)
Bagian ini digunakan untuk mengelola data taman kehati.
- `GET /`: Menampilkan daftar semua taman kehati dengan paginasi, filter, dan pencarian.
- `GET /{taman_id}`: Mengambil data taman kehati spesifik berdasarkan ID.
- `POST /`: (Hanya Admin) Membuat taman kehati baru.
- `PUT /{taman_id}`: (Hanya Admin) Memperbarui data taman kehati.
- `DELETE /{taman_id}`: (Hanya Admin) Menghapus data taman kehati.
- `GET /{taman_id}/geo`: Mengambil data geometri dari sebuah taman kehati dalam format GeoJSON.
- `GET /{taman_id}/stats`: Mengambil data statistik dari sebuah taman kehati (contoh: jumlah koleksi).
- `GET /near`: Menemukan taman kehati yang berada di dekat koordinat tertentu.

### Koleksi Tumbuhan (`/api/koleksi`)
Bagian ini digunakan untuk mengelola data spesimen tumbuhan yang ada di dalam taman.
- `GET /`: Menampilkan daftar semua koleksi tumbuhan dengan filter, paginasi, dan pencarian.
- `GET /{koleksi_id}`: Mengambil data koleksi tumbuhan spesifik berdasarkan ID.
- `POST /`: (Hanya Admin) Membuat data koleksi tumbuhan baru.
- `PUT /{koleksi_id}`: (Hanya Admin) Memperbarui data koleksi tumbuhan.
- `DELETE /{koleksi_id}`: (Hanya Admin) Menghapus data koleksi tumbuhan.
- `GET /{koleksi_id}/media`: Mengambil data media yang terhubung dengan sebuah koleksi tumbuhan.
- `GET /{koleksi_id}/relations`: Mengambil data koleksi dan artikel terkait untuk sebuah koleksi tumbuhan.
- `GET /suggest`: Mendapatkan saran koleksi tumbuhan berdasarkan query pencarian.
- `GET /stats`: Mengambil data statistik untuk koleksi tumbuhan, dikelompokkan berdasarkan kolom tertentu.
- `GET /map-clusters`: Mengambil data pengelompokan koleksi tumbuhan untuk visualisasi peta.

### Artikel (`/api/artikel`)
Bagian ini digunakan untuk mengelola artikel yang berhubungan dengan taman atau tumbuhan.
- `GET /`: Menampilkan daftar semua artikel dengan paginasi, filter, dan pencarian.
- `GET /{artikel_id}`: Mengambil data artikel spesifik berdasarkan ID.
- `GET /slug/{slug}`: Mengambil data artikel spesifik berdasarkan slug.
- `POST /`: (Hanya Admin) Membuat artikel baru.
- `PUT /{artikel_id}`: (Hanya Admin) Memperbarui artikel.
- `DELETE /{artikel_id}`: (Hanya Admin) Menghapus artikel.
- `PATCH /{artikel_id}/publish`: (Hanya Admin) Menerbitkan sebuah artikel.
- `PATCH /{artikel_id}/cover`: (Hanya Admin) Mengatur gambar sampul untuk sebuah artikel.
- `GET /{artikel_id}/related`: Mengambil artikel terkait untuk sebuah artikel.

## Data & Fitur Pendukung

### Pencarian (Search) (`/api/`)
- `GET /`: Melakukan pencarian teks di semua entitas (taman, koleksi, artikel) menggunakan parameter `q`.
- `GET /suggest`: Mendapatkan saran pencarian berdasarkan query.
- `POST /reindex`: (Hanya Super Admin) Membangun ulang indeks pencarian.

### Autentikasi (Authentication) (`/api/auth`)
- `/register`: (Hanya Super Admin) Mendaftarkan pengguna baru.
- `/login`: Mengautentikasi pengguna dan mengembalikan token akses dan refresh.
- `/refresh`: Memperbarui token akses menggunakan token refresh.
- `/me`: Mengambil informasi pengguna yang sedang login.

### Media (`/api/media`)
- `POST /`: Mengunggah file media (foto atau video) beserta metadata.
- `GET /`: Menampilkan daftar file media dengan filter opsional.
- `PATCH /{media_id}`: (Hanya Admin) Memperbarui metadata media (caption, dll.).
- `DELETE /{media_id}`: (Hanya Admin) Menghapus file media dan catatannya dari database.

### Data Geografis (`/api/provinsi`, `/api/kabupaten-kota`, dll.)
- `/provinsi`: Menampilkan daftar semua provinsi.
- `/kabupaten-kota`: Menampilkan daftar kabupaten/kota, bisa difilter berdasarkan provinsi.
- `/kecamatan`: Menampilkan daftar kecamatan, bisa difilter berdasarkan kabupaten/kota.
- `/desa`: Menampilkan daftar desa, bisa difilter berdasarkan kecamatan.

### Zona Taman (`/api/zona`)
- `GET /`: Menampilkan daftar semua zona taman, bisa difilter berdasarkan ID taman.
- `POST /`: (Hanya Admin) Membuat zona taman baru.
- `PATCH /{zona_id}`: (Hanya Admin) Memperbarui zona taman.
- `DELETE /{zona_id}`: (Hanya Admin) Menghapus zona taman.
- `GET /{zona_id}/geo`: Mengambil data geometri dari sebuah zona taman dalam format GeoJSON.
- `GET /{zona_id}/koleksi`: Mengambil data koleksi yang berada di dalam zona taman tertentu.
- `POST /import`: (Hanya Admin) Mengimpor zona taman dari file GeoJSON.

## Administrasi & Utilitas

### Pengguna (Users) (`/api/users`)
- `GET /`: (Hanya Super Admin) Menampilkan daftar semua pengguna.
- `GET /{user_id}`: (Hanya Super Admin) Mengambil data pengguna spesifik berdasarkan ID.
- `POST /`: (Hanya Super Admin) Membuat pengguna baru.
- `PUT /{user_id}`: Memperbarui profil pengguna sendiri, atau memperbolehkan super admin memperbarui pengguna manapun.
- `DELETE /{user_id}`: (Hanya Super Admin) Menghapus pengguna.

### Ekspor Data (`/api/export`)
- `/dwc`: Mengekspor data koleksi tumbuhan dalam format Darwin Core.
- `/geojson`: Mengekspor data koleksi tumbuhan dalam format GeoJSON.

### Log Audit (`/api/audit`)
- `GET /`: (Hanya Super Admin) Mengambil catatan (log) dari semua perubahan data di sistem.

### Metadata (`/api/meta`)
- `/enums`: Mengambil semua nilai enum yang digunakan di aplikasi (misalnya, untuk tipe status, peran, dll.).

### Kunjungan (Views) (`/api/views`)
- `POST /track`: Melacak kunjungan halaman (endpoint publik).
- `GET /series`: Mengambil data rangkaian kunjungan untuk analitik.
- `GET /top`: Mengambil item yang paling banyak dilihat.
