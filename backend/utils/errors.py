"""Tipe error aplikasi + penanganan respons error yang seragam."""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException


class AppError(Exception):
    """Kesalahan yang disengaja dan aman ditampilkan ke pengguna."""

    status_code = 400
    code = "app_error"

    def __init__(self, message: str, status_code: int | None = None,
                 errors: dict | None = None, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if errors:
            self.errors = errors
        else:
            self.errors = None
        if code:
            self.code = code


class ValidationError(AppError):
    """Input pengguna tidak lolos validasi."""

    status_code = 400
    code = "validation_error"


class ModelNotReadyError(AppError):
    """Model Machine Learning belum tersedia / gagal dimuat."""

    status_code = 503
    code = "model_not_ready"


class NotFoundError(AppError):
    """Data yang diminta tidak ditemukan."""

    status_code = 404
    code = "not_found"


def wants_json() -> bool:
    """True bila request menuju API atau klien meminta JSON."""
    if request.path.startswith("/api/"):
        return True
    best = request.accept_mimetypes.best
    return best == "application/json" and (
        request.accept_mimetypes[best] > request.accept_mimetypes["text/html"]
    )


def _error_response(message: str, status: int, errors: dict | None = None,
                    code: str | None = None):
    payload: dict = {"status": "error", "message": message}
    if errors:
        payload["errors"] = errors
    if code:
        payload["code"] = code

    if wants_json():
        return jsonify(payload), status

    template = "errors/404.html" if status == 404 else "errors/500.html"
    return render_template(template, message=message), status


def register_error_handlers(app: Flask) -> None:
    """Daftarkan seluruh error handler pada aplikasi."""

    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        payload = {"status": "error", "message": exc.message, "code": exc.code}
        if exc.errors:
            payload["errors"] = exc.errors

        if wants_json():
            return jsonify(payload), exc.status_code

        return render_template("errors/500.html", message=exc.message), exc.status_code

    @app.errorhandler(404)
    def handle_404(_exc):
        return _error_response(
            "Halaman atau data yang Anda cari tidak ditemukan.",
            404,
            code="not_found",
        )

    @app.errorhandler(405)
    def handle_405(_exc):
        return _error_response(
            "Metode permintaan tidak diizinkan untuk alamat ini.",
            405,
            code="method_not_allowed",
        )

    @app.errorhandler(413)
    def handle_413(_exc):
        return _error_response(
            "Data yang dikirim terlalu besar.", 413, code="payload_too_large"
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        return _error_response(
            exc.description or "Terjadi kesalahan pada permintaan.",
            exc.code or 500,
            code=(exc.name or "http_error").lower().replace(" ", "_"),
        )

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):  # noqa: BLE001
        app.logger.exception("Kesalahan tak terduga: %s", exc)
        return _error_response(
            "Terjadi kesalahan pada server. Silakan coba lagi.",
            500,
            code="internal_error",
        )
