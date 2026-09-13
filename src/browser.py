"""Playwright-backed browser retrieval with structured failure states."""

from __future__ import annotations

from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


class BrowserCollector:
    def __init__(self, headless: bool = True, timeout: int = 30_000, settle_ms: int = 750):
        self.headless = headless
        self.timeout = timeout
        self.settle_ms = settle_ms

    @staticmethod
    def _failure(url: str, error: str, status_code: int | None = None) -> dict:
        return {"url": url, "status_code": status_code, "title": "", "text": "",
                "sections": [], "links": [], "success": False, "error": error}

    def fetch_page(self, url: str) -> dict:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return self._failure(url, "Invalid HTTP(S) URL")
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                try:
                    page = browser.new_page()
                    page.set_default_timeout(self.timeout)
                    try:
                        response = page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                        try:
                            page.wait_for_load_state("networkidle", timeout=min(self.timeout, 5_000))
                        except PlaywrightTimeoutError:
                            pass
                        page.wait_for_timeout(self.settle_ms)
                        status = response.status if response else None
                        text = self._body_text(page)
                        result = {
                            "url": page.url, "status_code": status, "title": self._title(page),
                            "text": text, "sections": self._extract_sections(page),
                            "links": self._extract_links(page), "success": status is None or status < 400,
                            "error": None if status is None or status < 400 else f"HTTP {status}",
                        }
                        if self._looks_blocked(text):
                            result["success"] = False
                            result["error"] = "Page appears blocked by the site"
                        return result
                    except PlaywrightTimeoutError:
                        return self._failure(url, "Page navigation timed out")
                    except Exception as exc:
                        return self._failure(url, f"Browser error: {type(exc).__name__}: {exc}")
                finally:
                    browser.close()
        except Exception as exc:
            return self._failure(url, f"Browser startup error: {type(exc).__name__}: {exc}")

    @staticmethod
    def _title(page) -> str:
        try:
            return page.title().strip()
        except Exception:
            return ""

    @staticmethod
    def _body_text(page) -> str:
        try:
            return page.locator("body").inner_text(timeout=5_000)
        except Exception:
            return ""

    @staticmethod
    def _looks_blocked(text: str) -> bool:
        lowered = text.lower()
        return any(marker in lowered for marker in ("access denied", "temporarily blocked", "verify you are human", "captcha"))

    @staticmethod
    def _extract_links(page) -> list[dict]:
        try:
            return page.locator("a").evaluate_all("""
                anchors => anchors.map(a => ({
                    href: a.href || '', text: (a.innerText || a.textContent || '').replace(/\\s+/g, ' ').trim()
                }))
            """)
        except Exception:
            return []

    @staticmethod
    def _extract_sections(page) -> list[dict]:
        try:
            return page.locator("body").evaluate("""
                body => Array.from(body.querySelectorAll('h1,h2,h3,h4,h5,h6')).map(heading => {
                    const nodes = []; let node = heading.nextElementSibling;
                    while (node && !/^H[1-6]$/.test(node.tagName)) {
                        const text = (node.innerText || '').replace(/\\s+/g, ' ').trim();
                        if (text) nodes.push(text); node = node.nextElementSibling;
                    }
                    return {heading: (heading.innerText || '').replace(/\\s+/g, ' ').trim(),
                            level: Number(heading.tagName.slice(1)), content: nodes.join('\\n')};
                }).filter(section => section.heading || section.content)
            """)
        except Exception:
            return []
