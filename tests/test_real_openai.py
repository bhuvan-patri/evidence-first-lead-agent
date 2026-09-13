from src.evidence_pack import EvidenceItem, EvidencePack
from src.openai_extractor import OpenAIExtractor


def main():
    evidence = EvidencePack(company_domain="example.com")

    evidence.add(
        EvidenceItem(
            field="company_overview",
            value="Example Analytics builds cloud software for business analytics.",
            source_url="https://example.com/about",
            source_type="company_website",
        )
    )

    evidence.add(
        EvidenceItem(
            field="target_audience",
            value="The platform is designed for enterprise data teams and business analysts.",
            source_url="https://example.com/solutions",
            source_type="company_website",
        )
    )

    extractor = OpenAIExtractor()

    result = extractor.extract(evidence)

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()