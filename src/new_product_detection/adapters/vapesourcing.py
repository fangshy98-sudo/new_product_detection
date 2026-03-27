from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..models import ProductRecord, SiteConfig

PRICE_RE = re.compile(r"\$\s*([0-9]+(?:\.[0-9]{2})?)")
REVIEW_RE = re.compile(r"(\d+)\s+reviews?", re.I)
RATING_RE = re.compile(r"([0-5](?:\.\d+)?)\s+out\s+of\s+5", re.I)
SKIP_PARTS = ("blog", "news", "search", "account", "privacy", "contact")


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
        if "$" in text or "review" in text.lower() or "out of stock" in text.lower():
            return text
        fallback = text or fallback
    return fallback


def parse_vapesourcing_list(html: str, site: SiteConfig) -> list[ProductRecord]:
    soup = BeautifulSoup(html, "html.parser")
    products: list[ProductRecord] = []
    seen: set[str] = set()

    for anchor in soup.select("a[href$='.html']"):
        href = (anchor.get("href") or "").strip()
        if not href:
            continue
        if any(part in href.lower() for part in SKIP_PARTS):
            continue

        name = anchor.get_text(" ", strip=True)
        if len(name) < 8:
            continue

        context_text = _extract_context_text(anchor)
        if "$" not in context_text:
            continue

        product_url = _normalize_url(urljoin(site.base_url, href))
        if product_url in seen:
            continue

        price_match = PRICE_RE.search(context_text)
        review_match = REVIEW_RE.search(context_text)
        rating_match = RATING_RE.search(context_text)

        products.append(
            ProductRecord(
                site_id=site.site_id,
                market=site.market,
                product_key=product_url,
                name=name,
                product_url=product_url,
                price_text=price_match.group(0) if price_match else None,
                price_value=float(price_match.group(1)) if price_match else None,
                review_count=int(review_match.group(1)) if review_match else None,
                rating_value=float(rating_match.group(1)) if rating_match else None,
                in_stock="out of stock" not in context_text.lower(),
            )
        )
        seen.add(product_url)

    return products

