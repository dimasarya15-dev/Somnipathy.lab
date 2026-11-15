"""Orkestrasi satu kali deteksi.

Urutan: validasi -> prediksi ML -> rekomendasi aturan -> simpan database.
"""

from __future__ import annotations

import logging
from datetime import datetime

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from backend.extensions import db
from backend.models.detection import Detection, DetectionRecommendation
from backend.services import ml_service, recommendation_service, validation_service
from ml.schema import class_label, get_schema

logger = logging.getLogger(__name__)


def run(payload, session_token: str) -> dict:
    """Jalankan seluruh alur deteksi dan kembalikan hasil siap kirim."""
    schema = get_schema()

    # 1. Validasi (melempar ValidationError -> HTTP 400)
    cleaned = validation_service.validate_payload(payload, schema)

    # 2. Klasifikasi (melempar ModelNotReadyError -> HTTP 503 bila belum ada)
    prediction = ml_service.predict(cleaned)

    # 3. Rekomendasi berbasis aturan
    facts = {
        **cleaned,
        "prediction_label": prediction["label"],
        "confidence": prediction["confidence"],
        "is_confident": prediction["is_confident"],
    }
    recommendations = recommendation_service.generate(facts)

    # 4. Simpan ke database (kegagalan DB tidak menghapus hasil analisis)
    detection = Detection(
        session_token=session_token,
        input_data=cleaned,
        prediction=prediction["label"],
        confidence=prediction["confidence"],
        probabilities=prediction["probabilities"],
        model_version=prediction["model_version"],
    )

    saved = True
    warning = None
    try:
        db.session.add(detection)
        db.session.flush()

        for item in recommendations:
            db.session.add(
                DetectionRecommendation(
                    detection_id=detection.id,
                    rule_id=item["rule_id"],
                    category=item["category"],
                    severity=item["severity"],
                    title=item["title"],
                    message=item["message"],
                )
            )
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        saved = False
        warning = (
            "Hasil analisis berhasil dibuat, tetapi gagal disimpan ke database. "
            "Periksa koneksi MySQL."
        )
        logger.exception("Gagal menyimpan deteksi: %s", exc)

    created_at = detection.created_at or datetime.now()

    return {
        "detection_id": detection.id if saved else None,
        "saved": saved,
        "warning": warning,
        "prediction": {
            "label": prediction["label"],
            "label_display": class_label(prediction["label"], schema),
            "confidence": prediction["confidence"],
            "probabilities": prediction["probabilities"],
            "threshold": prediction["threshold"],
            "is_confident": prediction["is_confident"],
        },
        "recommendations": recommendations,
        "disclaimer": recommendation_service.get_disclaimer(),
        "model_version": prediction["model_version"],
        "schema_version": schema.get("version"),
        "created_at": created_at.isoformat(timespec="seconds"),
    }
