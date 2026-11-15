# Kebutuhan Dataset — Somnipathy Lab

**Status dokumen:** 15 November 2026
**Status dataset:** ❌ **belum tersedia** — tidak ada file data di proyek ini
**Keputusan:** belum ada pelatihan model, belum ada pengunduhan dataset

Dokumen ini adalah kontrak antara kebutuhan sistem dan dataset yang nanti dipakai.
Selama dokumen ini belum disetujui, pipeline Machine Learning **tidak dijalankan**.

---

## 1. Hasil pemeriksaan folder data

| Lokasi | Isi | Dataset? |
|---|---|---|
| `ml/data/` | subfolder `raw/` dan `processed/` | ❌ tidak ada |
| `ml/data/raw/` | hanya `README.md` (313 byte) | ❌ tidak ada |
| `ml/data/processed/` | hanya `README.md` (143 byte) | ❌ tidak ada |
| `ml/artifacts/` | hanya `README.md` (579 byte) | ❌ tidak ada model |
| Seluruh proyek (di luar `venv/`) | file `.py`, `.json`, `.html`, `.css`, `.js`, `.sql`, `.md` | ❌ tidak ada `.csv`/`.xlsx` |

Berkas `.csv`/`.pkl` yang ditemukan di proyek semuanya berada di dalam
`venv/Lib/site-packages/` (data uji bawaan numpy/scipy/sklearn/joblib) dan
**bukan** dataset Somnipathy Lab.

`flask check-model` juga melaporkan `Model siap: False`.

---

## 2. Prinsip yang tidak boleh dilanggar

1. **Tidak membuat dataset sintetis** untuk "supaya bisa training".
2. **Tidak mengunduh dataset** tanpa persetujuan tertulis dari pemilik proyek.
3. **Tidak melaporkan akurasi** sebelum model benar-benar dilatih dan diuji.
4. **Tidak mengubah pipeline** sebelum dataset diperiksa dan disetujui.
5. Klasifikasi tetap **Machine Learning**, rekomendasi tetap **rule-based**.
   Tidak ada LLM di jalur keputusan mana pun.

---

## 3. Peran dataset dalam arsitektur

```
Data mentah (CSV)  ──►  EDA & pembersihan  ──►  pelatihan (ml/train.py)
                                                        │
                                                   model_pipeline.pkl
                                                        │
Form pengguna ──► validasi ──► ml_service.predict ──► label + probabilitas
                                                        │
                                              recommendation_service (aturan)
```

Dataset **hanya** dipakai untuk melatih classifier. Rekomendasi tidak dilatih
dari dataset; ia berasal dari `rules/recommendation_rules.json`.

---

## 4. Format file yang diterima

| Aspek | Ketentuan |
|---|---|
| Format utama | `.csv` (UTF-8), baris pertama = nama kolom |
| Pemisah | koma `,` atau titik koma `;` (akan dideteksi saat EDA) |
| Desimal | titik `.` lebih disukai; koma diterima tetapi dicatat |
| Baris | satu baris = satu subjek / satu observasi |
| Kolom | nama unik, tanpa spasi di awal/akhir |
| Penamaan file | `sleep_dataset_v1.csv` (naikkan versi bila data berubah) |
| Lokasi | `ml/data/raw/` (mentah, **tidak boleh diedit**) |
| Alternatif | `.xlsx`/`.parquet` boleh, tetapi akan dikonversi ke CSV sebelum training |
| Ukuran | di bawah 50 MB agar mudah diproses lokal |

Setiap file mentah dicatat **nama, ukuran, tanggal, dan checksum SHA-256** di
`ml/data/raw/README.md` agar versi data yang dipakai bisa dilacak.

---

## 5. Fitur input dan target klasifikasi

### 5.1 Kontrak fitur saat ini (status: **draft**)

Sumber: `ml/feature_schema.json` versi `0.1.0-draft`. Form web, validasi, dan
`ml/train.py` membaca file ini.

| # | Kolom | Label di UI | Tipe | Rentang | Satuan | Wajib |
|---|---|---|---|---|---|---|
| 1 | `age` | Usia | integer | 10–100 | tahun | ya |
| 2 | `gender` | Jenis kelamin | kategori | `male`, `female` | — | ya |
| 3 | `sleep_duration` | Durasi tidur rata-rata | float | 0–14 | jam | ya |
| 4 | `sleep_quality` | Kualitas tidur | integer | 1–10 | skala | ya |
| 5 | `physical_activity_minutes` | Aktivitas fisik harian | integer | 0–300 | menit | ya |
| 6 | `stress_level` | Tingkat stres | integer | 1–10 | skala | ya |
| 7 | `bmi` | Indeks massa tubuh | float | 10–60 | kg/m² | ya |
| 8 | `systolic_bp` | Tekanan darah sistolik | integer | 70–250 | mmHg | ya |
| 9 | `diastolic_bp` | Tekanan darah diastolik | integer | 40–150 | mmHg | ya |
| 10 | `heart_rate` | Detak jantung istirahat | integer | 30–200 | bpm | ya |
| 11 | `daily_steps` | Langkah harian | integer | 0–50000 | langkah | ya |

