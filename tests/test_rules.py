"""Pengujian mesin aturan rekomendasi (tanpa database, tanpa model)."""

from __future__ import annotations

from backend.services import recommendation_service

BASE_FACTS = {
    "age": 27,
    "gender": "male",
    "sleep_duration": 7.5,
    "sleep_quality": 7,
    "physical_activity_minutes": 45,
    "stress_level": 4,
    "bmi": 23.0,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "heart_rate": 70,
    "daily_steps": 8000,
    "prediction_label": "None",
    "confidence": 0.9,
    "is_confident": True,
}


def rule_ids(recommendations):
    return [item["rule_id"] for item in recommendations]


def test_kondisi_normal_tidak_menghasilkan_rekomendasi():
    assert recommendation_service.generate(BASE_FACTS) == []


def test_sleep_apnea_keyakinan_tinggi_memicu_rujukan_medis():
    recs = recommendation_service.generate(
        {**BASE_FACTS, "prediction_label": "Sleep Apnea"}
    )

    assert "APN-01" in rule_ids(recs)
    assert recs[0]["category"] == "medical_referral"
    assert recs[0]["severity"] == "high"


def test_kategori_sama_hanya_muncul_sekali():
    recs = recommendation_service.generate(
        {**BASE_FACTS, "prediction_label": "Sleep Apnea"}
    )

    medical = [item for item in recs if item["category"] == "medical_referral"]
    assert len(medical) == 1


def test_keyakinan_rendah_menambah_rekomendasi_kualitas_data():
    recs = recommendation_service.generate(
        {**BASE_FACTS, "is_confident": False, "confidence": 0.4}
    )

    assert "LOWCONF" in rule_ids(recs)


def test_durasi_tidur_pendek_memicu_aturan_durasi():
    recs = recommendation_service.generate({**BASE_FACTS, "sleep_duration": 5})

    assert "DUR-01" in rule_ids(recs)


def test_tekanan_darah_tinggi_memicu_aturan_bp():
    recs = recommendation_service.generate(
        {**BASE_FACTS, "systolic_bp": 150, "diastolic_bp": 95}
    )

    assert "BP-01" in rule_ids(recs)


def test_hasil_dibatasi_maksimal_lima():
    recs = recommendation_service.generate(
        {
            **BASE_FACTS,
            "sleep_duration": 4,
            "sleep_quality": 2,
            "stress_level": 10,
            "bmi": 35,
            "systolic_bp": 160,
            "diastolic_bp": 100,
            "daily_steps": 1000,
            "physical_activity_minutes": 0,
            "heart_rate": 110,
            "prediction_label": "Sleep Apnea",
            "is_confident": False,
            "confidence": 0.3,
        }
    )

    assert 1 <= len(recs) <= 5


def test_urutan_prioritas_severity():
    recs = recommendation_service.generate(
        {
            **BASE_FACTS,
            "prediction_label": "Sleep Apnea",
            "sleep_duration": 5,
            "stress_level": 9,
        }
    )

    severities = [item["severity"] for item in recs]
    ranked = {"high": 0, "medium": 1, "low": 2, "info": 3}
    scores = [ranked[item] for item in severities]
    assert scores == sorted(scores)


def test_disclaimer_tersedia():
    assert "bukan diagnosis medis" in recommendation_service.get_disclaimer().lower()
