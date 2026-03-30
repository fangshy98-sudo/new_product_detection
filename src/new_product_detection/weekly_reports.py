from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .models import NewProductEvent, ReportingConfig

SITE_LABELS = {
    "vapordna_us": "VaporDNA",
    "vapecityusa_us": "Vape City USA",
    "vapesourcing_us": "Vapesourcing USA",
    "megavapeusa_us": "Mega Vape USA",
    "elementvape_us": "Element Vape",
}


def _escape_html(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _format_site(site_id: str) -> str:
    return SITE_LABELS.get(site_id, site_id)


def _parse_date(value: str) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def _build_week_ranges(anchor_date: date, end_date: date) -> list[tuple[date, date]]:
    ranges: list[tuple[date, date]] = []
    start = anchor_date
    while start <= end_date:
        finish = start + timedelta(days=6)
        ranges.append((start, finish))
        start = finish + timedelta(days=1)
    return ranges


def _format_params(params: dict[str, str], *, html: bool) -> str:
    if not params:
        return "-"
    if html:
        return "<br>".join(f"<strong>{_escape_html(key)}</strong>: {_escape_html(value)}" for key, value in params.items())
    return "<br>".join(f"{key}: {value}" for key, value in params.items())


def _format_points(points: list[str], *, html: bool) -> str:
    if not points:
        return "-"
    if html:
        return "<ul>" + "".join(f"<li>{_escape_html(point)}</li>" for point in points[:4]) + "</ul>"
    return "<br>".join(f"- {point}" for point in points[:4])


def _write_week_markdown(path: Path, start: date, finish: date, events: list[NewProductEvent]) -> None:
    grouped: dict[str, list[NewProductEvent]] = defaultdict(list)
    for event in events:
        grouped[event.site_id].append(event)

    lines = [
        f"# US Weekly New Product Report: {start.isoformat()} to {finish.isoformat()}",
        "",
        f"Period: `{start.isoformat()}` to `{finish.isoformat()}`",
        "",
        f"New products captured: **{len(events)}**",
        "",
    ]

    if not events:
        lines.append("No new products were logged in this weekly window yet.")
    else:
        for site_id in sorted(grouped):
            lines.extend([
                f"## {_format_site(site_id)}",
                "",
                "| First Detected | Image | Product | Price | Selling Points | Basic Parameters | URL |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ])
            for event in grouped[site_id]:
                image_cell = f"[Image]({event.image_url})" if event.image_url else "-"
                params_cell = _format_params(event.basic_params, html=False)
                points_cell = _format_points(event.selling_points, html=False)
                lines.append(
                    "| {date} | {image} | {name} | {price} | {points} | {params} | {url} |".format(
                        date=event.first_detected_date,
                        image=image_cell,
                        name=str(event.name).replace("|", "\\|"),
                        price=(event.price_text or "-").replace("|", "\\|"),
                        points=points_cell.replace("|", "\\|"),
                        params=params_cell.replace("|", "\\|"),
                        url=event.product_url.replace("|", "\\|"),
                    )
                )
                if event.description_text:
                    lines.extend(["", f"Summary: {event.description_text}", ""])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_week_html(path: Path, start: date, finish: date, events: list[NewProductEvent]) -> None:
    grouped: dict[str, list[NewProductEvent]] = defaultdict(list)
    for event in events:
        grouped[event.site_id].append(event)

    sections: list[str] = []
    if not events:
        sections.append("<p>No new products were logged in this weekly window yet.</p>")
    else:
        for site_id in sorted(grouped):
            rows: list[str] = []
            for event in grouped[site_id]:
                image_html = (
                    f'<img src="{_escape_html(event.image_url)}" alt="{_escape_html(event.name)}" width="88">'
                    if event.image_url
                    else "-"
                )
                rows.append(
                    "<tr>"
                    f"<td>{_escape_html(event.first_detected_date)}</td>"
                    f"<td>{image_html}</td>"
                    f"<td><strong>{_escape_html(event.name)}</strong><br><small>{_escape_html(event.description_text or '')}</small></td>"
                    f"<td>{_escape_html(event.price_text or '-')}</td>"
                    f"<td>{_format_points(event.selling_points, html=True)}</td>"
                    f"<td>{_format_params(event.basic_params, html=True)}</td>"
                    f"<td><a href=\"{_escape_html(event.product_url)}\" target=\"_blank\">Open</a></td>"
                    "</tr>"
                )

            sections.append(
                f"<h2>{_escape_html(_format_site(site_id))}</h2>"
                "<table>"
                "<thead><tr><th>First Detected</th><th>Image</th><th>Product</th><th>Price</th><th>Selling Points</th><th>Basic Parameters</th><th>URL</th></tr></thead>"
                f"<tbody>{''.join(rows)}</tbody>"
                "</table>"
            )

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>US Weekly New Product Report: {start.isoformat()} to {finish.isoformat()}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
    h1, h2 {{ margin-bottom: 12px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 28px; table-layout: fixed; }}
    th, td {{ border: 1px solid #ddd; padding: 10px; vertical-align: top; text-align: left; }}
    th {{ background: #f4f4f4; }}
    img {{ border-radius: 8px; background: #fff; object-fit: cover; }}
    ul {{ margin: 0; padding-left: 18px; }}
    small {{ color: #555; display: inline-block; margin-top: 6px; }}
  </style>
</head>
<body>
  <h1>US Weekly New Product Report</h1>
  <p>Period: <strong>{start.isoformat()}</strong> to <strong>{finish.isoformat()}</strong></p>
  <p>New products captured: <strong>{len(events)}</strong></p>
  {''.join(sections)}
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def generate_weekly_reports(events: list[NewProductEvent], config: ReportingConfig) -> list[Path]:
    report_dir = Path(config.weekly_report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    today_local = datetime.now(ZoneInfo(config.timezone)).date()
    anchor_date = _parse_date(config.weekly_anchor_date)
    end_date = max(today_local, max((_parse_date(event.first_detected_date) for event in events), default=anchor_date))

    created: list[Path] = []
    index_lines = [
        "# Weekly Report Index",
        "",
        f"Anchor date: `{config.weekly_anchor_date}`",
        "",
        "| Weekly Window | Product Count | Markdown | HTML |",
        "| --- | ---: | --- | --- |",
    ]

    for start, finish in _build_week_ranges(anchor_date, end_date):
        window_events = [event for event in events if start <= _parse_date(event.first_detected_date) <= finish]
        stem = f"us_week_{start.isoformat()}_to_{finish.isoformat()}"
        md_path = report_dir / f"{stem}.md"
        html_path = report_dir / f"{stem}.html"
        _write_week_markdown(md_path, start, finish, window_events)
        _write_week_html(html_path, start, finish, window_events)
        created.extend([md_path, html_path])
        index_lines.append(
            f"| {start.isoformat()} to {finish.isoformat()} | {len(window_events)} | [{md_path.name}]({md_path.name}) | [{html_path.name}]({html_path.name}) |"
        )

    index_path = Path(config.weekly_report_index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    created.append(index_path)
    return created

