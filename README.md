# Somnipathy Lab

Sistem deteksi awal gangguan tidur: **Flask + scikit-learn + MySQL/MariaDB + rekomendasi berbasis aturan**.

Pengguna mengisi data tidur → backend memvalidasi → model Machine Learning mengklasifikasi → mesin aturan menyusun rekomendasi → hasil disimpan ke database.

> **Bukan alat diagnosis medis.** Hasil bersifat skrining awal.

---

## 1. Status proyek saat ini

| Bagian | Status |
|---|---|
| Struktur proyek & konfigurasi | ✅ selesai |
| Application factory Flask | ✅ selesai |
| Koneksi MySQL + model SQLAlchemy | ✅ selesai |
| Halaman web (Beranda, Deteksi, Hasil, Riwayat, Tentang) | ✅ selesai |
| API `/api/predict`, `/api/health`, `/api/model-info`, `/api/detections` | ✅ selesai |
| Validasi input berbasis skema | ✅ selesai |
| Mesin rekomendasi berbasis aturan | ✅ selesai (aturan masih **draft**) |
| Pengujian otomatis | ✅ selesai (SQLite in-memory) |
| **Dataset & model ML** | ⛔ **belum ada** — `ml/artifacts/model_pipeline.pkl` belum dibuat |

Selama model belum ada:

- `POST /api/predict` membalas **503** dengan pesan jelas
- Form tetap bisa dibuka, tetapi tombol analisis dinonaktifkan
- Tidak ada prediksi palsu dan tidak ada angka akurasi karangan

Dokumentasi dataset dan EDA (belum dijalankan):

- `docs/KEBUTUHAN_DATASET.md` — kontrak dataset, fitur, target, risiko, checklist persetujuan
- `docs/RENCANA_EDA.md` — langkah pemeriksaan data sebelum training

---

## 2. Persyaratan

- **Python 3.11, 3.12, atau 3.13** (3.12 paling stabil untuk scikit-learn/pandas)
- **XAMPP** dengan MySQL/MariaDB
- Browser modern (Chrome/Edge/Firefox)

> Di komputer ini `python` mengarah ke stub Microsoft Store. Gunakan perintah **`py`**.
> Proyek sudah diuji berjalan dengan Python 3.13.0b4 di mesin ini.

---

## 3. Instalasi

### 3.1 Siapkan lingkungan Python

```bat
cd C:\xampp\htdocs\Somnipathy.lab
py -m venv venv
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r requirements.txt
```

Atau cukup jalankan `jalankan.bat` — skrip itu membuat venv, memasang dependensi, lalu menyalakan server.

### 3.2 Nyalakan MySQL

1. Buka **XAMPP Control Panel**
2. Klik **Start** pada baris **MySQL**
3. Apache **tidak perlu** dinyalakan

### 3.3 Siapkan database

Pilih salah satu:

**A. Lewat phpMyAdmin**

1. Buka <http://localhost/phpmyadmin>
2. Tab **SQL** → tempel isi `database/schema.sql` → **Go**

**B. Lewat terminal**

```bat
C:\xampp\mysql\bin\mysql.exe -u root < database\schema.sql
```

**C. Biarkan aplikasi membuat tabel otomatis**

`AUTO_CREATE_TABLES=1` di `.env` akan menjalankan `db.create_all()`. Database
`somnipathy_lab` tetap harus sudah dibuat lebih dulu.

### 3.4 Sesuaikan konfigurasi

Salin `.env.example` menjadi `.env` bila belum ada, lalu sesuaikan:

```dotenv
DB_USER=root
DB_PASSWORD=
DB_NAME=somnipathy_lab
```

---

## 4. Menjalankan aplikasi

```bat
venv\Scripts\python app.py
```

Buka <http://127.0.0.1:5000>.

Perintah CLI yang berguna:

```bat
venv\Scripts\python -m flask --app app init-db
venv\Scripts\python -m flask --app app check-model
venv\Scripts\python -m flask --app app check-rules
```

---

## 5. Struktur folder

```
Somnipathy.lab/
├── app.py                  titik masuk aplikasi
├── config.py               konfigurasi dari .env
├── requirements.txt        dependensi Python
├── jalankan.bat            skrip bantu: venv + install + run
├── backend/
│   ├── __init__.py         application factory
│   ├── extensions.py       objek SQLAlchemy
│   ├── cli.py              perintah init-db / check-model / check-rules
│   ├── models/             tabel database
│   ├── routes/             halaman web + endpoint API
│   ├── services/           validasi, ML, aturan, orkestrasi
│   └── utils/              respons JSON, error handler, sesi, tampilan
├── ml/
│   ├── feature_schema.json  daftar fitur (draft)
│   ├── schema.py            pembaca skema
│   ├── preprocessing.py     penyusun data untuk model
│   ├── train.py             pelatihan model
│   ├── evaluate.py          evaluasi model
│   ├── artifacts/           (kosong) tempat model_pipeline.pkl
│   └── data/                dataset mentah & olahan
├── rules/
│   ├── recommendation_rules.json  aturan rekomendasi (draft)
│   └── README.md                  panduan mengubah aturan
├── database/
│   └── schema.sql          DDL MySQL
├── frontend/
│   ├── templates/          HTML Jinja2
│   └── static/             CSS, JavaScript, ikon
└── tests/                  pengujian pytest
```

---

## 6. Alur kerja

