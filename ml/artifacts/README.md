# Folder artefak model

Folder ini **belum berisi model**. Berkas yang nanti dihasilkan oleh
`ml/train.py`:

| Berkas | Isi |
|---|---|
| `model_pipeline.pkl` | Pipeline scikit-learn lengkap (praproses + classifier) |
| `model_meta.json` | Versi model, tanggal latih, daftar fitur, metrik evaluasi |

Selama `model_pipeline.pkl` belum ada:

- `/api/health` melaporkan `model.ready = false`
- `POST /api/predict` membalas **503** dengan pesan jelas
- Website tetap bisa dibuka, tetapi analisis tidak dijalankan

Tidak ada prediksi palsu atau angka akurasi karangan di proyek ini.
