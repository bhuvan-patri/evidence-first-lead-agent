from src.evidence_builder import EvidenceBuilder
from src.gemini_extractor import GeminiExtractor
from src.profile_builder import ProfileBuilder
from src.site_analyzer import SiteAnalyzer


def main():
    analyzer = SiteAnalyzer(headless=True, max_pages=3)

    print("Analyzing postman.com...")
    analysis = analyzer.analyze("postman.com")

    if not analysis["success"]:
        raise RuntimeError(analysis["error"])

    print(f"Pages discovered: {analysis['pages_discovered']}")
    print(f"Pages selected: {analysis['pages_selected']}")

    builder = EvidenceBuilder()
    evidence = builder.build(analysis)

    print(f"Evidence items: {len(evidence.items)}")

    extractor = GeminiExtractor()
    draft = extractor.extract(evidence)

    profile_builder = ProfileBuilder()
    result = profile_builder.build(
        draft=draft,
        evidence=evidence,
    )

    print("\nFinal Lead Profile:")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()