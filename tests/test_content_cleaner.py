from src.content_cleaner import ContentCleaner
from src.evidence_collector import EvidenceCollector


def test_removes_repeated_navigation_but_preserves_description():
    cleaned = ContentCleaner().clean(
        "Sign up\nSign up\nSign up\n"
        "We build workflow software for engineering teams.\n"
        "Privacy policy\n"
    )
    assert "Sign up" not in cleaned
    assert "workflow software" in cleaned
    assert "Privacy policy" not in cleaned


def test_collector_preserves_generic_mailto_address_not_shown_in_link_text():
    class Browser:
        def fetch_page(self, _url):
            return {
                "url": "https://example.com/contact", "status_code": 200,
                "success": True, "title": "Contact", "text": "Contact sales",
                "sections": [], "links": [{"href": "mailto:sales@example.com?subject=Demo", "text": "Contact sales"}],
                "error": None,
            }

    collector = EvidenceCollector()
    collector.browser = Browser()

    page = collector.collect("https://example.com/contact")

    assert "sales@example.com" in page["content"]
