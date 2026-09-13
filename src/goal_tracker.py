class GoalTracker:
    REQUIRED_GOALS = {
        "company_overview",
        "target_audience",
        "contact_information",
        "leadership",
    }

    def find_missing(self, collected_pages):
        completed = set()

        for page in collected_pages:
            if not page.get("success"):
                continue

            # EvidenceBuilder may attach multiple detected goals.
            goals = page.get("goals", [])

            # Backward compatibility with the previous single-goal format.
            if not goals and page.get("goal"):
                goals = [page["goal"]]

            completed.update(goals)

        return self.REQUIRED_GOALS - completed