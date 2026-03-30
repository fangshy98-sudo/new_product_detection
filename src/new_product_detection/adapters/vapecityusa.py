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


def parse_vapecityusa_list(html: str, site: SiteConfig) -> list[ProductRecord]:
    soup = BeautifulSoup(html, "html.parser")
    products: list[ProductRecord] = []
    seen: set[str] = set()

    for anchor in soup.select("a.vape-card__name, a.product-item-link"):
        href = (anchor.get("href") or "").strip()
        if not href:
            continue

        product_url = _normalize_url(urljoin(site.base_url, href))
        if product_url in seen:
            continue
        if not product_url.startswith(site.base_url):
            continue

        name = (
            anchor.get_text(" ", strip=True)
            or (anchor.get("title") or "").strip()
            or (anchor.get("aria-label") or "").strip()
        )
        if len(name) < 4:
            continue

        node = anchor.parent
        context_text = anchor.get_text(" ", strip=True)
        for _ in range(5):
            if node is None:
                break
            text = node.get_text(" ", strip=True)
            if "$" in text or "add to cart" in text.lower() or "review" in text.lower():
                context_text = text
                break
            node = node.parent

        if "$" not in context_text:
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
                review_count=(0 if review_match and 'no reviews' in review_match.group(0).lower() else int(review_match.group(1))) if review_match else None,
                rating_value=float(rating_match.group(1)) if rating_match else None,
                in_stock="sold out" not in context_text.lower(),
            )
        )
        seen.add(product_url)

    return products
