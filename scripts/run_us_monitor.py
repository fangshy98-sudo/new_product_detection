from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from new_product_detection.adapters import parse_site_list
from new_product_detection.config_loader import load_sites
from new_product_detection.diff import detect_new_products, merge_with_previous
from new_product_detection.fetch import fetch_html
from new_product_detection.report import write_market_report
from new_product_detection.storage import load_products_state, save_products_state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the US new product monitor.")
    parser.add_argument("--config", default="config/sites/us_retailers.yaml")
    parser.add_argument("--state", default="data/state/us_products.json")
    parser.add_argument("--report", default="reports/us_latest.md")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    sites = [site for site in load_sites(args.config) if site.enabled]
    previous = load_products_state(args.state)
    current = []
    errors: dict[str, str] = {}

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

    seen_at = datetime.now(timezone.utc).isoformat()
    merged = merge_with_previous(previous, current, seen_at)
    new_products = detect_new_products(previous, merged)

    save_products_state(args.state, merged)
    write_market_report(args.report, merged, new_products, errors=errors)

    print(f"Tracked products: {len(merged)}")
    print(f"New products: {len(new_products)}")
    print(f"Report written to: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
