# Rencana EDA — Somnipathy Lab

**Status:** rencana saja. Belum dijalankan karena dataset belum tersedia.
**Sifat:** read-only terhadap data mentah; hasil olahan ditulis ke `ml/data/processed/`.

EDA (Exploratory Data Analysis) adalah pemeriksaan data sebelum training.
Tujuannya memastikan data layak dipakai, bukan sekadar "bisa dibaca pandas".

---

## 0. Output yang diharapkan

| Artefak | Isi |
|---|---|
| `docs/EDA_REPORT.md` | Laporan temuan + keputusan |
| `ml/data/processed/cleaned_v1.csv` | Data bersih (setelah keputusan EDA) |
| `ml/data/processed/eda_summary.json` | Ringkasan angka untuk lampiran |
| `ml/data/raw/CHECKSUM.txt` | SHA-256 berkas mentah |
| Gambar (opsional) | Distribusi target, korelasi, boxplot per fitur |

Belum ada file di atas yang dibuat sekarang.

---

## 1. Integritas berkas

```python
import hashlib, pandas as pd

path = "ml/data/raw/sleep_dataset_v1.csv"

# checksum
print(hashlib.sha256(open(path, "rb").read()).hexdigest())

# deteksi pemisah otomatis
df = pd.read_csv(path, sep=None, engine="python")
print(df.shape)
print(df.dtypes)
print(df.head())
```

Periksa:
- jumlah baris/kolom sesuai deskripsi sumber;
- encoding benar (tidak ada karakter aneh seperti `Ã©`);
- tipe data masuk akal (angka tidak terbaca sebagai teks);
- tidak ada kolom tanpa nama (`Unnamed: 0`).

---

## 2. Kamus data

Buat tabel pemetaan **kolom dataset → field sistem**:

| Kolom dataset | Field sistem | Tipe | Satuan | Catatan |
|---|---|---|---|---|
| … | … | … | … | … |

Keputusan yang harus eksplisit:
- kolom mana yang dipakai, diubah, atau dibuang;
- alasan membuang kolom;
- konversi satuan (mis. tinggi cm → m untuk IMT).

---

## 3. Nilai kosong

```python
missing = df.isna().mean().sort_values(ascending=False)
print(missing[missing > 0])
```

| Temuan | Tindakan |
|---|---|
| 0% | tidak ada tindakan |
| ≤ 5% pada fitur kunci | imputasi median (numerik) / modus (kategori), dicatat |
| > 5% | investigasi penyebab; pertimbangkan buang fitur |
| > 30% | fitur tidak layak dipakai |

Periksa juga nilai yang **disamarkan** sebagai angka: `0`, `-1`, `999`, string
kosong, `"unknown"`.

---

## 4. Duplikasi

```python
print("duplikat penuh :", df.duplicated().sum())

fitur = [c for c in df.columns if c not in {"Person ID", "id", "subject_id"}]
print("duplikat fitur :", df.duplicated(subset=fitur).sum())

if "Person ID" in df.columns:
    print("ID ganda       :", df["Person ID"].duplicated().sum())
```

| Temuan | Tindakan |
|---|---|
| Duplikat penuh | hapus, catat jumlahnya |
| Duplikat pada fitur (ID beda) | curigai entri ganda; putuskan sebelum split |
| ID ganda | periksa apakah subjek yang sama diukur berkali-kali → pakai group split |

**Aturan keras:** deduplikasi dilakukan **sebelum** pembagian data latih/uji.

---

## 5. Distribusi target

```python
target = "sleep_disorder"
print(df[target].value_counts())
print(df[target].value_counts(normalize=True).round(3))
```

Yang dinilai:
- jumlah dan proporsi tiap kelas;
- kelas dengan < 10% → tandai sebagai minoritas;
- label tak dikenal / salah ketik (`"Insomnia "`, `"insomnia"`, `NaN`);
- apakah kelas `None` benar-benar "sehat" atau hanya "tidak diperiksa".

Jika ada baris berlabel kosong: **jangan** diisi dengan tebakan. Buang atau
dokumentasikan.

---

## 6. Statistik deskriptif dan validitas fisiologis

```python
print(df.describe().T)
```

| Fitur | Pemeriksaan | Nilai mustahil |
|---|---|---|
| `age` | rentang & sebaran | < 0, > 110 |
| `sleep_duration` | histogram | 0 atau > 24 jam |
| `sleep_quality` | nilai unik | di luar 1–10 |
| `stress_level` | nilai unik | di luar 1–10 |
| `bmi` | histogram | < 10, > 70 |
| `systolic_bp` / `diastolic_bp` | sistolik > diastolik | tertukar, 0 |
| `heart_rate` | histogram | 0 atau > 220 |
| `daily_steps` | histogram | negatif |
| `gender` | `value_counts()` | kategori tak dikenal |

Deteksi outlier dengan IQR:

```python
q1, q3 = df["bmi"].quantile([0.25, 0.75])
iqr = q3 - q1
outlier = df[(df["bmi"] < q1 - 1.5*iqr) | (df["bmi"] > q3 + 1.5*iqr)]
print(len(outlier))
```

