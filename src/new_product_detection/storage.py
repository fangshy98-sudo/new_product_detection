from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ManualReviewRecord, NewProductEvent, ProductRecord


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


def load_new_product_events(path: str | Path) -> list[NewProductEvent]:
    file_path = Path(path)
    if not file_path.exists():
        return []

    payload = json.loads(file_path.read_text(encoding="utf-8-sig") or "[]")
    return [NewProductEvent.from_dict(item) for item in payload]


def save_new_product_events(path: str | Path, records: list[NewProductEvent]) -> None:
    _write_json(path, [record.to_dict() for record in records])


def load_known_product_keys(path: str | Path) -> set[str]:
    file_path = Path(path)
    if not file_path.exists():
        return set()

    payload = json.loads(file_path.read_text(encoding="utf-8-sig") or "[]")
    return {str(item) for item in payload}


def save_known_product_keys(path: str | Path, keys: set[str]) -> None:
    _write_json(path, sorted(keys))


def save_daily_snapshot(snapshot_dir: str | Path, snapshot_date: str, records: list[ProductRecord]) -> Path:
    directory = Path(snapshot_dir)
    directory.mkdir(parents=True, exist_ok=True)
    snapshot_path = directory / f"us_products_{snapshot_date}.json"
    _write_json(snapshot_path, [record.to_dict() for record in records])
    return snapshot_path


def load_manual_reviews_state(path: str | Path) -> list[ManualReviewRecord]:
    file_path = Path(path)
    if not file_path.exists():
        return []

    payload = json.loads(file_path.read_text(encoding="utf-8-sig") or "[]")
    return [ManualReviewRecord.from_dict(item) for item in payload]


def save_manual_reviews_state(path: str | Path, records: list[ManualReviewRecord]) -> None:
    _write_json(path, [record.to_dict() for record in records])
