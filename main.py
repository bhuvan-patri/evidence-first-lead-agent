"""CLI for the Evidence-First Autonomous Lead Intelligence Agent."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from src.agent import LeadEnrichmentAgent

ASSIGNMENT_DOMAINS = ["postman.com", "supabase.com", "vapi.ai"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render company sites and enrich them with Gemini.")
    parser.add_argument("domains", nargs="*", help="Company domains (defaults to the three assignment domains).")
    parser.add_argument("--max-pages", type=int, default=int(os.getenv("MAX_PAGES", "5")))
    parser.add_argument("--headed", action="store_true", help="Show Chromium while browsing.")
    parser.add_argument("--output", default="outputs/lead_profiles.json", help="JSON result file path.")
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    domains = args.domains or ASSIGNMENT_DOMAINS
    agent = LeadEnrichmentAgent(headless=not args.headed, max_pages=args.max_pages)
    results = agent.enrich_domains(domains)
    payload = {
        "results": [result | {"profile": result["profile"].model_dump() if result.get("profile") else None} for result in results],
        "telemetry_summary": agent.telemetry_summary(),
    }
    print(json.dumps(payload, indent=2))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    successful = sum(result["success"] for result in results)
    print(f"\nSaved {len(results)} domain result(s) to {output} ({successful} successful).")
    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    load_dotenv()
    raise SystemExit(main())
