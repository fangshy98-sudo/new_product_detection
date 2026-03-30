from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from xml.etree import ElementTree

from .fetch import build_session
from .models import NewProductEvent, ProductRecord, ReportingConfig

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
VAPECITY_SITEMAP_URL = "https://vapecityusa.com/sitemap.xml"


def _parse_iso_date(value: str) -> date:
    normalized = value.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).date()


def _load_vapecity_lastmods(cache: dict[str, dict[str, date]] | None = None) -> dict[str, date]:
    sitemap_cache = cache or {}
    cached = sitemap_cache.get("vapecity_sitemap_lastmods")
    if cached is not None:
        return cached

    session = build_session()
    response = session.get(VAPECITY_SITEMAP_URL, timeout=30)
    response.raise_for_status()
    root = ElementTree.fromstring(response.text)

    mapping: dict[str, date] = {}
    for url_node in root.findall("sm:url", SITEMAP_NS):
        loc_node = url_node.find("sm:loc", SITEMAP_NS)
        lastmod_node = url_node.find("sm:lastmod", SITEMAP_NS)
        if loc_node is None or lastmod_node is None:
            continue
        loc = (loc_node.text or "").strip().rstrip("/")
        lastmod = (lastmod_node.text or "").strip()
        if not loc or not lastmod:
            continue
        try:
            mapping[loc] = _parse_iso_date(lastmod)
        except ValueError:
            continue

    sitemap_cache["vapecity_sitemap_lastmods"] = mapping
    return mapping


def _is_probably_legacy_vapecity_product(product_url: str, detected_date: date, grace_days: int, cache: dict[str, dict[str, date]] | None = None) -> bool:
    if not product_url.startswith("https://vapecityusa.com/"):
        return False
    lastmods = _load_vapecity_lastmods(cache)
    lastmod = lastmods.get(product_url.rstrip("/"))
    if lastmod is None:
        return False
    return (detected_date - lastmod).days > grace_days


def suppress_probable_legacy_new_products(
    products: Iterable[ProductRecord],
    reporting: ReportingConfig,
    cache: dict[str, dict[str, date]] | None = None,
) -> tuple[list[ProductRecord], list[ProductRecord]]:
    kept: list[ProductRecord] = []
    suppressed: list[ProductRecord] = []

    for item in products:
        if item.site_id != "vapecityusa_us" or not item.first_seen_at:
            kept.append(item)
            continue
        detected_date = _parse_iso_date(item.first_seen_at)
        if _is_probably_legacy_vapecity_product(item.product_url, detected_date, reporting.vapecity_legacy_lastmod_grace_days, cache):
            suppressed.append(item)
            continue
        kept.append(item)

    return kept, suppressed


def suppress_probable_legacy_events(
    events: Iterable[NewProductEvent],
    reporting: ReportingConfig,
    cache: dict[str, dict[str, date]] | None = None,
) -> tuple[list[NewProductEvent], list[NewProductEvent]]:
    kept: list[NewProductEvent] = []
    suppressed: list[NewProductEvent] = []

    for event in events:
        if event.site_id != "vapecityusa_us":
            kept.append(event)
            continue
        try:
            detected_date = date.fromisoformat(event.first_detected_date)
        except ValueError:
            kept.append(event)
            continue
        if _is_probably_legacy_vapecity_product(event.product_url, detected_date, reporting.vapecity_legacy_lastmod_grace_days, cache):
            suppressed.append(event)
            continue
        kept.append(event)

    return kept, suppressed
