"""Endpoint sistem: kesehatan aplikasi, info model, dan skema fitur."""

from __future__ import annotations

from flask import Blueprint

from backend.extensions import db
from backend.services import ml_service, recommendation_service
from backend.utils.responses import success
from ml.schema import get_schema
from sqlalchemy import text

bp = Blueprint("system", __name__)


@bp.get("/health")
def health():
    """Status ringkas: database, model, skema, aturan."""
    connected, db_error = _check_database()
    model = ml_service.status()
    schema = get_schema()

    data = {
        "status": "ok" if connected and model["ready"] else "degraded",
        "database": {"connected": connected, "error": db_error},
        "model": model,
        "schema": {
            "version": schema.get("version"),
            "status": schema.get("status"),
        },
        "rules": _rules_summary(),
    }
    return success(data)


@bp.get("/model-info")
def model_info():
    """Informasi model tanpa menjalankan prediksi (tanpa angka karangan)."""
    model = ml_service.status()
    schema = get_schema()

    return success(
        {
            "ready": model["ready"],
            "reason": model.get("reason"),
            "model_version": model.get("model_version"),
            "trained_at": model.get("trained_at"),
            "classes": model.get("classes"),
            "threshold": model.get("threshold"),
            "features": [field["name"] for field in schema.get("fields", [])],
            "schema_version": schema.get("version"),
        }
    )


@bp.get("/schema")
def schema_info():
    """Skema fitur yang dipakai form dan validasi."""
    return success(get_schema())


def _check_database() -> tuple[bool, str | None]:
    try:
        db.session.execute(text("SELECT 1"))
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, str(exc).splitlines()[0]
    finally:
        db.session.rollback()


def _rules_summary() -> dict:
    try:
        data = recommendation_service.load_rules()
        return {"version": data.get("version"), "count": len(data.get("rules", []))}
    except Exception as exc:  # noqa: BLE001
        return {"version": None, "count": 0, "error": str(exc)}
