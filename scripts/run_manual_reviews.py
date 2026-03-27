from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from new_product_detection.config_loader import load_manual_products
from new_product_detection.manual_review_pipeline import run_manual_review_pipeline
from new_product_detection.report import write_manual_review_report
from new_product_detection.storage import save_manual_reviews_state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run manual review extraction for selected products.")
    parser.add_argument("--config", default="config/manual_products.yaml")
    parser.add_argument("--state", default="data/state/manual_reviews.json")
    parser.add_argument("--report", default="reports/manual_reviews_latest.md")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    products = load_manual_products(args.config)
    records = run_manual_review_pipeline(products)
    save_manual_reviews_state(args.state, records)
    write_manual_review_report(args.report, records)

    print(f"Processed manual review targets: {len(records)}")
    print(f"Report written to: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
