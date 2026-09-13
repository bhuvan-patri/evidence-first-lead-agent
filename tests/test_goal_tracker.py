from src.goal_tracker import GoalTracker


def test_finds_missing_goals():
    tracker = GoalTracker()

    pages = [
        {
            "success": True,
            "goal": "company_overview",
        },
        {
            "success": True,
            "goal": "contact_information",
        },
    ]

    missing = tracker.find_missing(pages)

    assert missing == {
        "target_audience",
        "leadership",
    }