from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ManualReviewRecord, ProductRecord


def _ensure_parent(path: str | Path) -> Path:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def _write_json(path: str | Path, payload: Any) -> None:
    file_path = _ensure_parent(path)
    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8-sig",
    )


def load_products_state(path: str | Path) -> list[ProductRecord]:
    file_path = Path(path)
    if not file_path.exists():
        return []

    payload = json.loads(file_path.read_text(encoding="utf-8-sig") or "[]")
    return [ProductRecord.from_dict(item) for item in payload]


def save_products_state(path: str | Path, records: list[ProductRecord]) -> None:
    _write_json(path, [record.to_dict() for record in records])


def load_manual_reviews_state(path: str | Path) -> list[ManualReviewRecord]:
    file_path = Path(path)
    if not file_path.exists():
        return []

    payload = json.loads(file_path.read_text(encoding="utf-8-sig") or "[]")
    return [ManualReviewRecord.from_dict(item) for item in payload]


def save_manual_reviews_state(path: str | Path, records: list[ManualReviewRecord]) -> None:
    _write_json(path, [record.to_dict() for record in records])

