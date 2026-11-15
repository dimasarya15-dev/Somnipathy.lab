"""Pengujian endpoint HTTP.

Catatan: model belum dilatih, jadi /api/predict diharapkan membalas 503.
Tes ini memastikan sistem TIDAK pernah mengembalikan hasil palsu.
"""

from __future__ import annotations

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


def test_halaman_beranda_bisa_dibuka(client):
    response = client.get("/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Somnipathy" in body


def test_halaman_deteksi_menampilkan_form(client):
    response = client.get("/deteksi")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="form-deteksi"' in body
    assert "Durasi tidur" in body


def test_halaman_riwayat_bisa_dibuka(client):
    response = client.get("/riwayat")

    assert response.status_code == 200
    assert "Riwayat deteksi" in response.get_data(as_text=True)


def test_health_endpoint(client):
    response = client.get("/api/health")
    body = response.get_json()

    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["data"]["database"]["connected"] is True
    assert body["data"]["model"]["ready"] is False


def test_model_info_jujur_soal_kesiapan(client):
    body = client.get("/api/model-info").get_json()

    assert body["data"]["ready"] is False
    assert body["data"]["reason"]
    assert body["data"]["features"]


def test_predict_menolak_bukan_json(client):
    response = client.post(
        "/api/predict", data="bukan json", content_type="text/plain"
    )

    assert response.status_code == 415


def test_predict_melaporkan_error_validasi(client):
    response = client.post("/api/predict", json={"age": 999})
    body = response.get_json()

    assert response.status_code == 400
    assert body["status"] == "error"
    assert "age" in body["errors"]


def test_predict_tanpa_model_membalas_503(client):
    response = client.post("/api/predict", json=VALID_PAYLOAD)
    body = response.get_json()

    assert response.status_code == 503
    assert body["code"] == "model_not_ready"
    assert "Model" in body["message"]


def test_riwayat_awalnya_kosong(client):
    body = client.get("/api/detections").get_json()

    assert body["data"]["items"] == []
    assert body["data"]["total"] == 0


def test_api_tidak_dikenal_membalas_json_404(client):
    response = client.get("/api/tidak-ada")

    assert response.status_code == 404
    assert response.is_json


def test_halaman_tidak_dikenal_membalas_html_404(client):
    response = client.get("/halaman-tidak-ada")

    assert response.status_code == 404
    assert "text/html" in response.headers["Content-Type"]


def _buat_deteksi(app, token="sesi-uji"):
    """Fixture data uji (bukan hasil model sungguhan)."""
    from backend.extensions import db
    from backend.models.detection import Detection, DetectionRecommendation

    detection = Detection(
        session_token=token,
        input_data={
            "age": 27,
            "gender": "male",
            "sleep_duration": 5.0,
            "sleep_quality": 4,
            "physical_activity_minutes": 20,
            "stress_level": 8,
            "bmi": 27.0,
            "systolic_bp": 125,
            "diastolic_bp": 82,
            "heart_rate": 78,
            "daily_steps": 3000,
        },
        prediction="Insomnia",
        confidence=0.82,
        probabilities={"None": 0.1, "Insomnia": 0.82, "Sleep Apnea": 0.08},
        model_version="uji-coba",
    )
    db.session.add(detection)
    db.session.flush()

    db.session.add(
        DetectionRecommendation(
            detection_id=detection.id,
            rule_id="INS-01",
            category="insomnia",
            severity="medium",
            title="Kelola pola tidur",
            message="Pesan pengujian.",
        )
    )
    db.session.commit()
    return detection.id


def test_halaman_hasil_merender_rekomendasi(client, app):
    with app.app_context():
        detection_id = _buat_deteksi(app)

    with client.session_transaction() as session_data:
        session_data["sid"] = "sesi-uji"

    response = client.get(f"/hasil/{detection_id}")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Insomnia" in body
    assert "INS-01" in body
    assert "bukan diagnosis medis" in body.lower()


def test_hasil_sesi_lain_tidak_bisa_dibuka(client, app):
    with app.app_context():
        detection_id = _buat_deteksi(app, token="milik-orang-lain")

    with client.session_transaction() as session_data:
        session_data["sid"] = "sesi-saya"

    assert client.get(f"/hasil/{detection_id}").status_code == 404
