"""Sistem rekomendasi berbasis aturan (rule-based).

Bukan LLM, bukan model statistik: hasilnya deterministik dan bisa diaudit.
Aturan disimpan sebagai data di rules/recommendation_rules.json sehingga
teks rekomendasi bisa diubah tanpa menyentuh kode Python.

Operator yang didukung:
    eq, ne, gt, gte, lt, lte, in, between
Grup kondisi:
    {"all": [...]}, {"any": [...]}, {"not": {...}}
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from flask import current_app

logger = logging.getLogger(__name__)

DEFAULT_RULES_PATH = (
    Path(__file__).resolve().parent.parent.parent / "rules" / "recommendation_rules.json"
)

SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2, "info": 3}

_cache: dict = {"path": None, "mtime": None, "data": None}


def load_rules(path: str | Path | None = None, force: bool = False) -> dict:
    """Muat aturan dari file JSON (di-cache berdasarkan waktu ubah file)."""
    if path is None:
        try:
            path = current_app.config.get("RULES_PATH") or DEFAULT_RULES_PATH
        except RuntimeError:  # di luar application context
            path = DEFAULT_RULES_PATH

    rules_path = Path(path)
    if not force and _cache["path"] == str(rules_path) and _cache["data"] is not None:
        try:
            if rules_path.stat().st_mtime == _cache["mtime"]:
                return _cache["data"]
        except OSError:
            pass

    with rules_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    data.setdefault("rules", [])
    _cache.update(path=str(rules_path), mtime=rules_path.stat().st_mtime, data=data)
    return data


def reload_rules(path: str | Path | None = None) -> dict:
    return load_rules(path, force=True)


def get_disclaimer() -> str:
    """Teks penafian yang selalu ditampilkan bersama rekomendasi."""
    try:
        return load_rules().get("disclaimer", "")
    except (OSError, json.JSONDecodeError) as exc:
        logger.exception("Gagal membaca aturan rekomendasi: %s", exc)
        return "Hasil ini adalah skrining awal dan bukan diagnosis medis."


def generate(facts: dict, path: str | Path | None = None, limit: int | None = None) -> list[dict]:
    """Evaluasi semua aturan terhadap fakta, kembalikan rekomendasi terurut.

    Parameter facts minimal berisi:
        prediction_label, confidence, is_confident, dan seluruh field input.
    """
    data = load_rules(path)
    matched: list[dict] = []

    for rule in data.get("rules", []):
        when = rule.get("when")
        if not when:
            continue
        try:
            if _matches(facts, when):
                matched.append(rule)
        except Exception as exc:  # noqa: BLE001 - satu aturan rusak jangan mematikan semua
            logger.exception("Aturan %s gagal dievaluasi: %s", rule.get("id"), exc)

    matched.sort(
        key=lambda rule: (
            SEVERITY_RANK.get(str(rule.get("severity", "info")), 99),
            int(rule.get("priority", 100)),
            str(rule.get("id", "")),
        )
    )

    # Satu kategori cukup diwakili satu rekomendasi terkuat
    seen_categories: set[str] = set()
    selected: list[dict] = []
    for rule in matched:
        category = str(rule.get("category", "umum"))
        if category in seen_categories:
            continue
        seen_categories.add(category)
        selected.append(_public_rule(rule))

    max_items = limit or int(data.get("max_recommendations", 5))
    return selected[:max_items]


def _matches(facts: dict, node: dict) -> bool:
    if "all" in node:
        return all(_matches(facts, child) for child in node["all"])
    if "any" in node:
        return any(_matches(facts, child) for child in node["any"])
    if "not" in node:
        return not _matches(facts, node["not"])

    field = node.get("field")
    if not field:
        raise ValueError("Kondisi aturan tidak memiliki 'field'.")

    return _compare(facts.get(field), str(node.get("op", "eq")), node.get("value"))


def _compare(actual, op: str, expected) -> bool:
    if actual is None:
        return False

    if op == "eq":
        if isinstance(expected, bool):
            return bool(actual) is expected
        return actual == expected or str(actual) == str(expected)

    if op == "ne":
        return not _compare(actual, "eq", expected)

    if op == "in":
        if not isinstance(expected, (list, tuple)):
            return False
        return actual in expected or str(actual) in [str(item) for item in expected]

    if op == "between":
        if not isinstance(expected, (list, tuple)) or len(expected) != 2:
            return False
        return _to_number(expected[0]) <= _to_number(actual) <= _to_number(expected[1])

    if op in {"gt", "gte", "lt", "lte"}:
        left = _to_number(actual)
        right = _to_number(expected)
        if op == "gt":
            return left > right
        if op == "gte":
            return left >= right
        if op == "lt":
            return left < right
        return left <= right

    raise ValueError(f"Operator '{op}' tidak dikenal.")


def _to_number(value) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return float(value)


def _public_rule(rule: dict) -> dict:
    return {
        "rule_id": rule.get("id", "-"),
        "category": rule.get("category", "umum"),
        "severity": rule.get("severity", "info"),
        "title": rule.get("title", ""),
        "message": rule.get("message", ""),
    }
