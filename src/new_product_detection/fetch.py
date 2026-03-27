from __future__ import annotations

from collections.abc import Iterable

import requests

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

DEFAULT_CLICK_SELECTORS = [
    "text=Enter",
    "text=I am over 21",
    "text=I am 21 or older",
    "text=Yes, I am over 21",
    "text=Accept",
    "text=Agree",
    "button:has-text('Enter')",
]


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch_html(
    url: str,
    *,
    timeout: int = 30,
    headers: dict[str, str] | None = None,
    session: requests.Session | None = None,
) -> str:
    active_session = session or build_session()
    response = active_session.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding or response.encoding
    return response.text


def fetch_html_with_browser(
    url: str,
    *,
    timeout_ms: int = 60000,
    extra_wait_ms: int = 2500,
    click_selectors: Iterable[str] | None = None,
    headless: bool = True,
) -> str:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required for browser fetches. Install dependencies and run `playwright install chromium`."
        ) from exc

    selectors = list(click_selectors or DEFAULT_CLICK_SELECTORS)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.count() > 0:
                    locator.click(timeout=2000)
                    page.wait_for_timeout(500)
            except Exception:
                continue

        try:
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except PlaywrightTimeoutError:
            pass

        page.wait_for_timeout(extra_wait_ms)
        html = page.content()
        browser.close()
        return html
