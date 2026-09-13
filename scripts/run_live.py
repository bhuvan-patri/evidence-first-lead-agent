"""Manually run the real Playwright + Gemini pipeline (not collected by pytest)."""

from pathlib import Path
import sys

# Support the README command (`python scripts/run_live.py`) without requiring
# callers to manually set PYTHONPATH.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent import LeadEnrichmentAgent


if __name__ == "__main__":
    agent = LeadEnrichmentAgent(headless=True, max_pages=5)
    for result in agent.enrich_domains(["postman.com", "supabase.com", "vapi.ai"]):
        print(result["profile"].model_dump_json(indent=2) if result["profile"] else result)
    print(agent.telemetry_summary())
