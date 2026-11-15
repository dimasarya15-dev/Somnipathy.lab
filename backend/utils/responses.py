"""Format respons JSON yang seragam untuk seluruh API."""

from __future__ import annotations

from flask import jsonify


def success(data=None, message: str | None = None, status: int = 200, **extra):
    """Respons sukses.

    Bentuk: {"status": "success", "message": "...", "data": {...}}
    """
    payload: dict = {"status": "success"}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return jsonify(payload), status


def error(message: str, status: int = 400, errors: dict | None = None,
          code: str | None = None):
    """Respons gagal.

    Bentuk: {"status": "error", "message": "...", "errors": {...}}
    """
    payload: dict = {"status": "error", "message": message}
    if errors:
        payload["errors"] = errors
    if code:
        payload["code"] = code
    return jsonify(payload), status
