from src.browser import BrowserCollector
from src.content_cleaner import ContentCleaner


class EvidenceCollector:
    def __init__(self, headless: bool = True):
        self.browser = BrowserCollector(
            headless=headless
        )
        self.cleaner = ContentCleaner()

    def collect(self, url: str) -> dict:
        page = self.browser.fetch_page(url)

        if not page["success"]:
            return {
                "url": url,
                "success": False,
                "title": "",
                "content": "",
                "sections": [],
                "error": page["error"],
            }

        cleaned_content = self.cleaner.clean(
            page["text"]
        )

        cleaned_sections = self._clean_sections(
            page.get("sections", [])
        )

        return {
            "url": page["url"],
            "success": True,
            "title": page["title"],
            "content": cleaned_content,
            "sections": cleaned_sections,
            "error": None,
        }

    def _clean_sections(
        self,
        sections: list[dict],
    ) -> list[dict]:
        cleaned_sections = []

        for section in sections:
            heading = section.get(
                "heading",
                "",
            ).strip()

            content = section.get(
                "content",
                "",
            )

            cleaned_content = self.cleaner.clean(
                content
            )

            if not heading and not cleaned_content:
                continue

            cleaned_sections.append(
                {
                    "heading": heading,
                    "level": section.get(
                        "level",
                        0,
                    ),
                    "content": cleaned_content,
                }
            )

        return cleaned_sections