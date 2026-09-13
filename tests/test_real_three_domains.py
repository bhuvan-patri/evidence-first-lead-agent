from src.agent import LeadEnrichmentAgent


DOMAINS = [
    "postman.com",
    "supabase.com",
    "vapi.ai",
]


def main():
    agent = LeadEnrichmentAgent(
        headless=True,
        max_pages=5,
    )

    results = agent.enrich_domains(DOMAINS)

    for result in results:
        print("\n" + "=" * 80)
        print(f"DOMAIN: {result['domain']}")
        print("=" * 80)

        if not result["success"]:
            print("STATUS: FAILED")
            print(f"ERROR: {result['error']}")
            continue

        print("STATUS: SUCCESS")
        print(f"Pages discovered: {result['pages_discovered']}")
        print(f"Pages selected: {result['pages_selected']}")
        print(f"Evidence items: {result['evidence_items']}")

        print("\nLead Profile:")
        print(
            result["profile"].model_dump_json(
                indent=2
            )
        )

    print("\n" + "=" * 80)
    print("TELEMETRY")
    print("=" * 80)
    print(agent.telemetry_summary())


if __name__ == "__main__":
    main()