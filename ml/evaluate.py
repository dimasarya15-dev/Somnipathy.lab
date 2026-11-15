"""Evaluasi model yang sudah tersimpan terhadap dataset uji.

Contoh:
    py -m ml.evaluate --csv ml/data/raw/dataset_tidur.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from ml.preprocessing import split_xy
from ml.schema import get_target, load_schema

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ARTIFACT_DIR = BASE_DIR / "ml" / "artifacts"


def evaluate(csv_path: Path, artifact_dir: Path) -> dict:
    schema = load_schema()
    target_column = get_target(schema).get("column")
    pipeline_path = artifact_dir / "model_pipeline.pkl"

    if not pipeline_path.exists():
        raise SystemExit(
            f"Model belum ada: {pipeline_path}\n"
            "Latih model terlebih dahulu dengan: py -m ml.train --csv <dataset.csv>"
        )
    if not csv_path.exists():
        raise SystemExit(f"Dataset tidak ditemukan: {csv_path}")

    dataframe = pd.read_csv(csv_path).dropna(subset=[target_column])
    x_data, y_data = split_xy(dataframe, schema)
    pipeline = joblib.load(pipeline_path)

    y_pred = pipeline.predict(x_data)
    labels = sorted(y_data.unique().tolist())

    report = {
        "accuracy": round(float(accuracy_score(y_data, y_pred)), 4),
        "classification_report": classification_report(
            y_data, y_pred, output_dict=True, zero_division=0
        ),
        "confusion_matrix": confusion_matrix(y_data, y_pred, labels=labels).tolist(),
        "confusion_matrix_labels": [str(item) for item in labels],
        "rows": int(len(dataframe)),
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluasi model Somnipathy Lab")
    parser.add_argument("--csv", required=True, help="Path dataset evaluasi (CSV)")
    parser.add_argument("--artifacts", default=str(DEFAULT_ARTIFACT_DIR))
    args = parser.parse_args()

    evaluate(Path(args.csv), Path(args.artifacts))


if __name__ == "__main__":
    main()
