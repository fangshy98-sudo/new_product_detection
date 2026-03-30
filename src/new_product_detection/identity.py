from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import replace
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup

from .fetch import build_session
from .models import NewProductEvent, ProductRecord, SiteConfig

PRODUCT_ID_RE = re.compile(r'"productId"\s*:\s*"?([0-9]{2,})', re.I)
SKU_LABEL_RE = re.compile(r"\bSKU:\s*([A-Z0-9_-]{4,})\b", re.I)
SKU_VALUE_RE = re.compile(r"^[A-Z0-9_-]{4,}$")


def _normalize_url(url: str) -> str:
    parts = urlsplit(str(url).strip())
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def _iter_objects(payload):
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from _iter_objects(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_objects(item)


def _extract_json_ld_product(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select("script[type='application/ld+json']"):
        raw = (node.string or node.get_text()).strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for obj in _iter_objects(payload):
            if not isinstance(obj, dict):
                continue
            obj_type = obj.get("@type")
            if obj_type == "Product" or (isinstance(obj_type, list) and "Product" in obj_type):
                return obj
    return {}


def _extract_vapecity_identity_from_html(html: str, fallback_url: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    canonical = None
    node = soup.find("link", rel="canonical")
    if node and node.get("href"):
        canonical = _normalize_url(node["href"])
    product_schema = _extract_json_ld_product(html)
    canonical = canonical or _normalize_url(str(product_schema.get("url") or fallback_url))

    product_id_match = PRODUCT_ID_RE.search(html)
    if product_id_match:
        return f"vapecityusa_us:pid:{product_id_match.group(1)}", canonical

    for key in ("sku", "mpn"):
        value = product_schema.get(key)
        if isinstance(value, str):
            candidate = value.strip().upper()
            if SKU_VALUE_RE.fullmatch(candidate):
                return f"vapecityusa_us:sku:{candidate}", canonical

    match = SKU_LABEL_RE.search(soup.get_text(" ", strip=True))
    if match:
        return f"vapecityusa_us:sku:{match.group(1).strip().upper()}", canonical

    return canonical, canonical


def _resolve_identity_from_url(url: str, site: SiteConfig, cache: dict[str, tuple[str, str]]) -> tuple[str, str]:
    normalized = _normalize_url(url)
    if normalized in cache:
        return cache[normalized]

    if site.site_id != "vapecityusa_us":
        resolved = (normalized, normalized)
        cache[normalized] = resolved
        return resolved

    session = build_session()
    response = session.get(normalized, timeout=30)
    response.raise_for_status()
    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding or response.encoding
    resolved = _extract_vapecity_identity_from_html(response.text, response.url)
    cache[normalized] = resolved
    cache[_normalize_url(response.url)] = resolved
    return resolved


def _infer_site_from_url(url: str, sites_by_id: dict[str, SiteConfig]) -> SiteConfig | None:
    normalized = _normalize_url(url)
    for site in sites_by_id.values():
        base_url = _normalize_url(site.base_url)
        if normalized.startswith(base_url):
            return site
    return None


def migrate_product_records(
    records: Iterable[ProductRecord],
    sites_by_id: dict[str, SiteConfig],
    cache: dict[str, tuple[str, str]] | None = None,
) -> list[ProductRecord]:
    identity_cache = cache or {}
    migrated: dict[str, ProductRecord] = {}

    for record in records:
        site = sites_by_id.get(record.site_id)
        if not site:
            migrated[record.product_key] = record
            continue

        stable_key, canonical_url = _resolve_identity_from_url(record.product_url, site, identity_cache)
        candidate = replace(record, product_key=stable_key, product_url=canonical_url)

        existing = migrated.get(candidate.product_key)
        if not existing:
            migrated[candidate.product_key] = candidate
            continue

        if not existing.image_url and candidate.image_url:
            existing.image_url = candidate.image_url
        if not existing.description_text and candidate.description_text:
            existing.description_text = candidate.description_text
        if not existing.selling_points and candidate.selling_points:
            existing.selling_points = list(candidate.selling_points)
        if not existing.basic_params and candidate.basic_params:
            existing.basic_params = dict(candidate.basic_params)
        if existing.review_count is None and candidate.review_count is not None:
            existing.review_count = candidate.review_count
        if existing.rating_value is None and candidate.rating_value is not None:
            existing.rating_value = candidate.rating_value
        if existing.rating_count is None and candidate.rating_count is not None:
            existing.rating_count = candidate.rating_count
        if existing.first_seen_at and candidate.first_seen_at:
            existing.first_seen_at = min(existing.first_seen_at, candidate.first_seen_at)
        elif candidate.first_seen_at:
            existing.first_seen_at = candidate.first_seen_at
        if existing.last_seen_at and candidate.last_seen_at:
            existing.last_seen_at = max(existing.last_seen_at, candidate.last_seen_at)
        elif candidate.last_seen_at:
            existing.last_seen_at = candidate.last_seen_at

    return list(migrated.values())


def migrate_new_product_events(
    events: Iterable[NewProductEvent],
    sites_by_id: dict[str, SiteConfig],
    cache: dict[str, tuple[str, str]] | None = None,
) -> list[NewProductEvent]:
    identity_cache = cache or {}
    migrated: dict[str, NewProductEvent] = {}

    for event in events:
        site = sites_by_id.get(event.site_id)
        if not site:
            migrated[event.product_key] = event
            continue

        stable_key, canonical_url = _resolve_identity_from_url(event.product_url, site, identity_cache)
        candidate = replace(event, product_key=stable_key, product_url=canonical_url)
        existing = migrated.get(candidate.product_key)
        if not existing:
            migrated[candidate.product_key] = candidate
            continue

        if candidate.first_detected_at < existing.first_detected_at:
            existing.first_detected_at = candidate.first_detected_at
            existing.first_detected_date = candidate.first_detected_date
        if not existing.image_url and candidate.image_url:
            existing.image_url = candidate.image_url
        if not existing.description_text and candidate.description_text:
            existing.description_text = candidate.description_text
        if not existing.selling_points and candidate.selling_points:
            existing.selling_points = list(candidate.selling_points)
        if not existing.basic_params and candidate.basic_params:
            existing.basic_params = dict(candidate.basic_params)
        if existing.review_count is None and candidate.review_count is not None:
            existing.review_count = candidate.review_count
        if existing.rating_value is None and candidate.rating_value is not None:
            existing.rating_value = candidate.rating_value
        if existing.rating_count is None and candidate.rating_count is not None:
            existing.rating_count = candidate.rating_count

    return sorted(migrated.values(), key=lambda item: (item.first_detected_at, item.site_id, item.name.lower()))


def migrate_known_product_keys(
    keys: set[str],
    sites_by_id: dict[str, SiteConfig],
    cache: dict[str, tuple[str, str]] | None = None,
) -> set[str]:
    identity_cache = cache or {}
    migrated: set[str] = set()

    for key in keys:
        if str(key).startswith("http://") or str(key).startswith("https://"):
            site = _infer_site_from_url(str(key), sites_by_id)
            if site:
                stable_key, _ = _resolve_identity_from_url(str(key), site, identity_cache)
                migrated.add(stable_key)
                continue
        migrated.add(str(key))

    return migrated
