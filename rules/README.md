# Aturan Rekomendasi Somnipathy Lab

File `recommendation_rules.json` adalah **otak** sistem rekomendasi. Isinya
data, bukan kode, sehingga teks dan ambang batas bisa diubah tanpa menyentuh
Python.

## Status: DRAFT

Semua aturan di sini masih **rancangan**. Sebelum website dipakai oleh
pengguna nyata, setiap ambang batas dan teks harus ditinjau oleh tenaga
kesehatan. Ini penting karena menyangkut kesehatan tidur.

## Struktur satu aturan

```json
{
  "id": "DUR-01",
  "priority": 30,
  "severity": "medium",
  "category": "sleep_duration",
  "when": { "all": [ { "field": "sleep_duration", "op": "lt", "value": 6 } ] },
  "title": "Durasi tidur kurang dari 6 jam",
  "message": "Penjelasan untuk pengguna..."
}
```

| Properti | Arti |
|---|---|
| `id` | Kode unik aturan. Ditampilkan di halaman hasil agar bisa diaudit. |
| `priority` | Angka kecil = dievaluasi/diurutkan lebih dulu. |
| `severity` | `high`, `medium`, `low`, `info`. Menentukan urutan tampil. |
| `category` | Satu kategori hanya menampilkan satu rekomendasi terkuat. |
| `when` | Kondisi pemicu. |
| `title`, `message` | Teks yang dilihat pengguna. |

## Operator

| Operator | Contoh | Arti |
|---|---|---|
| `eq` | `{"field":"prediction_label","op":"eq","value":"Insomnia"}` | sama dengan |
| `ne` | `{"field":"gender","op":"ne","value":"male"}` | tidak sama |
| `gt` / `gte` | `{"field":"bmi","op":"gte","value":30}` | lebih besar (atau sama) |
| `lt` / `lte` | `{"field":"sleep_duration","op":"lt","value":6}` | lebih kecil (atau sama) |
| `in` | `{"field":"gender","op":"in","value":["male","female"]}` | termasuk salah satu |
| `between` | `{"field":"age","op":"between","value":[18,60]}` | di antara dua nilai |

## Grup kondisi

```json
{ "all": [ ... ] }   // semua harus benar
{ "any": [ ... ] }   // salah satu benar
{ "not": { ... } }   // kebalikan
```

Boleh bersarang, misalnya `all` berisi `any`.

## Field yang tersedia

Field input mengikuti `ml/feature_schema.json`:

`age`, `gender`, `sleep_duration`, `sleep_quality`,
`physical_activity_minutes`, `stress_level`, `bmi`, `systolic_bp`,
`diastolic_bp`, `heart_rate`, `daily_steps`

Field tambahan hasil model:

| Field | Tipe | Arti |
|---|---|---|
| `prediction_label` | teks | Kelas hasil klasifikasi |
| `confidence` | angka 0-1 | Keyakinan model |
| `is_confident` | boolean | `confidence >= CONFIDENCE_THRESHOLD` |

## Menguji perubahan aturan

Setelah mengubah JSON, jalankan:

```
py -m pytest tests/test_rules.py
py -m flask --app app check-rules
```

Server tidak perlu di-restart: file aturan dimuat ulang otomatis saat
waktu ubahnya berubah.
