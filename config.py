"""Konfigurasi aplikasi Somnipathy Lab.

Semua nilai sensitif (password database, secret key) dibaca dari file .env
agar tidak tertulis langsung di dalam kode.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Folder akar proyek (tempat file config.py berada)
BASE_DIR = Path(__file__).resolve().parent

# Muat variabel dari .env jika ada
load_dotenv(BASE_DIR / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    """Ubah teks '1', 'true', 'yes', 'on' menjadi True."""
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _resolve_path(value: str | None, default: str) -> str:
    """Ubah path relatif (mis. 'ml/artifacts') menjadi path absolut."""
    path = Path(value or default)
    if not path.is_absolute():
        path = BASE_DIR / path
    return str(path.resolve())


def _database_uri() -> str:
    """Susun URL koneksi SQLAlchemy untuk MySQL/MariaDB."""
    override = os.getenv("DATABASE_URL")
    if override:
        return override

    user = quote_plus(os.getenv("DB_USER", "root"))
    password = quote_plus(os.getenv("DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "somnipathy_lab")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


class Config:
    """Konfigurasi default untuk pengembangan lokal."""

    # --- Flask ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-please-change")
    DEBUG = _as_bool(os.getenv("FLASK_DEBUG"), True)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,   # pulihkan otomatis koneksi yang mati
        "pool_recycle": 280,     # hindari timeout koneksi MySQL
    }

    # --- Machine Learning ---
    MODEL_DIR = _resolve_path(os.getenv("MODEL_DIR"), "ml/artifacts")
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.55"))

    # --- Sistem rekomendasi ---
    RULES_PATH = _resolve_path(
        os.getenv("RULES_PATH"), "rules/recommendation_rules.json"
    )

    # --- Lain-lain ---
    AUTO_CREATE_TABLES = _as_bool(os.getenv("AUTO_CREATE_TABLES"), True)
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = 256 * 1024  # batas ukuran body request (256 KB)
