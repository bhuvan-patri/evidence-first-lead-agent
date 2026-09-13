from src.site_analyzer import SiteAnalyzer


DOMAINS = [
    "postman.com",
    "supabase.com",
    "vapi.ai",
]


def main():
    analyzer = SiteAnalyzer(headless=True, max_pages=5)

    for domain in DOMAINS:
        print("\n" + "=" * 70)
        print(f"ANALYZING: {domain}")
        print("=" * 70)

        try:
            result = analyzer.analyze(domain)

            if not result["success"]:
                print(f"FAILED: {result['error']}")
                continue

            print(f"Pages discovered: {result['pages_discovered']}")
            print(f"Pages selected: {result['pages_selected']}")

            print("\nSelected evidence pages:")

            for page in result["pages"]:
                print(
                    f"- [{page.get('goal', 'homepage')}] "
                    f"{page['url']}"
                )

        except Exception as exc:
            print(
                f"UNEXPECTED ERROR: "
                f"{type(exc).__name__}: {exc}"
            )


if __name__ == "__main__":
    main()