from __future__ import annotations

import json
import re
from typing import Any

from bs4 import BeautifulSoup

REVIEW_COUNT_RE = re.compile(r"(?<!\d)(\d+)\s+reviews?\b", re.I)
RATING_COUNT_RE = re.compile(r"(?<!\d)(\d+)\s+ratings?\b", re.I)
RATING_VALUE_RE = re.compile(r"([0-5](?:\.\d+)?)\s+out\s+of\s+5", re.I)
COMMENT_SELECTORS = [
    ".review",
    ".reviews-content",
    ".jdgm-rev",
    ".spr-review",
    ".okeReviews-review",
    "[itemprop='review']",
]


def _extract_int(pattern: re.Pattern[str], text: str) -> int | None:
    match = pattern.search(text)
    if not match:
        return None
    return int(match.group(1))


def _extract_float(pattern: re.Pattern[str], text: str) -> float | None:
    match = pattern.search(text)
    if not match:
        return None
    return float(match.group(1))


def _iter_objects(payload: Any):
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from _iter_objects(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_objects(item)


def _extract_schema_metrics(soup: BeautifulSoup) -> tuple[int | None, float | None, int | None, list[str]]:
    review_count = None
    rating_value = None
    rating_count = None
    comments: list[str] = []

    for node in soup.select("script[type='application/ld+json']"):
        raw = node.string or node.get_text(strip=True)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        for obj in _iter_objects(payload):
            aggregate = obj.get("aggregateRating") if isinstance(obj, dict) else None
            if isinstance(aggregate, dict):
                if review_count is None and aggregate.get("reviewCount") not in (None, ""):
                    review_count = int(float(aggregate["reviewCount"]))
                if rating_count is None and aggregate.get("ratingCount") not in (None, ""):
                    rating_count = int(float(aggregate["ratingCount"]))
                if rating_value is None and aggregate.get("ratingValue") not in (None, ""):
                    rating_value = float(aggregate["ratingValue"])

            if not isinstance(obj, dict):
                continue

            review_body = obj.get("reviewBody")
            if isinstance(review_body, str) and review_body.strip():
                comments.append(review_body.strip())

    return review_count, rating_value, rating_count, comments


def _extract_comments_from_dom(soup: BeautifulSoup) -> list[str]:
    comments: list[str] = []
    seen: set[str] = set()

    for selector in COMMENT_SELECTORS:
        for node in soup.select(selector):
            snippet = node.get_text(" ", strip=True)
            if not snippet or len(snippet) < 20:
                continue
            snippet = snippet[:500]
            if snippet in seen:
                continue
            seen.add(snippet)
            comments.append(snippet)

    return comments


def extract_review_metrics_and_content(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    review_count = _extract_int(REVIEW_COUNT_RE, text)
    rating_count = _extract_int(RATING_COUNT_RE, text)
    rating_value = _extract_float(RATING_VALUE_RE, text)

    schema_review_count, schema_rating_value, schema_rating_count, schema_comments = _extract_schema_metrics(soup)

    if review_count is None:
        review_count = schema_review_count
    if rating_value is None:
        rating_value = schema_rating_value
    if rating_count is None:
        rating_count = schema_rating_count

    comments = _extract_comments_from_dom(soup)
    if not comments:
        comments = schema_comments

    return {
        "review_count": review_count,
        "rating_value": rating_value,
        "rating_count": rating_count,
        "comments": comments[:20],
    }

