"""Helper kecil untuk menampilkan data di template."""

from __future__ import annotations

BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

SEVERITY_LABELS = {
    "high": "Prioritas tinggi",
    "medium": "Perlu perhatian",
    "low": "Saran",
    "info": "Informasi",
}


def severity_label(value: str | None) -> str:
    """Label bahasa Indonesia untuk tingkat kepentingan rekomendasi."""
    if not value:
        return "Informasi"
    return SEVERITY_LABELS.get(value, str(value).capitalize())


def format_datetime(value, with_time: bool = True) -> str:
    """Format tanggal gaya Indonesia, mis. '15 November 2026, 18:20'."""
    if not value:
        return "-"
    text = f"{value.day} {BULAN[value.month - 1]} {value.year}"
    if with_time:
        text += f", {value:%H:%M}"
    return text


def describe_inputs(detection, schema: dict) -> list[dict]:
    """Ubah data mentah deteksi menjadi baris siap tampil (label + nilai)."""
    rows: list[dict] = []
    raw_data = detection.input_data or {}

    for field in schema.get("fields", []):
        raw_value = raw_data.get(field["name"])
        if raw_value is None:
            continue

        value = raw_value
        if field.get("type") == "select":
            for option in field.get("options", []):
                if str(option.get("value")) == str(raw_value):
                    value = option.get("label", raw_value)
                    break

        rows.append(
            {
                "label": field.get("label", field["name"]),
                "value": value,
                "unit": field.get("unit"),
            }
        )

    return rows
