from src.site_analyzer import SiteAnalyzer


class FakeCollector:
    def __init__(self):
        self.pages = {
            "https://example.com": {
                "url": "https://example.com", "success": True, "content": "We build software.",
                "links": [{"href": "/team", "text": "Leadership"}], "sections": [], "title": "",
            },
            "https://example.com/team": {
                "url": "https://example.com/team", "success": True,
                "content": "Our leadership team\nJane Doe, CEO", "links": [], "sections": [], "title": "",
            },
        }
    def collect(self, url):
        return self.pages[url]


def test_adaptive_selection_respects_page_budget():
    analyzer = SiteAnalyzer(max_pages=2)
    analyzer.collector = FakeCollector()
    result = analyzer.analyze("example.com")
    assert result["success"] is True
    assert result["pages_selected"] == 1
    assert len(result["pages"]) == 2


def test_leadership_goal_requires_evidence_pack_item_not_heading_only():
    analyzer = SiteAnalyzer()
    pages = [{
        "url": "https://example.com/team",
        "success": True,
        "content": "Leadership\nMeet the team",
        "sections": [],
        "links": [],
    }]

    assert "leadership" not in analyzer.completed_goals(pages)
