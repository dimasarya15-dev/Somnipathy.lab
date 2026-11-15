"""Penyusunan data untuk prediksi dan pelatihan.

PENTING: urutan kolom harus selalu sama antara saat melatih dan saat
memprediksi. Karena itu urutan diambil dari ml/feature_schema.json.
"""

from __future__ import annotations

from typing import Any

from ml.schema import get_fields, get_schema, get_target

NUMERIC_TYPES = {"integer", "float"}
CATEGORICAL_TYPES = {"select", "text"}


def build_input_frame(payload: dict, schema: dict | None = None):
    """Ubah satu payload hasil validasi menjadi DataFrame satu baris."""
    import pandas as pd  # import lazy: hanya dibutuhkan saat memprediksi

    schema = schema or get_schema()
    fields = get_fields(schema)
    columns = [field["name"] for field in fields]
    row = {field["name"]: payload.get(field["name"]) for field in fields}

    return pd.DataFrame([row], columns=columns)


def split_xy(dataframe, schema: dict | None = None):
    """Pisahkan kolom fitur (X) dan kolom target (y) dari DataFrame dataset."""
    schema = schema or get_schema()
    target_column = get_target(schema).get("column")

    if not target_column:
        raise ValueError("Kolom target belum didefinisikan di feature_schema.json.")

    feature_names = [field["name"] for field in get_fields(schema)]
    missing = [name for name in feature_names + [target_column] if name not in dataframe.columns]
    if missing:
        raise ValueError(
            "Kolom berikut tidak ditemukan di dataset: " + ", ".join(missing)
        )

    return dataframe[feature_names].copy(), dataframe[target_column].copy()


def numeric_and_categorical(schema: dict | None = None) -> tuple[list[str], list[str]]:
    """Kelompokkan nama fitur berdasarkan tipe untuk ColumnTransformer."""
    schema = schema or get_schema()
    numeric = [
        field["name"] for field in get_fields(schema)
        if field.get("type") in NUMERIC_TYPES
    ]
    categorical = [
        field["name"] for field in get_fields(schema)
        if field.get("type") in CATEGORICAL_TYPES
    ]
    return numeric, categorical


def missing_value_columns(dataframe, schema: dict | None = None) -> dict[str, int]:
    """Ringkasan jumlah nilai kosong per kolom fitur (untuk laporan EDA)."""
    schema = schema or get_schema()
    names = [field["name"] for field in get_fields(schema)]
    return {
        name: int(dataframe[name].isna().sum())
        for name in names
        if name in dataframe.columns
    }
