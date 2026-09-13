from src.browser import BrowserCollector
from src.content_cleaner import ContentCleaner
from src.models import EMAIL_PATTERN, normalize_generic_email


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

        cleaned_content = self.cleaner.clean(page["text"])
        generic_mailtos = self._generic_mailto_addresses(page.get("links", []))
        if generic_mailtos:
            # A common pattern is a button labelled "Contact sales" whose
            # mailto target contains the actual public address. Preserve that
            # rendered-DOM evidence before cleaning and LLM extraction.
            email_line = f"Public email links: {', '.join(generic_mailtos)}"
            cleaned_content = "\n".join(part for part in (cleaned_content, email_line) if part)

        cleaned_sections = self._clean_sections(
            page.get("sections", [])
        )

        return {
            "url": page["url"],
            "status_code": page.get("status_code"),
            "success": True,
            "title": page["title"],
            "content": cleaned_content,
            "sections": cleaned_sections,
            "links": page.get("links", []),
            "error": None,
        }

    @staticmethod
    def _generic_mailto_addresses(links: list[dict]) -> list[str]:
        emails: list[str] = []
        for link in links:
            href = str(link.get("href", "")) if isinstance(link, dict) else ""
            if not href.lower().startswith("mailto:"):
                continue
            # Query parameters (for example, ?subject=demo) are not part of
            # the address. A malformed href simply contributes no evidence.
            candidate = href[7:].split("?", 1)[0].strip()
            email = normalize_generic_email(candidate)
            if email and email not in emails:
                emails.append(email)
        return emails

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
