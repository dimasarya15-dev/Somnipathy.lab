"""Application factory untuk Somnipathy Lab.

create_app() merakit seluruh bagian aplikasi:
    1. konfigurasi
    2. database
    3. model Machine Learning (dimuat sekali saat startup)
    4. blueprint / route
    5. penanganan error
    6. perintah CLI
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from backend.extensions import db
from backend.utils.display import format_datetime, severity_label
from config import Config

# Lokasi folder frontend (template HTML + aset statis)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app(config_object=None, **overrides) -> Flask:
    """Buat instance Flask lengkap.

    Parameter:
        config_object: kelas konfigurasi (default: Config dari config.py)
        **overrides:   nilai konfigurasi tambahan, mis. untuk pengujian
    """
    app = Flask(
        __name__,
        template_folder=str(FRONTEND_DIR / "templates"),
        static_folder=str(FRONTEND_DIR / "static"),
    )
    app.config.from_object(config_object or Config)
    app.config.update(overrides)

    # Supaya teks Indonesia (mis. "tidur") tidak diubah menjadi \uXXXX di JSON
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    # --- Database ---
    db.init_app(app)

    # --- Machine Learning: muat model SEKALI di sini ---
    from backend.services import ml_service

    ml_service.load(app.config)

    # --- Blueprint ---
    from backend.routes.history_routes import bp as history_bp
    from backend.routes.predict_routes import bp as predict_bp
    from backend.routes.system_routes import bp as system_bp
    from backend.routes.web_routes import bp as web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(predict_bp, url_prefix="/api")
    app.register_blueprint(history_bp, url_prefix="/api")
    app.register_blueprint(system_bp, url_prefix="/api")

    # --- Error handler ---
    from backend.utils.errors import register_error_handlers

    register_error_handlers(app)

    # --- Helper tampilan untuk template Jinja ---
    app.jinja_env.globals["severity_label"] = severity_label
    app.jinja_env.filters["tanggal"] = format_datetime

    # --- Perintah CLI (flask init-db, flask check-model) ---
    from backend.cli import register_cli

    register_cli(app)

    # --- Pastikan model ikut terdaftar sebelum create_all() ---
    from backend import models  # noqa: F401

    if app.config.get("AUTO_CREATE_TABLES"):
        _auto_create_tables(app)

    return app


def _auto_create_tables(app: Flask) -> None:
    """Buat tabel otomatis bila database bisa dijangkau.

    Jika MySQL belum menyala, aplikasi tetap boleh jalan (mode degradasi),
    dan statusnya terlihat di /api/health.
    """
    with app.app_context():
        try:
            db.create_all()
        except Exception as exc:  # noqa: BLE001 - sengaja menangkap semua error DB
            app.logger.warning(
                "Tabel belum bisa dibuat otomatis (database belum siap?): %s", exc
            )
