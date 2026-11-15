"""Endpoint utama: POST /api/predict."""

from __future__ import annotations

from flask import Blueprint, request

from backend.services import detection_service
from backend.utils.responses import error, success
from backend.utils.session import get_session_token

bp = Blueprint("predict", __name__)


@bp.post("/predict")
def predict():
    """Terima jawaban pengguna, jalankan ML + aturan, simpan, kembalikan hasil."""
    payload = request.get_json(silent=True)

    if payload is None:
        return error(
            "Kirim data dalam format JSON (Content-Type: application/json).",
            status=415,
            code="invalid_content_type",
        )

    result = detection_service.run(payload, get_session_token())
    return success(result, message="Analisis berhasil.")