**Target:** kolom `sleep_disorder`, 3 kelas:

| Nilai kelas | Label UI | Arti |
|---|---|---|
| `None` | Tidak terindikasi | Tidak ada indikasi gangguan tidur |
| `Insomnia` | Insomnia | Kesulitan memulai/mempertahankan tidur |
| `Sleep Apnea` | Sleep Apnea | Gangguan napas saat tidur |

### 5.2 Dua jalur penyesuaian (pilih satu, jangan campur diam-diam)

**Jalur A — skema mengikuti dataset.**
Jika dataset Anda punya nama kolom atau fitur berbeda:

1. Perbarui `ml/feature_schema.json` (`name`, `type`, `min`, `max`, `unit`).
2. Perbarui `threshold`/field pada `rules/recommendation_rules.json` bila nama field berubah.
3. Form web otomatis mengikuti karena dirender dari JSON.

**Jalur B — dataset disesuaikan ke skema.**
Lakukan pemetaan kolom eksplisit (mis. `Blood Pressure` → `systolic_bp` +
`diastolic_bp`) di tahap EDA, dan simpan hasilnya di `ml/data/processed/`.

Aturan tambahan: **jangan membuang fitur penting hanya agar cocok.** Jika
dataset tidak punya, misalnya, `daily_steps`, keputusan menghapus field harus
tercatat dan disetujui, karena aturan `STEP-01` akan berhenti relevan.

### 5.3 Fitur yang TIDAK boleh dipakai

- Kolom identitas (`Person ID`, NIK, nama, email).
- Kolom yang **diturunkan dari label** atau dari aturan yang sama dengan label.
- Kolom hasil pemeriksaan setelah diagnosis (mis. hasil polisomnografi final,
  obat yang diberikan) → menyebabkan *data leakage*.
- Kolom waktu pengisian yang membocorkan urutan pengambilan data.

---

## 6. Kualitas minimum (kriteria penerimaan)

Angka berikut adalah **heuristik**, bukan jaminan performa:

| Kriteria | Ambang minimum | Ambang ideal | Alasan |
|---|---|---|---|
| Jumlah baris | 500 | ≥ 1.000 | 3 kelas × 11 fitur butuh variasi cukup |
| Baris per kelas | 100 | ≥ 150–200 | kelas minoritas tetap bisa dipelajari |
| Proporsi kelas terkecil | ≥ 10% | ≥ 20% | hindari model "menebak mayoritas" |
| Nilai kosong per fitur kunci | ≤ 5% | 0% | imputasi berlebihan mengaburkan sinyal |
| Duplikasi baris | ≤ 1% | 0% | duplikat antar-split menggelembungkan skor |
| Rentang nilai | semua fisiologis | — | mencegah outlier mustahil (tidur 25 jam) |
| Dokumentasi sumber | ada | ada + lisensi | reproducibility dan etika |
| Data pribadi | tidak ada | tidak ada | privasi pengguna |

Jika dataset akhirnya di bawah ambang minimum, **tetap boleh dilaporkan sebagai
prototipe**, tetapi harus jujur disebut sebagai keterbatasan dan tidak
diklaim akurat untuk penggunaan nyata.

---

## 7. Risiko dataset dan mitigasinya

### 7.1 Dataset terlalu kecil

| Dampak | Penjelasan |
|---|---|
| Overfitting | Model menghafal data latih; akurasi latih tinggi, akurasi data baru jatuh |
| Variansi tinggi | Ganti random seed sedikit → metrik berubah banyak |
| Kelas minoritas tidak terpelajari | Terutama `Sleep Apnea` yang khasnya paling sedikit |
| Interval kepercayaan lebar | 1 kesalahan pada 50 data uji = 2% perubahan akurasi |

**Mitigasi:** validasi silang stratifikasi (5–10 fold), laporkan metrik per
kelas, laporkan jumlah data per kelas, dan sampaikan batasan di UI.

### 7.2 Duplikasi data

| Dampak | Penjelasan |
|---|---|
| Kebocoran train/test | Baris identik di latih dan uji membuat skor terlihat bagus padahal menghafal |
| Sampel efektif mengecil | 1.000 baris bisa jadi hanya 700 subjek unik |
| Bobot kelas bias | Duplikat menambah bobot kelas tertentu secara artifisial |

**Mitigasi:** hapus duplikat **sebelum** split; cek duplikat parsial (semua
kolom fitur sama); jika ada ID subjek, split berdasarkan ID (`GroupShuffleSplit`).

### 7.3 Ketidakseimbangan kelas

