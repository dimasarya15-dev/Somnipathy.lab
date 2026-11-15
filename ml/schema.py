"""Pembaca skema fitur (ml/feature_schema.json).

Modul ini sengaja hanya memakai pustaka standar (json, pathlib) agar bisa
diimpor oleh aplikasi web tanpa membutuhkan pandas/scikit-learn.
"""

from __future__ import annotations

import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().with_name("feature_schema.json")

_cache: dict[str, dict] = {}


def load_schema(path: str | Path | None = None, force: bool = False) -> dict:
    """Muat skema fitur (di-cache agar tidak membaca file berulang)."""
    schema_path = Path(path) if path else SCHEMA_PATH
    key = str(schema_path)

    if not force and key in _cache:
        return _cache[key]

    with schema_path.open(encoding="utf-8") as handle:
        schema = json.load(handle)

    schema.setdefault("fields", [])
    schema.setdefault("target", {})
    _cache[key] = schema
    return schema


def get_schema() -> dict:
    return load_schema()


def reload_schema() -> dict:
    return load_schema(force=True)


def get_fields(schema: dict | None = None) -> list[dict]:
    return list((schema or get_schema()).get("fields", []))


def get_feature_names(schema: dict | None = None) -> list[str]:
    return [field["name"] for field in get_fields(schema)]


def get_target(schema: dict | None = None) -> dict:
    return dict((schema or get_schema()).get("target", {}))


def get_classes(schema: dict | None = None) -> list[str]:
    return list(get_target(schema).get("classes", []))


def class_label(value: str | None, schema: dict | None = None) -> str:
    """Nama kelas yang ramah dibaca (bahasa Indonesia)."""
    if value is None:
        return "-"
    labels = get_target(schema).get("labels", {}) or {}
    return labels.get(value, value)
