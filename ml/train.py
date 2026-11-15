"""Skrip pelatihan model Somnipathy Lab.

BELUM DIJALANKAN karena dataset belum tersedia. Skrip ini tidak berisi
angka akurasi apa pun; semua metrik dihasilkan dari dataset Anda sendiri.

Contoh pemakaian setelah dataset tersedia:

    py -m ml.train --csv ml/data/raw/dataset_tidur.csv

Hasil:
    ml/artifacts/model_pipeline.pkl
    ml/artifacts/model_meta.json

Catatan: ganti daftar fitur di ml/feature_schema.json agar sesuai dengan
nama kolom dataset. Skrip akan berhenti dengan pesan jelas bila ada kolom
yang tidak cocok.
"""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.preprocessing import numeric_and_categorical, split_xy
from ml.schema import get_target, load_schema

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = BASE_DIR / "ml" / "artifacts"


def build_pipeline(categorical: list[str], numeric: list[str]) -> Pipeline:
    """Pipeline lengkap: praproses + classifier (disimpan sebagai satu objek)."""
    numeric_steps = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_steps = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_steps, numeric),
            ("cat", categorical_steps, categorical),
        ],
        remainder="drop",
    )

    classifier = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )

    return Pipeline(steps=[("preprocessor", preprocessor), ("classifier", classifier)])


def train(csv_path: Path, output_dir: Path, test_size: float = 0.2) -> dict:
    schema = load_schema()
    target_column = get_target(schema).get("column")

    if not csv_path.exists():
        raise SystemExit(f"Dataset tidak ditemukan: {csv_path}")

    dataframe = pd.read_csv(csv_path)
    names = [field["name"] for field in schema.get("fields", [])]
    missing = [name for name in names + [target_column] if name not in dataframe.columns]

    if missing:
        raise SystemExit(
            "Dataset tidak cocok dengan skema fitur.\n"
            f"Kolom yang hilang: {', '.join(missing)}\n"
            "Perbaiki ml/feature_schema.json atau sesuaikan nama kolom dataset."
        )

    # Buang baris tanpa label
    dataframe = dataframe.dropna(subset=[target_column]).reset_index(drop=True)

    x_data, y_data = split_xy(dataframe, schema)
    numeric, categorical = numeric_and_categorical(schema)

    class_counts = y_data.value_counts()
    if len(class_counts) < 2:
        raise SystemExit("Dataset hanya memiliki satu kelas; tidak bisa melatih model.")
    if class_counts.min() < 2:
        raise SystemExit(
            "Ada kelas dengan kurang dari 2 contoh. Tambah data sebelum melatih."
        )

    x_train, x_test, y_train, y_test = train_test_split(
        x_data,
        y_data,
        test_size=test_size,
        random_state=42,
        stratify=y_data,
    )

    pipeline = build_pipeline(categorical=categorical, numeric=numeric)
    pipeline.fit(x_train, y_train)

    y_pred = pipeline.predict(x_test)
    labels = sorted(y_data.unique().tolist())

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "classification_report": classification_report(
            y_test, y_pred, output_dict=True, zero_division=0
        ),
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=labels).tolist(),
        "confusion_matrix_labels": [str(item) for item in labels],
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
    }

    model_version = "v" + datetime.now().strftime("%Y%m%d-%H%M")

    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output_dir / "model_pipeline.pkl")

    meta = {
        "model_version": model_version,
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": csv_path.name,
        "dataset_rows": int(len(dataframe)),
        "features": [field["name"] for field in schema.get("fields", [])],
        "target": target_column,
        "classes": list(pipeline.classes_),
        "metrics": metrics,
        "environment": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": __import__("numpy").__version__,
        },
        "schema_version": schema.get("version"),
        "notes": (
            "Metrik di atas dihitung dari data uji yang dipisahkan secara acak "
            "dengan stratifikasi. Bukan hasil dari data latih."
        ),
    }

    with (output_dir / "model_meta.json").open("w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2, ensure_ascii=False)

    print(f"Model tersimpan di {output_dir / 'model_pipeline.pkl'}")
    print(f"Akurasi data uji: {metrics['accuracy']:.4f}")
    print("Laporan lengkap: ml/artifacts/model_meta.json")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Latih model klasifikasi Somnipathy Lab")
    parser.add_argument("--csv", required=True, help="Path dataset pelatihan (CSV)")
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT), help="Folder artefak model")
    parser.add_argument("--test-size", type=float, default=0.2, help="Proporsi data uji")
    args = parser.parse_args()

    train(Path(args.csv), Path(args.out), test_size=args.test_size)


if __name__ == "__main__":
    main()
