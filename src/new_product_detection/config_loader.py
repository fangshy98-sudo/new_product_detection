from __future__ import annotations

from pathlib import Path

import yaml

from .models import ManualProductConfig, SiteConfig


def _load_yaml(path: str | Path) -> dict:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")

    raw = yaml.safe_load(file_path.read_text(encoding="utf-8-sig")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Config file must contain a YAML object: {file_path}")
    return raw


def load_sites(path: str | Path) -> list[SiteConfig]:
    payload = _load_yaml(path)
    sites = payload.get("sites", [])
    return [SiteConfig(**item) for item in sites]


def load_manual_products(path: str | Path) -> list[ManualProductConfig]:
    payload = _load_yaml(path)
    products = payload.get("products", [])
    return [ManualProductConfig(**item) for item in products]

