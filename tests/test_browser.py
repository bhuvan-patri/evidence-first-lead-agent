from src.browser import BrowserCollector


def test_invalid_url_is_structured_failure():
    page = BrowserCollector().fetch_page("not a url")
    assert page["success"] is False
    assert page["links"] == []
    assert "Invalid" in page["error"]
