from __future__ import annotations

from datetime import datetime, timezone

from .fetch import fetch_html, fetch_html_with_browser
from .models import ManualProductConfig, ManualReviewRecord
from .review_extractors import extract_review_metrics_and_content


def extract_manual_product_reviews(product: ManualProductConfig) -> ManualReviewRecord:
    extracted_at = datetime.now(timezone.utc).isoformat()

    try:
        if product.extract_mode == "browser":
            html = fetch_html_with_browser(product.product_url)
        else:
            html = fetch_html(product.product_url)

        payload = extract_review_metrics_and_content(html)
        return ManualReviewRecord(
            site_id=product.site_id,
            product_url=product.product_url,
            extract_mode=product.extract_mode,
            review_count=payload.get("review_count"),
            rating_value=payload.get("rating_value"),
            rating_count=payload.get("rating_count"),
            comments=payload.get("comments", []),
            extracted_at=extracted_at,
        )
    except Exception as exc:
        return ManualReviewRecord(
            site_id=product.site_id,
            product_url=product.product_url,
            extract_mode=product.extract_mode,
            extracted_at=extracted_at,
            error=str(exc),
        )


def run_manual_review_pipeline(products: list[ManualProductConfig]) -> list[ManualReviewRecord]:
    return [extract_manual_product_reviews(product) for product in products]
