"""Penanda sesi anonim untuk menyimpan riwayat deteksi.

Kami tidak meminta nama, email, atau identitas apa pun. Setiap pengunjung
mendapat satu token acak yang disimpan di cookie sesi Flask yang ditandatangani.
Riwayat hanya bisa dilihat oleh pemilik token tersebut.
"""

from __future__ import annotations

import uuid

from flask import session

SESSION_KEY = "sid"


def get_session_token() -> str:
    """Ambil token sesi; buat baru bila belum ada."""
    token = session.get(SESSION_KEY)
    if not token:
        token = str(uuid.uuid4())
        session[SESSION_KEY] = token
    return token
