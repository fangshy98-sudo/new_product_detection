from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .fetch import fetch_html, fetch_html_with_browser
from .models import ProductRecord, SiteConfig
from .review_extractors import extract_review_metrics_and_content

NOISE_SNIPPETS = (
    "shipping",
    "return policy",
    "privacy policy",
    "warning:",
    "warning ",
    "copyright",
    "sign in",
    "wishlist",
    "reward points",
)
DESCRIPTION_SELECTORS = [
    "[itemprop='description']",
    ".product__description",
    ".product-description",
    ".product-desc",
    ".tab-body-content",
    ".short-description",
    ".product.attribute.description",
    ".rte",
    ".productView-description",
]
LIST_SELECTORS = [
    ".product__description li",
    ".product-description li",
    ".product-desc li",
    ".tab-body-content li",
    ".short-description li",
    ".product.attribute.description li",
    ".rte li",
    ".productView-description li",
    ".faq li",
    ".accordion li",
    ".pagebuilder-column-group li",
]
TABLE_ROW_SELECTORS = [
    "table tr",
    ".table-wrapper tr",
]
IMAGE_META_SELECTORS = [
    ("property", "og:image"),
    ("name", "twitter:image"),
]


def _clean_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    return cleaned.replace("бк", "-").replace("\\x00", "")


def _is_meaningful(text: str) -> bool:
    lowered = text.lower()
    if len(text) < 12:
        return False
    if any(snippet in lowered for snippet in NOISE_SNIPPETS):
        return False
    return True


