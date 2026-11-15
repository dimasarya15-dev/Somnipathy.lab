"""Validasi input pengguna berdasarkan skema fitur.

Skema fitur ada di ml/feature_schema.json, sehingga bila dataset berubah
(cukup ganti daftar fitur), kode validasi ini TIDAK perlu diubah.
"""

from __future__ import annotations

from backend.utils.errors import ValidationError
from ml.schema import get_schema

NUMERIC_TYPES = {"integer", "float"}


def validate_payload(payload, schema: dict | None = None) -> dict:
    """Periksa dan ubah input menjadi tipe data yang benar.

    Mengembalikan dict bersih siap dipakai model.
    Melempar ValidationError berisi pesan per-field bila ada masalah.
    """
    schema = schema or get_schema()

    if not isinstance(payload, dict):
        raise ValidationError(
            "Format data tidak dikenali. Kirim objek JSON.",
            errors={"_": "payload harus berupa objek JSON"},
        )

    cleaned: dict = {}
    errors: dict[str, str] = {}

    for field in schema.get("fields", []):
        name = field["name"]
        label = field.get("label", name)
        raw_value = payload.get(name)

        if _is_blank(raw_value):
            if field.get("required", True):
                errors[name] = f"{label} wajib diisi."
            else:
                cleaned[name] = None
            continue

        try:
            cleaned[name] = _coerce_value(raw_value, field)
        except ValueError as exc:
            errors[name] = str(exc)

    if errors:
        raise ValidationError("Beberapa isian belum valid.", errors=errors)

    return cleaned


def _is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _coerce_value(raw_value, field: dict):
    kind = field.get("type", "text")
    label = field.get("label", field["name"])

    if kind == "integer":
        try:
            value = int(float(str(raw_value).replace(",", ".")))
        except (TypeError, ValueError):
            raise ValueError(f"{label} harus berupa angka bulat.") from None
        _check_range(value, field, label)
        return value

    if kind == "float":
        try:
            value = float(str(raw_value).replace(",", "."))
        except (TypeError, ValueError):
            raise ValueError(f"{label} harus berupa angka.") from None
        decimals = int(field.get("decimals", 2))
        value = round(value, decimals)
        _check_range(value, field, label)
        return value

    if kind in {"select", "text"}:
        value = str(raw_value).strip()
        if kind == "select":
            allowed = [str(option.get("value")) for option in field.get("options", [])]
            if allowed and value not in allowed:
                raise ValueError(f"Pilihan {label} tidak dikenali.")
        max_length = field.get("max_length")
        if max_length and len(value) > int(max_length):
            raise ValueError(f"{label} terlalu panjang (maksimal {max_length} karakter).")
        return value

    raise ValueError(f"Tipe field '{kind}' tidak didukung untuk {label}.")


def _check_range(value, field: dict, label: str) -> None:
    minimum = field.get("min")
    maximum = field.get("max")

    if minimum is not None and value < minimum:
        raise ValueError(f"{label} minimal {minimum}.")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} maksimal {maximum}.")