**Jangan langsung menghapus outlier.** Nilai ekstrem bisa valid secara medis.
Bedakan "mustahil" (hapus) dan "ekstrem tapi mungkin" (pertahankan, beri catatan).

---

## 7. Hubungan fitur dengan target

Numerik vs target kategorikal:

```python
df.groupby(target)[["sleep_duration", "bmi", "stress_level"]].agg(["mean", "median", "std"])
```

Korelasi antar-fitur numerik:

```python
print(df.select_dtypes("number").corr(method="spearman").round(2))
```

Kategori vs target:

```python
from scipy.stats import chi2_contingency
table = pd.crosstab(df["gender"], df[target])
print(table)
print(chi2_contingency(table))
```

Yang dicari:
- fitur dengan sinyal jelas (mis. durasi tidur vs insomnia);
- fitur hampir konstan → kandidat dibuang;
- pasangan fitur sangat berkorelasi (> 0.9) → pertimbangkan salah satu;
- kombinasi kategori yang sangat sedikit (mis. `male` + apnea hanya 3 baris).

---

## 8. Pemeriksaan kebocoran (leakage) dan label sirkular

Ini bagian yang paling sering dilewatkan.

| Pemeriksaan | Cara | Tindakan bila positif |
|---|---|---|
| Kolom turunan label | nama kolom mirip target, mis. `diagnosis_code`, `treatment` | buang |
| Label dibuat dari fitur | tanyakan ke sumber: apakah label = aturan atas fitur yang sama? | hentikan, desain ulang |
| ID sebagai fitur | kolom `Person ID` ikut masuk model | buang |
| Urutan baris | data terurut berdasarkan label | acak sebelum split |
| Duplikat antar-split | cek irisan setelah split | deduplikasi dulu |

Uji cepat: latih model **sederhana** pada data latih lalu lihat apakah
akurasinya "terlalu sempurna" (mis. 0.99+). Itu tanda leakage, bukan prestasi.

---

## 9. Strategi pembagian data

| Kondisi | Metode |
|---|---|
| Data independen, kelas seimbang | `train_test_split(stratify=y, test_size=0.2, random_state=42)` |
| Kelas tidak seimbang | sama, wajib `stratify=y` |
| Ada beberapa baris per subjek | `GroupShuffleSplit` berdasarkan ID subjek |
| Data time-series | split kronologis, bukan acak |

Validasi model: **Stratified K-Fold (5–10 fold)** pada data latih, dan data uji
disentuh **sekali** di akhir.

---

## 10. Keputusan praproses

Mengikuti pipeline yang sudah ada (`ml/train.py`):

| Jenis | Perlakuan | Alasan |
|---|---|---|
| Numerik | `SimpleImputer(median)` + `StandardScaler` | tahan outlier, skala seragam |
| Kategori | `SimpleImputer(most_frequent)` + `OneHotEncoder(handle_unknown="ignore")` | kategori baru saat produksi tidak error |

Catatan penting: seluruh praproses berada **di dalam** `Pipeline`, sehingga
saat prediksi di web, perlakuan otomatis sama dengan saat latihan
(tidak ada *train/serve skew*).

---

## 11. Rencana penanganan ketidakseimbangan

Urutan yang direkomendasikan (bertahap, bukan sekaligus):

1. Ukur dulu: proporsi kelas, macro-F1, recall per kelas.
2. Pakai `class_weight="balanced"` (sudah aktif).
3. Sesuaikan ambang keputusan bila kelas minoritas penting (mis. apnea).
4. Baru pertimbangkan resampling, dan **hanya pada data latih**.

Resampling menambah dependensi (`imbalanced-learn`) → butuh persetujuan.

---

## 12. Gerbang keputusan sebelum training

Training hanya dijalankan jika semua poin ini terpenuhi:

- [ ] Sumber dan lisensi dataset jelas
- [ ] Checksum tercatat
- [ ] Tidak ada data pribadi
- [ ] Duplikasi sudah ditangani
- [ ] Distribusi kelas dilaporkan, termasuk kelas minoritas
- [ ] Nilai mustahil sudah dibersihkan
- [ ] Tidak ada kolom bocor/label sirkular
- [ ] Pemetaan kolom → `feature_schema.json` disetujui
- [ ] Strategi split ditentukan
- [ ] Pemilik proyek menyetujui pelatihan

Jika salah satu belum terpenuhi, training **ditunda**.

---

## 13. Format laporan EDA

Laporan akhir akan memuat:

1. Ringkasan dataset (sumber, jumlah baris/kolom, tanggal akses)
2. Tabel kamus data
3. Temuan nilai kosong & duplikasi
4. Distribusi target + grafik
5. Statistik tiap fitur + daftar anomali
6. Hubungan fitur–target
7. Daftar risiko yang ditemukan
8. Keputusan pembersihan (beserta alasannya)
9. Batasan yang harus ditulis di UI/README
10. Rekomendasi apakah dataset layak dilatih

Tidak ada angka akurasi pada tahap ini. Akurasi baru muncul setelah training
dan evaluasi pada data uji.
