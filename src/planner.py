from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class InformationGoal:
    name: str
    keywords: list[str]
    priority: int


class InformationPlanner:
    def __init__(self):
        self.goals = [
            InformationGoal(
                name="leadership",
                keywords=[
                    "leadership",
                    "team",
                    "people",
                    "executives",
                    "management",
                    "founders",
                ],
                priority=7,
            ),
            InformationGoal(
                name="contact_information",
                keywords=[
                    "contact",
                    "sales",
                    "support",
                    "help",
                ],
                priority=5,
            ),
            InformationGoal(
                name="company_overview",
                keywords=[
                    "about",
                    "our-story",
                    "story",
                    "mission",
                    "overview",
                    "company",
                ],
                priority=6,
            ),
            InformationGoal(
                name="target_audience",
                keywords=[
                    "industries",
                    "customers",
                    "clients",
                    "use-cases",
                    "solutions",
                    "developers",
                    "teams",
                ],
                priority=4,
            ),
        ]

    def _goal_score(
        self,
        url: str,
        text: str,
        goal: InformationGoal,
    ) -> int:
        parsed = urlparse(url)

        path = parsed.path.lower()
        link_text = text.lower()

        score = 0

        for keyword in goal.keywords:
            if keyword in path:
                score += 3

            if keyword in link_text:
                score += 2

        return score

    def rank_links(
        self,
        links: list[dict],
        completed_goals: set[str] | None = None,
    ) -> list[dict]:
        completed_goals = completed_goals or set()

        ranked = []

        for link in links:
            best_goal = None
            best_goal_score = 0

            for goal in self.goals:
                if goal.name in completed_goals:
                    continue

                goal_score = self._goal_score(
                    link["url"],
                    link["text"],
                    goal,
                )

                if goal_score > best_goal_score:
                    best_goal = goal
                    best_goal_score = goal_score

            if best_goal is None:
                continue

            ranked.append(
                {
                    **link,
                    "goal": best_goal.name,
                    "goal_score": best_goal_score,
                    "goal_priority": best_goal.priority,
                }
            )

        ranked.sort(
            key=lambda item: (
                item["goal_priority"],
                item["goal_score"],
                item["score"],
            ),
            reverse=True,
        )

        return ranked

    def best_goal_for(self, link: dict, missing_goals: set[str]) -> dict | None:
        """Score a link against current, rather than initial, information gaps."""
        candidates = []
        for goal in self.goals:
            if goal.name not in missing_goals:
                continue
            relevance = self._goal_score(link["url"], link.get("text", ""), goal)
            if relevance:
                candidates.append((goal.priority, relevance, goal))
        if not candidates:
            return None
        _, relevance, goal = max(candidates, key=lambda item: (item[0], item[1]))
        return {**link, "goal": goal.name, "goal_score": relevance, "goal_priority": goal.priority}
