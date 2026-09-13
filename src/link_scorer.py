from urllib.parse import urlparse


class LinkScorer:
    KEYWORDS = {
        "about": 5,
        "company": 5,
        "story": 5,
        "mission": 5,
        "team": 5,
        "leadership": 6,
        "executives": 6,
        "people": 5,
        "contact": 6,
        "solutions": 4,
        "product": 4,
        "services": 4,
        "industries": 4,
        "customers": 3,
        "use-cases": 4,
        "clients": 3,
        "careers": 2,
    }

    def score(self, url: str, text: str = "") -> int:
        parsed = urlparse(url)

        target = f"{parsed.path} {text}".lower()

        score = 0

        for keyword, weight in self.KEYWORDS.items():
            if keyword in target:
                score += weight

        return score
