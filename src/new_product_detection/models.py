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
    first_seen_at: Optional[str] = None
    last_seen_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProductRecord":
        return cls(**data)


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
