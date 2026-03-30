from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass(slots=True)
class SiteConfig:
    site_id: str
    market: str
    display_name: str
    base_url: str
    list_url: str
    platform: str
    fetch_mode: str
    product_url_pattern: str
    supports_review_tracking: bool
    enabled: bool = True


@dataclass(slots=True)
class ReportingConfig:
    weekly_anchor_date: str = "2026-03-28"
    timezone: str = "Asia/Shanghai"
    snapshot_dir: str = "data/history/daily_snapshots"
    new_product_event_log_path: str = "data/history/new_product_events.json"
    known_product_keys_path: str = "data/history/known_product_keys.json"
    weekly_report_dir: str = "reports/weekly"
    weekly_report_index_path: str = "reports/weekly/index.md"


@dataclass(slots=True)
class ManualProductConfig:
    site_id: str
    product_url: str
    extract_mode: str = "http"


@dataclass(slots=True)
class ProductRecord:
    site_id: str
    market: str
    product_key: str
    name: str
    product_url: str
    price_text: Optional[str] = None
    price_value: Optional[float] = None
    review_count: Optional[int] = None
    rating_value: Optional[float] = None
    rating_count: Optional[int] = None
    in_stock: Optional[bool] = None
    image_url: Optional[str] = None
    description_text: Optional[str] = None
    selling_points: list[str] = field(default_factory=list)
    basic_params: dict[str, str] = field(default_factory=dict)
    detail_fetched_at: Optional[str] = None
    first_seen_at: Optional[str] = None
    last_seen_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProductRecord":
        payload = dict(data)
        payload.setdefault("selling_points", [])
        payload.setdefault("basic_params", {})
        return cls(**payload)


@dataclass(slots=True)
class NewProductEvent:
    site_id: str
    market: str
    product_key: str
    name: str
    product_url: str
    first_detected_at: str
    first_detected_date: str
    price_text: Optional[str] = None
    price_value: Optional[float] = None
    review_count: Optional[int] = None
    rating_value: Optional[float] = None
    rating_count: Optional[int] = None
    image_url: Optional[str] = None
    description_text: Optional[str] = None
    selling_points: list[str] = field(default_factory=list)
    basic_params: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewProductEvent":
        payload = dict(data)
        payload.setdefault("selling_points", [])
        payload.setdefault("basic_params", {})
        return cls(**payload)


@dataclass(slots=True)
class ManualReviewRecord:
    site_id: str
    product_url: str
    product_name: Optional[str] = None
    extract_mode: str = "http"
    review_count: Optional[int] = None
    rating_value: Optional[float] = None
    rating_count: Optional[int] = None
    comments: list[str] = field(default_factory=list)
    extracted_at: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManualReviewRecord":
        return cls(**data)
