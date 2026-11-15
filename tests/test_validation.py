"""Pengujian validasi input."""

from __future__ import annotations

import pytest

from backend.services.validation_service import validate_payload
from backend.utils.errors import ValidationError

VALID_PAYLOAD = {
    "age": 27,
    "gender": "male",
    "sleep_duration": 6.5,
    "sleep_quality": 6,
    "physical_activity_minutes": 45,
    "stress_level": 5,
    "bmi": 24.2,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "heart_rate": 72,
    "daily_steps": 8000,
}


def test_payload_valid_dibersihkan():
    result = validate_payload(VALID_PAYLOAD)

    assert result["age"] == 27
    assert result["gender"] == "male"
    assert isinstance(result["sleep_duration"], float)
    assert result["sleep_duration"] == 6.5


def test_field_wajib_yang_kosong_dilaporkan():
    payload = dict(VALID_PAYLOAD)
    payload.pop("age")

    with pytest.raises(ValidationError) as info:
        validate_payload(payload)

    assert "age" in info.value.errors
    assert "wajib diisi" in info.value.errors["age"].lower()


def test_nilai_di_luar_rentang_ditolak():
    payload = {**VALID_PAYLOAD, "stress_level": 99}

    with pytest.raises(ValidationError) as info:
        validate_payload(payload)

    assert "stress_level" in info.value.errors


def test_pilihan_kategori_tidak_dikenal_ditolak():
    payload = {**VALID_PAYLOAD, "gender": "lainnya"}

    with pytest.raises(ValidationError) as info:
        validate_payload(payload)

    assert "gender" in info.value.errors


def test_koma_desimal_diterima():
    payload = {**VALID_PAYLOAD, "sleep_duration": "6,5"}

    assert validate_payload(payload)["sleep_duration"] == 6.5


def test_bukan_objek_json_ditolak():
    with pytest.raises(ValidationError) as info:
        validate_payload(["bukan", "objek"])

    assert "_" in info.value.errors
