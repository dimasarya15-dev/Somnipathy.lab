"""Blueprint untuk halaman HTML (bukan API)."""

from __future__ import annotations

from flask import Blueprint, abort, render_template

from backend.extensions import db
from backend.models.detection import Detection
from backend.services import ml_service
from backend.utils.display import describe_inputs
from backend.utils.session import get_session_token
from ml.schema import get_schema

bp = Blueprint("web", __name__)


@bp.get("/")
def index():
    return render_template("index.html", model=ml_service.status(), schema=get_schema())


@bp.get("/deteksi")
def detection_page():
    schema = get_schema()
    return render_template(
        "detection.html", schema=schema, model=ml_service.status()
    )


@bp.get("/hasil/<int:detection_id>")
def result_page(detection_id: int):
    token = get_session_token()
    detection = db.session.get(Detection, detection_id)

    if detection is None or detection.session_token != token:
        abort(404)

    schema = get_schema()
    return render_template(
        "result.html",
        detection=detection,
        schema=schema,
        input_rows=describe_inputs(detection, schema),
        threshold=ml_service.status()["threshold"],
    )


@bp.get("/riwayat")
def history_page():
    token = get_session_token()
    detections = (
        Detection.query.filter_by(session_token=token)
        .order_by(Detection.created_at.desc())
        .limit(30)
        .all()
    )
    return render_template(
        "history.html", detections=detections, schema=get_schema()
    )


@bp.get("/tentang")
def about_page():
    return render_template(
        "tentang.html", model=ml_service.status(), schema=get_schema()
    )
