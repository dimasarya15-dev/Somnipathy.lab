"""Endpoint riwayat deteksi (hanya untuk sesi pengunjung itu sendiri)."""

from __future__ import annotations

from flask import Blueprint, request

from backend.extensions import db
from backend.models.detection import Detection
from backend.utils.responses import success
from backend.utils.session import get_session_token

bp = Blueprint("history", __name__)


@bp.get("/detections")
def list_detections():
    token = get_session_token()
    page = _positive_int(request.args.get("page"), default=1)
    per_page = min(_positive_int(request.args.get("per_page"), default=10), 50)

    pagination = (
        Detection.query.filter_by(session_token=token)
        .order_by(Detection.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return success(
        {
            "items": [item.to_dict() for item in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
            "total": pagination.total,
        }
    )


@bp.get("/detections/<int:detection_id>")
def get_detection(detection_id: int):
    token = get_session_token()
    detection = db.session.get(Detection, detection_id)

    # Deteksi milik sesi lain diperlakukan sebagai "tidak ditemukan"
    if detection is None or detection.session_token != token:
        from backend.utils.errors import NotFoundError

        raise NotFoundError("Hasil deteksi tidak ditemukan.")

    return success(detection.to_dict(include_input=True))


def _positive_int(raw_value, default: int) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    return max(value, 1)