| Dampak | Penjelasan |
|---|---|
| Akurasi menyesatkan | Model menebak kelas mayoritas bisa "akurat" 80% tanpa berguna |
| Recall kelas minoritas rendah | Kasus apnea yang terlewat (false negative) justru yang paling berbahaya |
| Probabilitas tidak kalibrasi | `predict_proba` cenderung terlalu yakin pada kelas mayoritas |

**Mitigasi berurutan:**
1. `class_weight="balanced"` (sudah dipakai di `ml/train.py`).
2. Evaluasi dengan **macro-F1** dan **recall per kelas**, bukan akurasi saja.
3. Penyesuaian ambang keputusan bila perlu.
4. Resampling (SMOTE/undersampling) **hanya pada data latih**, bukan seluruh dataset. Saat ini belum dipakai; butuh persetujuan karena menambah dependensi.

### 7.4 Label tidak tervalidasi

| Dampak | Penjelasan |
|---|---|
| Plafon performa rendah | Label berisik membatasi akurasi maksimum |
| Label sirkular | Jika label dibuat dari aturan/fitur yang sama, model hanya mempelajari aturan itu → tidak menambah nilai |
| Bias pelaporan diri | Kuesioner bisa keliru mengingat durasi/keluhan |
| Tidak representatif | Populasi dataset bisa berbeda dari pengguna website (usia, wilayah, kultur) |

**Mitigasi:** catat asal label (klinis? kuesioner? aturan?), definisi tiap
kelas, dan siapa yang menetapkannya. Jika label berasal dari aturan atas
fitur yang sama, hentikan dan diskusikan ulang desain — itu bukan klasifikasi
yang bermakna.

### 7.5 Risiko tambahan yang sering terlewat

| Risiko | Contoh | Mitigasi |
|---|---|---|
| Satuan tidak konsisten | tinggi 170 vs 1.70; berat kg vs pound | validasi rentang, cek distribusi |
| Format gabungan | `"120/80"` dalam satu kolom | pecah saat EDA |
| Nilai sentinel | `0`, `-1`, `999` sebagai "tidak tahu" | perlakukan sebagai missing |
| Kategori tidak seragam | `Male`, `male`, `Laki-laki` | normalisasi + dokumentasi |
| Data leakage | kolom turunan diagnosis | buang sebelum training |
| Domain shift | dataset rumah sakit vs pengguna web | nyatakan batasan di UI |
| Privasi | data kesehatan pribadi | anonimkan, jangan simpan identitas |

---

## 8. Pilihan sumber data (belum diunduh — menunggu persetujuan)

| Opsi | Deskripsi | Catatan |
|---|---|---|
| **A. Dataset publik** | Mis. *Sleep Health and Lifestyle Dataset* (Kaggle) yang memuat durasi tidur, kualitas tidur, stres, BMI, tekanan darah, detak jantung, langkah harian, dan label gangguan tidur | Perlu persetujuan Anda, verifikasi lisensi/atribusi, dan pengecekan jumlah baris (dataset ini relatif kecil, sekitar ratusan baris — di bawah ambang ideal) |
| **B. Kuesioner sendiri** | Kumpulkan data dengan instrumen tervalidasi (mis. PSQI, ESS, STOP-BANG) | Butuh izin responden, jumlah sampel memadai, dan definisi label yang jelas |
| **C. Data klinis berlisensi** | Data dari institusi/rumah sakit | Butuh etika penelitian, anonimisasi, dan perjanjian data |

Saya **tidak** mengunduh salah satu opsi di atas sampai Anda memilih dan
menyetujuinya.

---

## 9. Yang akan dilakukan setelah persetujuan

1. Verifikasi file: ukuran, checksum, jumlah baris/kolom, encoding.
2. Menjalankan rencana EDA di `docs/RENCANA_EDA.md` (read-only terhadap data mentah).
3. Menyusun pemetaan kolom dan memutuskan Jalur A atau B (bagian 5.2).
4. Menyimpan versi bersih di `ml/data/processed/`.
5. Meminta persetujuan **kedua** sebelum menjalankan `ml/train.py`.

---

## 10. Checklist persetujuan dataset

Isi dan setujui sebelum data dimasukkan:

- [ ] Sumber dataset: ______________________
- [ ] Lisensi / izin penggunaan: ______________________
- [ ] Jumlah baris & kolom: ______________________
- [ ] Nama kolom target: ______________________
- [ ] Nilai kelas target: ______________________
- [ ] Ada data pribadi? (ya/tidak): ______________________
- [ ] Jalur penyesuaian: A / B
- [ ] Izin menjalankan EDA: ya / tidak
- [ ] Izin melatih model setelah EDA: ya / tidak

---

## 11. Batasan yang dinyatakan sejak awal

- Hasil klasifikasi adalah **skrining awal**, bukan diagnosis.
- Performa model hanya berlaku sebaik dataset yang dipakai.
- Rekomendasi tetap deterministik dari aturan, bukan keluaran model bahasa.
- Tidak ada angka akurasi di dokumen ini karena model belum dilatih.
