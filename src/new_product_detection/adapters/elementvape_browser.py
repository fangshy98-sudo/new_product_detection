from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..fetch import fetch_html_with_browser
from ..models import ProductRecord, SiteConfig

PRICE_RE = re.compile(r"\$\s*([0-9]+(?:\.[0-9]{2})?)")
SKIP_PARTS = (
    "/collections/",
    "/pages/",
    "/account",
    "/search",
    "/cart",
    "/blog",
    "javascript:",
    "#",
)


def _normalize_url(url: str) -> str:
    return url.split("#", 1)[0].split("?", 1)[0].rstrip("/")


def _extract_context_text(anchor) -> str:
    node = anchor
    fallback = anchor.get_text(" ", strip=True)
    for _ in range(6):
        node = node.parent
        if node is None:
            break
        text = node.get_text(" ", strip=True)
        if "$" in text or "review" in text.lower() or "sold out" in text.lower():
            return text
        fallback = text or fallback
    return fallback


def parse_elementvape_with_browser(site: SiteConfig) -> list[ProductRecord]:
    html = fetch_html_with_browser(site.list_url, extra_wait_ms=4000)
    soup = BeautifulSoup(html, "html.parser")
    products: list[ProductRecord] = []
    seen: set[str] = set()

    for anchor in soup.select("a[href$='.html'], a[href*='/products/']"):
        href = (anchor.get("href") or "").strip()
        if not href or any(part in href.lower() for part in SKIP_PARTS):
            continue

        product_url = _normalize_url(urljoin(site.base_url, href))
        if product_url in seen:
            continue

        name = (
            anchor.get_text(" ", strip=True)
            or (anchor.get("title") or "").strip()
            or (anchor.get("aria-label") or "").strip()
        )
        if len(name) < 6:
            continue

        context_text = _extract_context_text(anchor)
        if "$" not in context_text and "review" not in context_text.lower() and "rating" not in context_text.lower():
            continue

        price_match = PRICE_RE.search(context_text)
        products.append(
            ProductRecord(
                site_id=site.site_id,
                market=site.market,
                product_key=product_url,
                name=name,
                product_url=product_url,
                price_text=price_match.group(0) if price_match else None,
                price_value=float(price_match.group(1)) if price_match else None,
                in_stock="sold out" not in context_text.lower(),
            )
        )
        seen.add(product_url)

    return products

