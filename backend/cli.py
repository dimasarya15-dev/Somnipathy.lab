"""Perintah CLI tambahan.

Contoh pemakaian:
    py -m flask --app app init-db
    py -m flask --app app check-model
"""

from __future__ import annotations

import click
from flask import Flask
from flask.cli import with_appcontext


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db_command():
        """Buat semua tabel berdasarkan model SQLAlchemy."""
        from backend import models  # noqa: F401
        from backend.extensions import db

        db.create_all()
        click.echo("Tabel database berhasil dibuat/diperbarui.")

    @app.cli.command("check-model")
    def check_model_command():
        """Tampilkan status kesiapan model Machine Learning."""
        from backend.services import ml_service

        info = ml_service.status()
        click.echo(f"Model siap : {info['ready']}")
        click.echo(f"Versi      : {info['model_version'] or '-'}")
        click.echo(f"Kelas      : {', '.join(info['classes']) or '-'}")
        click.echo(f"Ambang     : {info['threshold']}")
        click.echo(f"Folder     : {info['model_dir']}")
        if info.get("reason"):
            click.echo(f"Catatan    : {info['reason']}")

    @app.cli.command("check-rules")
    @with_appcontext
    def check_rules_command():
        """Tampilkan jumlah aturan rekomendasi yang termuat."""
        from backend.services import recommendation_service

        data = recommendation_service.load_rules()
        click.echo(f"Versi aturan : {data.get('version', '-')}")
        click.echo(f"Jumlah aturan: {len(data.get('rules', []))}")
