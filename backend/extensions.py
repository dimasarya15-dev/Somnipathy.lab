"""Objek ekstensi Flask yang dipakai bersama.

Dipisah dari create_app() agar tidak terjadi circular import.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
