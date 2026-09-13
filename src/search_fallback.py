from src.search import SearchProvider, SearchResult


class SearchFallback:
    def __init__(self, provider: SearchProvider):
        self.provider = provider

    def find_evidence(
        self,
        company_domain: str,
        goal: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        queries = {
            "leadership": (
                f"site:{company_domain} leadership OR team OR executives"
            ),
            "contact_information": (
                f"site:{company_domain} contact OR sales OR email"
            ),
            "company_overview": (
                f"site:{company_domain} about OR company OR mission"
            ),
            "target_audience": (
                f"site:{company_domain} customers OR industries OR solutions"
            ),
        }

        query = queries.get(goal)

        if not query:
            return []

        return self.provider.search(
            query=query,
            max_results=max_results,
        )

    def find_linkedin_profiles(
        self,
        company_domain: str,
        max_results: int = 3,
    ) -> list[SearchResult]:
        """Discover candidate LinkedIn leadership pages for browser validation."""
        return self.provider.search(
            query=(
                f'site:linkedin.com/in "{company_domain}" '
                '(CEO OR founder OR co-founder OR executive)'
            ),
            max_results=max_results,
        )