def _dedupe_keep_order(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(normalized)
    return output


def _iter_objects(payload):
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from _iter_objects(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_objects(item)


def _load_json_ld_objects(soup: BeautifulSoup) -> list[dict]:
    objects: list[dict] = []
    for node in soup.select("script[type='application/ld+json']"):
        raw = (node.string or node.get_text()).strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for obj in _iter_objects(payload):
            if isinstance(obj, dict):
                objects.append(obj)
    return objects


def _extract_product_schema(objects: list[dict]) -> dict:
    for obj in objects:
        obj_type = obj.get("@type")
        if obj_type == "Product":
            return obj
        if isinstance(obj_type, list) and "Product" in obj_type:
            return obj
    return {}


def _extract_faq_answers(objects: list[dict]) -> list[str]:
    answers: list[str] = []
    for obj in objects:
        if obj.get("@type") != "FAQPage":
            continue
        for entity in obj.get("mainEntity", []):
            accepted = entity.get("acceptedAnswer") if isinstance(entity, dict) else None
            text = accepted.get("text") if isinstance(accepted, dict) else None
            cleaned = _clean_text(text or "")
            if _is_meaningful(cleaned):
                answers.append(cleaned)
    return _dedupe_keep_order(answers)


def _extract_image_url(soup: BeautifulSoup, product_schema: dict, product_url: str) -> str | None:
    image = product_schema.get("image") if product_schema else None
    if isinstance(image, list) and image:
        return urljoin(product_url, str(image[0]))
    if isinstance(image, str) and image:
        return urljoin(product_url, image)

    for attr, value in IMAGE_META_SELECTORS:
        node = soup.find("meta", attrs={attr: value})
        if node and node.get("content"):
            return urljoin(product_url, node["content"])

    for selector in ["img[src]", ".product-image img", ".productView-image img"]:
        node = soup.select_one(selector)
        if node and node.get("src"):
            return urljoin(product_url, node["src"])
    return None


def _extract_description_blocks(soup: BeautifulSoup, product_schema: dict) -> list[str]:
    blocks: list[str] = []
    if product_schema.get("description"):
        description = _clean_text(str(product_schema["description"]))
        if _is_meaningful(description):
            blocks.append(description)

    for selector in DESCRIPTION_SELECTORS:
        for node in soup.select(selector):
            text = _clean_text(node.get_text(" ", strip=True))
            if _is_meaningful(text):
                blocks.append(text)
    return _dedupe_keep_order(blocks)


def _extract_list_points(soup: BeautifulSoup) -> list[str]:
    points: list[str] = []
    for selector in LIST_SELECTORS:
        for node in soup.select(selector):
            text = _clean_text(node.get_text(" ", strip=True))
            if _is_meaningful(text):
                points.append(text)
    return _dedupe_keep_order(points)


def _extract_table_rows(soup: BeautifulSoup) -> list[str]:
    rows: list[str] = []
    for selector in TABLE_ROW_SELECTORS:
        for row in soup.select(selector):
            cells = [_clean_text(cell.get_text(" ", strip=True)) for cell in row.select("th, td")]
            cells = [cell for cell in cells if cell]
            if len(cells) >= 2:
                rows.append(f"{cells[0]}: {cells[1]}")
    return _dedupe_keep_order(rows)


def _extract_heading_sections(soup: BeautifulSoup) -> list[str]:
    values: list[str] = []
    headings = soup.find_all(re.compile(r"^h[1-4]$"))
    for heading in headings:
        label = _clean_text(heading.get_text(" ", strip=True)).lower()
        if not any(keyword in label for keyword in ("feature", "spec", "parameter", "detail", "overview")):
            continue
        sibling = heading.find_next_sibling()
        hops = 0
        while sibling is not None and hops < 3:
            text = _clean_text(sibling.get_text(" ", strip=True))
            if _is_meaningful(text):
                values.append(text)
            sibling = sibling.find_next_sibling()
            hops += 1
    return _dedupe_keep_order(values)


def _split_feature_blob(text: str) -> list[str]:
    pieces = re.split(r"(?:\s+[•·]\s+|\s*;\s*|\s*\|\s*|\s{2,})", text)
    cleaned = [_clean_text(piece) for piece in pieces if _is_meaningful(_clean_text(piece))]
    return _dedupe_keep_order(cleaned)


def _extract_basic_params(texts: list[str]) -> dict[str, str]:
    combined = " ".join(texts)
    params: dict[str, str] = {}
    patterns = {
        "puff_count": re.compile(r"(?i)\b(?:up to\s*)?((?:\d{1,3}(?:,\d{3})+)|\d{4,6})\s*(?:puffs?|hits?)\b"),
        "oil_volume": re.compile(r"(?i)\b(\d+(?:\.\d+)?)\s*m[lL]\b"),
        "battery": re.compile(r"(?i)\b(\d{3,5}\s*mAh)\b"),
        "power": re.compile(r"(?i)\b(\d+(?:\.\d+)?)\s*(?:w|watt(?:s)?)\b"),
        "nicotine": re.compile(r"(?i)\b(\d+(?:\.\d+)?%\s*(?:nicotine(?:\s*salt)?|salt\s*nic)?|\d+(?:\.\d+)?\s*mg)\b"),
        "coil": re.compile(r"(?i)\b(dual mesh coil|mesh coil|dual mesh|quad mesh|single mesh|ceramic coil|\d+(?:\.\d+)?\s*ohm)\b"),
        "screen": re.compile(r"(?i)\b(hd screen|touch screen|display|screen)\b"),
        "airflow": re.compile(r"(?i)\b(adjustable airflow|airflow control|airflow)\b"),
        "charging": re.compile(r"(?i)\b(usb[-\s]?c|type-c|rechargeable|fast charging)\b"),
        "modes": re.compile(r"(?i)\b(boost mode|regular mode|pulse mode|eco mode|turbo mode|dual modes?|adjustable wattage|mtl and dl vaping|mtl|dtl)\b"),
        "dimensions": re.compile(r"(?i)\b(\d+(?:\.\d+)?\s*(?:x|×)\s*\d+(?:\.\d+)?\s*(?:x|×)\s*\d+(?:\.\d+)?\s*mm)\b"),
    }

    for key, pattern in patterns.items():
        match = pattern.search(combined)
        if match:
            value = _clean_text(match.group(1))
            if key == "oil_volume" and not value.lower().endswith("ml"):
                value = f"{value} mL"
            params[key] = value

    for text in texts:
        lower = text.lower()
        if lower.startswith("dimensions") and "dimensions" not in params:
            params["dimensions"] = text.split(":", 1)[-1].strip() if ":" in text else text
        if lower.startswith("battery") and "battery" not in params:
            params["battery"] = text.split(":", 1)[-1].strip() if ":" in text else text
        if lower.startswith("nicotine") and "nicotine" not in params:
            params["nicotine"] = text.split(":", 1)[-1].strip() if ":" in text else text

    return params


def extract_product_detail_from_html(html: str, product_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    schema_objects = _load_json_ld_objects(soup)
    product_schema = _extract_product_schema(schema_objects)
    faq_answers = _extract_faq_answers(schema_objects)
    review_metrics = extract_review_metrics_and_content(html)

    description_blocks = _extract_description_blocks(soup, product_schema)
    list_points = _extract_list_points(soup)
    row_points = _extract_table_rows(soup)
    section_points = _extract_heading_sections(soup)

    selling_points = _dedupe_keep_order(list_points + section_points + faq_answers)
    if not selling_points and description_blocks:
        selling_points = _split_feature_blob(description_blocks[0]) or description_blocks[:3]

    description_text = description_blocks[0] if description_blocks else None
    all_texts = description_blocks + list_points + row_points + faq_answers
    basic_params = _extract_basic_params(all_texts)

    rating_value = review_metrics.get("rating_value")
    rating_count = review_metrics.get("rating_count")
    review_count = review_metrics.get("review_count")

    aggregate = product_schema.get("aggregateRating") if isinstance(product_schema, dict) else None
    if isinstance(aggregate, dict):
        if rating_value is None and aggregate.get("ratingValue") not in (None, ""):
            rating_value = float(aggregate["ratingValue"])
        if rating_count is None and aggregate.get("ratingCount") not in (None, ""):
            rating_count = int(float(aggregate["ratingCount"]))
        if review_count is None and aggregate.get("reviewCount") not in (None, ""):
            review_count = int(float(aggregate["reviewCount"]))

    return {
        "image_url": _extract_image_url(soup, product_schema, product_url),
        "description_text": description_text,
        "selling_points": selling_points[:6],
        "basic_params": basic_params,
        "review_count": review_count,
        "rating_value": rating_value,
        "rating_count": rating_count,
    }


def enrich_product_record(record: ProductRecord, site: SiteConfig) -> ProductRecord:
    if site.fetch_mode == "browser":
        html = fetch_html_with_browser(record.product_url, extra_wait_ms=3000)
    else:
        html = fetch_html(record.product_url)

    detail = extract_product_detail_from_html(html, record.product_url)
    record.image_url = detail.get("image_url") or record.image_url
    record.description_text = detail.get("description_text") or record.description_text
    record.selling_points = detail.get("selling_points") or record.selling_points
    record.basic_params = detail.get("basic_params") or record.basic_params
    record.review_count = detail.get("review_count") if detail.get("review_count") is not None else record.review_count
    record.rating_value = detail.get("rating_value") if detail.get("rating_value") is not None else record.rating_value
    record.rating_count = detail.get("rating_count") if detail.get("rating_count") is not None else record.rating_count
    record.detail_fetched_at = datetime.now(timezone.utc).isoformat()
    return record