```
Pengguna
   │  isi form
   ▼
detection.js ──POST /api/predict──► predict_routes
                                      │
                                      ▼
                              detection_service
                     ┌────────────────┼────────────────┐
                     ▼                ▼                ▼
              validation_service   ml_service   recommendation_service
                     │           (scikit-learn)   (aturan JSON)
                     └────────────────┼────────────────┘
                                      ▼
                                MySQL (SQLAlchemy)
                                      ▼
                          JSON hasil → redirect /hasil/<id>
```

Detail teknis:

1. **Model dimuat sekali** saat aplikasi start (`ml_service.load`), bukan tiap request.
2. **Pipeline scikit-learn** menyimpan praproses + classifier dalam satu objek, sehingga praproses saat prediksi identik dengan saat latihan.
3. **Aturan rekomendasi** dievaluasi terhadap fakta (input + hasil model), lalu diurutkan berdasarkan severity dan priority, dideduplikasi per kategori, maksimal 5 item.
4. **Riwayat** terikat pada token sesi anonim di cookie; pengguna lain tidak bisa melihatnya.

---

## 7. Endpoint API

| Metode | Alamat | Fungsi |
|---|---|---|
| GET | `/` | Beranda |
| GET | `/deteksi` | Form deteksi |
| GET | `/hasil/<id>` | Hasil deteksi |
| GET | `/riwayat` | Riwayat sesi ini |
| GET | `/tentang` | Penjelasan sistem |
| POST | `/api/predict` | Jalankan klasifikasi + rekomendasi |
| GET | `/api/detections` | Daftar riwayat (JSON, paginasi) |
| GET | `/api/detections/<id>` | Detail satu deteksi |
| GET | `/api/health` | Status database, model, aturan |
| GET | `/api/model-info` | Info model tanpa angka karangan |
| GET | `/api/schema` | Skema fitur yang dipakai form |

Contoh memanggil API dari PowerShell:

```powershell
$body = @{
  age = 27; gender = "male"; sleep_duration = 6.5; sleep_quality = 6
  physical_activity_minutes = 45; stress_level = 5; bmi = 24.2
  systolic_bp = 120; diastolic_bp = 80; heart_rate = 72; daily_steps = 8000
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:5000/api/predict `
  -Method Post -Body $body -ContentType "application/json"
```

Kode status: `400` validasi, `415` bukan JSON, `503` model belum siap, `500` kesalahan server.

---

## 8. Menambahkan dataset dan melatih model

**Prasyarat: dataset harus tersedia dan asli.** Proyek ini tidak menyertakan dataset.

1. Letakkan dataset di `ml/data/raw/` (mis. `dataset_tidur.csv`).
2. Sesuaikan `ml/feature_schema.json`:
   - `name` setiap field **harus sama** dengan nama kolom dataset
   - `target.column` = nama kolom label
   - `target.classes` = nilai kelas yang ada
3. Latih model:

```bat
venv\Scripts\python -m ml.train --csv ml/data/raw/dataset_tidur.csv
```

4. Hasil:
   - `ml/artifacts/model_pipeline.pkl`
   - `ml/artifacts/model_meta.json` (berisi akurasi & classification report dari data uji)
5. Restart server. `/api/health` akan melaporkan `model.ready = true`.
6. Evaluasi ulang bila perlu:

```bat
venv\Scripts\python -m ml.evaluate --csv ml/data/raw/dataset_tidur.csv
```

Tidak ada angka akurasi di dalam kode. Semua metrik dihitung dari dataset Anda.

---

## 9. Mengubah rekomendasi

Edit `rules/recommendation_rules.json`. Panduan lengkap: `rules/README.md`.

Perubahan langsung berlaku saat file disimpan (dimuat ulang berdasarkan waktu ubah).
Setiap rekomendasi menampilkan `rule_id` agar bisa ditelusuri.

---

## 10. Pengujian

```bat
venv\Scripts\python -m pytest
```

Pengujian memakai SQLite di memori, tidak menyentuh MySQL dan tidak membutuhkan model.

---

## 11. Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| `python` membuka Microsoft Store | Gunakan `py`, atau matikan App Execution Alias untuk `python.exe` |
| `ModuleNotFoundError: flask` | Venv belum aktif / dependensi belum dipasang: `venv\Scripts\python -m pip install -r requirements.txt` |
| Health: `database.connected = false` | MySQL belum dinyalakan, atau `DB_USER`/`DB_PASSWORD` salah |
| `Access denied for user 'root'` | Isi `DB_PASSWORD` di `.env` sesuai password MySQL Anda |
| `Unknown database 'somnipathy_lab'` | Jalankan `database/schema.sql` lebih dulu |
| `model.ready = false` | Normal sebelum model dilatih; lihat bagian 8 |
| Port 5000 dipakai aplikasi lain | Hentikan aplikasi tersebut, atau ubah `port` di `app.py` |
| scikit-learn gagal dipasang | Coba Python 3.12 lalu buat ulang venv (di mesin ini 3.13 berhasil) |

---

## 12. Catatan etika

- Hasil analisis **bukan diagnosis medis**.
- Ambang batas pada aturan masih draft dan perlu ditinjau tenaga kesehatan.
- Jangan memasukkan data identitas pribadi ke dalam form.
- Riwayat disimpan dengan token sesi anonim dan bisa dihapus dengan menghapus data di tabel `detections`.
