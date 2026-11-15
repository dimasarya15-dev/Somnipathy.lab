"""Layanan Machine Learning.

Prinsip penting:
  * Model dimuat SEKALI saat aplikasi start, bukan setiap request.
  * Bila artefak model belum ada, layanan melaporkan "belum siap" dan
    endpoint prediksi membalas 503. TIDAK ADA hasil palsu atau acak.
  * Import scikit-learn/pandas dilakukan secara lazy agar aplikasi web
    tetap bisa dijalankan walau library ML belum terpasang.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

from backend.utils.errors import ModelNotReadyError
from ml.schema import get_classes

logger = logging.getLogger(__name__)

PIPELINE_FILENAME = "model_pipeline.pkl"
META_FILENAME = "model_meta.json"

_lock = threading.Lock()
_state: dict = {
    "ready": False,
    "reason": "Model belum dimuat.",
    "pipeline": None,
    "meta": None,
    "model_dir": None,
    "threshold": 0.55,
}


def load(config: dict) -> dict:
    """Muat pipeline model dari MODEL_DIR. Aman dipanggil berulang."""
    global _state

    with _lock:
        model_dir = Path(config.get("MODEL_DIR") or "ml/artifacts")
        threshold = float(config.get("CONFIDENCE_THRESHOLD", 0.55))
        _state["model_dir"] = str(model_dir)
        _state["threshold"] = threshold

        pipeline_path = model_dir / PIPELINE_FILENAME
        meta_path = model_dir / META_FILENAME
        meta = _read_meta(meta_path)
        _state["meta"] = meta

        # Sudah termuat sebelumnya? Jangan muat ulang (mis. saat reloader aktif).
        if _state["ready"] and _state["pipeline"] is not None:
            return status()

        if not pipeline_path.exists():
            _state.update(
                ready=False,
                pipeline=None,
                reason=(
                    "Model belum tersedia. Berkas yang dicari: "
                    f"{pipeline_path}. Latih model terlebih dahulu "
                    "(lihat ml/train.py) setelah dataset disiapkan."
                ),
            )
            logger.warning("Model ML belum ada di %s", pipeline_path)
            return status()

        try:
            import joblib  # noqa: PLC0415 - import lazy disengaja
        except ImportError:
            _state.update(
                ready=False,
                pipeline=None,
                reason=(
                    "Library joblib/scikit-learn belum terpasang. "
                    "Jalankan: py -m pip install -r requirements.txt"
                ),
            )
            logger.warning("joblib belum terpasang, model tidak dapat dimuat.")
            return status()

        try:
            pipeline = joblib.load(pipeline_path)
        except Exception as exc:  # noqa: BLE001
            _state.update(
                ready=False,
                pipeline=None,
                reason=f"Model gagal dimuat: {exc}",
            )
            logger.exception("Gagal memuat model dari %s", pipeline_path)
            return status()

        classes = list(getattr(pipeline, "classes_", []) or [])
        _state.update(ready=True, pipeline=pipeline, reason=None)
        if classes:
            _state["meta"] = {**(meta or {}), "classes": classes}
        logger.info("Model ML siap dipakai (%s kelas).", len(classes) or "?")
        return status()


def status() -> dict:
    """Informasi status model untuk /api/health dan banner di UI."""
    meta = _state.get("meta") or {}
    classes = meta.get("classes") or get_classes()

    return {
        "ready": bool(_state.get("ready")),
        "reason": _state.get("reason"),
        "model_version": meta.get("model_version"),
        "trained_at": meta.get("trained_at"),
        "classes": classes,
        "threshold": _state.get("threshold", 0.55),
        "model_dir": _state.get("model_dir"),
    }


def is_ready() -> bool:
    return bool(_state.get("ready"))


def predict(cleaned_payload: dict) -> dict:
    """Jalankan prediksi untuk satu baris data yang sudah divalidasi."""
    if not _state.get("ready") or _state.get("pipeline") is None:
        raise ModelNotReadyError(
            _state.get("reason") or "Model Machine Learning belum siap."
        )

    pipeline = _state["pipeline"]
    threshold = float(_state.get("threshold", 0.55))

    # Import lazy: pandas hanya dibutuhkan saat benar-benar memprediksi.
    from ml.preprocessing import build_input_frame

    frame = build_input_frame(cleaned_payload)

    if not hasattr(pipeline, "predict_proba"):
        raise ModelNotReadyError(
            "Model tidak mendukung predict_proba sehingga probabilitas "
            "tidak dapat dihitung."
        )

    try:
        probabilities = pipeline.predict_proba(frame)[0]
    except Exception as exc:  # noqa: BLE001
        raise ModelNotReadyError(f"Gagal menjalankan prediksi: {exc}") from exc

    classes = [str(item) for item in getattr(pipeline, "classes_", [])]
    if len(classes) != len(probabilities):
        raise ModelNotReadyError(
            "Jumlah kelas model tidak sesuai dengan keluaran probabilitas."
        )

    best_index = int(probabilities.argmax())
    confidence = round(float(probabilities[best_index]), 4)
    label = classes[best_index]

    return {
        "label": label,
        "label_index": best_index,
        "confidence": confidence,
        "probabilities": {
            name: round(float(score), 4)
            for name, score in zip(classes, probabilities)
        },
        "threshold": threshold,
        "is_confident": confidence >= threshold,
        "model_version": (_state.get("meta") or {}).get("model_version") or "unknown",
    }


def _read_meta(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("model_meta.json tidak terbaca: %s", exc)
        return None
