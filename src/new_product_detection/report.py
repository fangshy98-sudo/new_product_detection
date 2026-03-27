from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .models import ManualReviewRecord, ProductRecord


def _escape_markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_market_report(
    path: str | Path,
    products: list[ProductRecord],
    new_products: list[ProductRecord],
    *,
    errors: dict[str, str] | None = None,
) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    counts = Counter(item.site_id for item in products)
    timestamp = datetime.now(timezone.utc).isoformat()

    lines = [
        "# US New Product Monitor Report",
        "",
        f"Generated at: `{timestamp}`",
        "",
        f"Tracked products: **{len(products)}**",
        f"New products in this run: **{len(new_products)}**",
        "",
        "## Coverage",
        "",
        "| Site | Product Count |",
        "| --- | ---: |",
    ]

    for site_id, count in sorted(counts.items()):
        lines.append(f"| {_escape_markdown_cell(site_id)} | {count} |")

    if errors:
        lines.extend([
            "",
            "## Fetch Errors",
            "",
            "| Site | Error |",
            "| --- | --- |",
        ])
        for site_id, error in sorted(errors.items()):
            lines.append(f"| {_escape_markdown_cell(site_id)} | {_escape_markdown_cell(error)} |")

    lines.extend(["", "## New Products", ""])
    if not new_products:
        lines.append("No new products detected in this run.")
    else:
        lines.extend([
            "| Site | Name | Price | Reviews | Rating | URL |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ])
        for item in new_products:
            lines.append(
                "| {site} | {name} | {price} | {reviews} | {rating} | {url} |".format(
                    site=_escape_markdown_cell(item.site_id),
                    name=_escape_markdown_cell(item.name),
                    price=_escape_markdown_cell(item.price_text or "-"),
                    reviews=item.review_count if item.review_count is not None else "-",
                    rating=item.rating_value if item.rating_value is not None else "-",
                    url=_escape_markdown_cell(item.product_url),
                )
            )

    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manual_review_report(
    path: str | Path,
    records: list[ManualReviewRecord],
) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    lines = [
        "# Manual Review Extraction Report",
        "",
        f"Generated at: `{timestamp}`",
        "",
        f"Products processed: **{len(records)}**",
        "",
    ]

    if not records:
        lines.append("No manual review extraction records found.")
    else:
        lines.extend([
            "| Site | Review Count | Rating | Error | URL |",
            "| --- | ---: | ---: | --- | --- |",
        ])
        for record in records:
            lines.append(
                "| {site} | {review_count} | {rating} | {error} | {url} |".format(
                    site=_escape_markdown_cell(record.site_id),
                    review_count=record.review_count if record.review_count is not None else "-",
                    rating=record.rating_value if record.rating_value is not None else "-",
                    error=_escape_markdown_cell(record.error or "-"),
                    url=_escape_markdown_cell(record.product_url),
                )
            )

        for record in records:
            lines.extend([
                "",
                f"## {record.site_id}",
                "",
                f"URL: `{record.product_url}`",
                "",
                f"Review count: `{record.review_count}`",
                f"Rating value: `{record.rating_value}`",
                f"Rating count: `{record.rating_count}`",
            ])
            if record.error:
                lines.extend(["", f"Error: `{record.error}`"])
                continue
            if not record.comments:
                lines.extend(["", "No visible review content extracted."])
                continue

            lines.extend(["", "Visible review excerpts:"])
            for comment in record.comments:
                lines.extend(["", f"> {comment}"])

    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
