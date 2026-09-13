from urllib.parse import urljoin, urlparse, urldefrag

from playwright.sync_api import sync_playwright

from src.link_scorer import LinkScorer


class LinkDiscovery:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.scorer = LinkScorer()

    def discover(self, url: str) -> list[dict]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)

            try:
                page = browser.new_page()
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )

                links = page.locator("a").all()
                discovered = {}
                base_domain = urlparse(page.url).netloc

                for link in links:
                    href = link.get_attribute("href")
                    text = link.inner_text().strip()

                    if not href:
                        continue

                    absolute_url = urljoin(page.url, href)
                    absolute_url, _ = urldefrag(absolute_url)

                    parsed = urlparse(absolute_url)

                    if parsed.scheme not in {"http", "https"}:
                        continue

                    if parsed.netloc != base_domain:
                        continue

                    score = self.scorer.score(absolute_url, text)

                    candidate = {
                        "url": absolute_url,
                        "text": text,
                        "score": score,
                    }

                    existing = discovered.get(absolute_url)

                    if existing is None or score > existing["score"]:
                        discovered[absolute_url] = candidate

                results = list(discovered.values())

                results.sort(
                    key=lambda item: item["score"],
                    reverse=True,
                )

                return results

            finally:
                browser.close()