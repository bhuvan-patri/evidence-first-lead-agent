from src.planner import InformationPlanner


def test_leadership_and_overview_outrank_lower_value_unresolved_goals():
    planner = InformationPlanner()
    priorities = {goal.name: goal.priority for goal in planner.goals}

    assert priorities["leadership"] > priorities["company_overview"]
    assert priorities["company_overview"] > priorities["target_audience"]


def test_about_link_is_selected_for_an_unresolved_overview():
    result = InformationPlanner().best_goal_for(
        {"url": "https://example.com/about/company", "text": "About the company", "score": 5},
        {"company_overview", "target_audience"},
    )

    assert result["goal"] == "company_overview"
