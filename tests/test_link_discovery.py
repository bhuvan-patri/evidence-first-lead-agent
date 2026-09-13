from src.link_discovery import LinkDiscovery


def test_normalizes_deduplicates_and_filters_external_links():
    page = {
        "url": "https://example.com/",
        "links": [
            {"href": "/about#team", "text": "About"},
            {"href": "https://example.com/about?ref=nav", "text": "Company"},
            {"href": "https://elsewhere.example/team", "text": "Team"},
            {"href": "mailto:hello@example.com", "text": "Email"},
        ],
    }
    links = LinkDiscovery().discover_from_page(page)
    assert len(links) == 1
    assert links[0]["url"] == "https://example.com/about"
