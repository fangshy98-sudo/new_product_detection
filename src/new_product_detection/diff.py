from __future__ import annotations

from collections.abc import Iterable

from .models import ProductRecord


def merge_with_previous(
    previous: list[ProductRecord],
    current: list[ProductRecord],
    seen_at: str,
) -> list[ProductRecord]:
    previous_map = {item.product_key: item for item in previous}
    merged: list[ProductRecord] = []

    for item in current:
        old = previous_map.get(item.product_key)
        item.first_seen_at = old.first_seen_at if old and old.first_seen_at else seen_at
        item.last_seen_at = seen_at

        if old:
            if item.review_count is None:
                item.review_count = old.review_count
            if item.rating_value is None:
                item.rating_value = old.rating_value
            if item.rating_count is None:
                item.rating_count = old.rating_count
            if item.price_text is None:
                item.price_text = old.price_text
            if item.price_value is None:
                item.price_value = old.price_value
            if item.in_stock is None:
                item.in_stock = old.in_stock
            if item.image_url is None:
                item.image_url = old.image_url
            if item.description_text is None:
                item.description_text = old.description_text
            if not item.selling_points:
                item.selling_points = list(old.selling_points)
            if not item.basic_params:
                item.basic_params = dict(old.basic_params)
            if item.detail_fetched_at is None:
                item.detail_fetched_at = old.detail_fetched_at

        merged.append(item)

    return merged


def detect_new_products(
    previous: list[ProductRecord],
    current: list[ProductRecord],
) -> list[ProductRecord]:
    previous_keys = {item.product_key for item in previous}
    return [item for item in current if item.product_key not in previous_keys]


def detect_unseen_products(
    current: Iterable[ProductRecord],
    known_keys: set[str],
) -> list[ProductRecord]:
    return [item for item in current if item.product_key not in known_keys]
