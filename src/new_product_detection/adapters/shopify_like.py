from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..models import ProductRecord, SiteConfig

PRICE_RE = re.compile(r"\$\s*([0-9]+(?:\.[0-9]{2})?)")
REVIEW_RE = re.compile(r"(?:(\d+)\s+reviews?|no\s+reviews)", re.I)
RATING_RE = re.compile(r"([0-5](?:\.\d+)?)\s+out\s+of\s+5", re.I)


def _normalize_url(url: str) -> str:
    return url.split("#", 1)[0].split("?", 1)[0].rstrip("/")


def _extract_context_text(anchor) -> str:
    node = anchor
    fallback = anchor.get_text(" ", strip=True)
    for _ in range(5):
        node = node.parent
        if node is None:
            break
        text = node.get_text(" ", strip=True)
        if "$" in text or "review" in text.lower() or "sold out" in text.lower():
            return text
        fallback = text or fallback
    return fallback


def _extract_price(text: str) -> tuple[str | None, float | None]:
    match = PRICE_RE.search(text)
    if not match:
        return None, None
    return match.group(0), float(match.group(1))


def _extract_review_count(text: str) -> int | None:
    match = REVIEW_RE.search(text)
    if not match:
        return None
    if "no reviews" in match.group(0).lower():
        return 0
    return int(match.group(1))


def _extract_rating(text: str) -> float | None:
    match = RATING_RE.search(text)
    if not match:
        return None
    return float(match.group(1))


def parse_shopify_like_list(html: str, site: SiteConfig) -> list[ProductRecord]:
    soup = BeautifulSoup(html, "html.parser")
    products: list[ProductRecord] = []
    seen: set[str] = set()

    for anchor in soup.select("a[href*='/products/']"):
        href = (anchor.get("href") or "").strip()
        if not href:
            continue

        product_url = _normalize_url(urljoin(site.base_url, href))
        if product_url in seen:
            continue

        name = (
            anchor.get_text(" ", strip=True)
            or (anchor.get("title") or "").strip()
            or (anchor.get("aria-label") or "").strip()
        )
        if len(name) < 4:
            continue

        context_text = _extract_context_text(anchor)
        if "$" not in context_text and "sold out" not in context_text.lower() and "review" not in context_text.lower():
            continue

        price_text, price_value = _extract_price(context_text)
        review_count = _extract_review_count(context_text)
        rating_value = _extract_rating(context_text)

        products.append(
            ProductRecord(
                site_id=site.site_id,
                market=site.market,
                product_key=product_url,
                name=name,
                product_url=product_url,
                price_text=price_text,
                price_value=price_value,
                review_count=review_count,
                rating_value=rating_value,
                in_stock="sold out" not in context_text.lower(),
            )
        )
        seen.add(product_url)

    return products

