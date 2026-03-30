from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from new_product_detection.adapters import parse_site_list
from new_product_detection.config_loader import load_reporting_config, load_sites
from new_product_detection.detail_extraction import enrich_product_record
from new_product_detection.diff import detect_unseen_products, merge_with_previous
from new_product_detection.fetch import fetch_html
from new_product_detection.freshness import suppress_probable_legacy_events, suppress_probable_legacy_new_products
from new_product_detection.identity import migrate_known_product_keys, migrate_new_product_events, migrate_product_records
from new_product_detection.models import NewProductEvent, ProductRecord
from new_product_detection.report import write_market_report
from new_product_detection.storage import (
    load_known_product_keys,
    load_new_product_events,
    load_products_state,
    save_daily_snapshot,
    save_known_product_keys,
    save_new_product_events,
    save_products_state,
)
from new_product_detection.weekly_reports import generate_weekly_reports

URL_RE = re.compile(r"https?://[^\s)]+")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the US new product monitor.")
    parser.add_argument("--config", default="config/sites/us_retailers.yaml")
    parser.add_argument("--reporting-config", default="config/reporting.yaml")
    parser.add_argument("--state", default="data/state/us_products.json")
    parser.add_argument("--report", default="reports/us_latest.md")
    return parser


def _to_local_date(iso_timestamp: str, tz_name: str) -> str:
    dt = datetime.fromisoformat(iso_timestamp)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo(tz_name)).date().isoformat()


def _build_new_product_events(products: list[ProductRecord], tz_name: str) -> list[NewProductEvent]:
    events: list[NewProductEvent] = []
    for item in products:
        first_detected_at = item.first_seen_at or datetime.now(timezone.utc).isoformat()
        events.append(
            NewProductEvent(
                site_id=item.site_id,
                market=item.market,
                product_key=item.product_key,
                name=item.name,
                product_url=item.product_url,
                first_detected_at=first_detected_at,
                first_detected_date=_to_local_date(first_detected_at, tz_name),
                price_text=item.price_text,
                price_value=item.price_value,
                review_count=item.review_count,
                rating_value=item.rating_value,
                rating_count=item.rating_count,
                image_url=item.image_url,
                description_text=item.description_text,
                selling_points=list(item.selling_points),
                basic_params=dict(item.basic_params),
            )
        )
    return events


def _bootstrap_known_keys(
    existing_known_keys: set[str],
    previous: list[ProductRecord],
    existing_events: list[NewProductEvent],
    report_path: str,
) -> set[str]:
    keys = set(existing_known_keys)
    keys.update(item.product_key for item in previous)
    keys.update(item.product_key for item in existing_events)

    report_file = Path(report_path)
    if report_file.exists():
        for url in URL_RE.findall(report_file.read_text(encoding="utf-8-sig", errors="ignore")):
            if "/products/" in url or url.endswith(".html"):
                keys.add(url.rstrip("|"))

    return keys


def main() -> int:
    args = build_parser().parse_args()
    reporting = load_reporting_config(args.reporting_config)
    sites = [site for site in load_sites(args.config) if site.enabled]
    sites_by_id = {site.site_id: site for site in sites}

    identity_cache: dict[str, tuple[str, str]] = {}
    sitemap_cache: dict[str, dict[str, object]] = {}
    errors: dict[str, str] = {}

    previous = migrate_product_records(load_products_state(args.state), sites_by_id, identity_cache)
    existing_events = migrate_new_product_events(load_new_product_events(reporting.new_product_event_log_path), sites_by_id, identity_cache)
    stored_known_keys = migrate_known_product_keys(load_known_product_keys(reporting.known_product_keys_path), sites_by_id, identity_cache)

    existing_events, suppressed_existing_events = suppress_probable_legacy_events(existing_events, reporting, sitemap_cache)
    if suppressed_existing_events:
        errors["cleanup:vapecityusa_us"] = (
            f"Suppressed {len(suppressed_existing_events)} legacy historical events using Vape City sitemap lastmod "
            f"older than {reporting.vapecity_legacy_lastmod_grace_days} days."
        )

    known_keys = _bootstrap_known_keys(stored_known_keys, previous, existing_events, args.report)
    known_keys = migrate_known_product_keys(known_keys, sites_by_id, identity_cache)

    current: list[ProductRecord] = []

    for site in sites:
        try:
            html = None
            if site.fetch_mode == "http":
                html = fetch_html(site.list_url)
            records = parse_site_list(html, site)
            current.extend(records)
            print(f"[{site.site_id}] parsed {len(records)} product records")
        except Exception as exc:
            errors[site.site_id] = str(exc)
            print(f"[{site.site_id}] failed: {exc}")

    current = migrate_product_records(current, sites_by_id, identity_cache)

    seen_at = datetime.now(timezone.utc).isoformat()
    local_date = datetime.now(ZoneInfo(reporting.timezone)).date().isoformat()
    merged = merge_with_previous(previous, current, seen_at)
    historically_new_products = detect_unseen_products(merged, known_keys)
    historically_new_products, suppressed_new_products = suppress_probable_legacy_new_products(
        historically_new_products,
        reporting,
        sitemap_cache,
    )
    if suppressed_new_products:
        message = (
            f"Suppressed {len(suppressed_new_products)} pseudo-new products using Vape City sitemap lastmod "
            f"older than {reporting.vapecity_legacy_lastmod_grace_days} days."
        )
        if "cleanup:vapecityusa_us" in errors:
            errors["cleanup:vapecityusa_us"] = f"{errors['cleanup:vapecityusa_us']} {message}"
        else:
            errors["cleanup:vapecityusa_us"] = message

    for item in historically_new_products:
        try:
            enrich_product_record(item, sites_by_id[item.site_id])
        except Exception as exc:
            errors[f"detail:{item.site_id}:{item.product_key}"] = str(exc)
            print(f"[detail:{item.site_id}] failed for {item.product_key}: {exc}")

    new_events = _build_new_product_events(historically_new_products, reporting.timezone)
    all_events = migrate_new_product_events(existing_events + new_events, sites_by_id, identity_cache)
    updated_known_keys = set(known_keys)
    updated_known_keys.update(item.product_key for item in merged)

    save_products_state(args.state, merged)
    snapshot_path = save_daily_snapshot(reporting.snapshot_dir, local_date, merged)
    save_new_product_events(reporting.new_product_event_log_path, all_events)
    save_known_product_keys(reporting.known_product_keys_path, updated_known_keys)
    created_reports = generate_weekly_reports(all_events, reporting)
    write_market_report(args.report, merged, historically_new_products, errors=errors)

    print(f"Tracked products: {len(merged)}")
    print(f"Historically new products: {len(historically_new_products)}")
    print(f"Suppressed legacy Vape City events: {len(suppressed_existing_events)}")
    print(f"Suppressed pseudo-new Vape City products this run: {len(suppressed_new_products)}")
    print(f"Daily snapshot written to: {snapshot_path}")
    print(f"Weekly reports refreshed: {len(created_reports)} files")
    print(f"Report written to: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

