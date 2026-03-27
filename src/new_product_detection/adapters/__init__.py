from __future__ import annotations

from .elementvape_browser import parse_elementvape_with_browser
from .shopify_like import parse_shopify_like_list
from .vapesourcing import parse_vapesourcing_list
from ..models import ProductRecord, SiteConfig


def parse_site_list(html: str | None, site: SiteConfig) -> list[ProductRecord]:
    if site.platform == "shopify_like":
        return parse_shopify_like_list(html or "", site)
    if site.platform == "vapesourcing_html":
        return parse_vapesourcing_list(html or "", site)
    if site.platform == "elementvape_browser":
        return parse_elementvape_with_browser(site)
    raise ValueError(f"Unsupported platform: {site.platform}")
