"""Fixture bersama untuk seluruh pengujian.

Pengujian memakai SQLite di memori agar tidak menyentuh database MySQL asli.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from backend import create_app
from backend.extensions import db as _db

BASE_DIR = Path(__file__).resolve().parent.parent


class TestConfig:
    TESTING = True
    DEBUG = False
    SECRET_KEY = "kunci-rahasia-untuk-pengujian"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTO_CREATE_TABLES = False
    MODEL_DIR = str(BASE_DIR / "ml" / "artifacts")
    CONFIDENCE_THRESHOLD = 0.55
    RULES_PATH = str(BASE_DIR / "rules" / "recommendation_rules.json")


@pytest.fixture()
def app():
    application = create_app(TestConfig)

    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
