from src.goal_tracker import GoalTracker


def test_finds_missing_goals():
    tracker = GoalTracker()

    pages = [
        {
            "success": True,
            "url": "https://example.com/about",
            "content": "We provide software for developers.",
            "sections": [],
        },
        {
            "success": True,
            "url": "https://example.com/contact",
            "content": "Contact sales@example.com.",
            "sections": [],
        },
    ]

    missing = tracker.find_missing(pages)

    assert missing == {"leadership"}


def test_heading_only_does_not_mark_leadership_complete():
    missing = GoalTracker().find_missing([{
        "success": True,
        "url": "https://example.com/team",
        "content": "Leadership\nMeet the team",
        "sections": [],
    }])

    assert "leadership" in missing
