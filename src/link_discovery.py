"""Discover and normalize same-site links from rendered browser DOM data."""

from urllib.parse import urljoin, urlparse, urldefrag

from src.browser import BrowserCollector
from src.link_scorer import LinkScorer


class LinkDiscovery:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.scorer = LinkScorer()

    def discover_from_page(self, page: dict) -> list[dict]:
        base_url = page.get("url", "")
        base_domain = urlparse(base_url).netloc.casefold()
        discovered: dict[str, dict] = {}
        for raw in page.get("links", []):
            href = raw.get("href", "") if isinstance(raw, dict) else ""
            text = raw.get("text", "") if isinstance(raw, dict) else ""
            if not href:
                continue
            absolute, _ = urldefrag(urljoin(base_url, href))
            parsed = urlparse(absolute)
            if parsed.scheme not in {"http", "https"} or parsed.netloc.casefold() != base_domain:
                continue
            normalized = parsed._replace(query="").geturl().rstrip("/") or absolute
            score = self.scorer.score(normalized, text)
            candidate = {"url": normalized, "text": " ".join(text.split()), "score": score}
            if normalized not in discovered or score > discovered[normalized]["score"]:
                discovered[normalized] = candidate
        return sorted(discovered.values(), key=lambda item: item["score"], reverse=True)

    def discover(self, url: str) -> list[dict]:
        page = BrowserCollector(headless=self.headless).fetch_page(url)
        return self.discover_from_page(page) if page.get("success") else []
