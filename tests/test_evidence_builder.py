from src.evidence_builder import EvidenceBuilder


def test_builder_extracts_compact_first_party_evidence():
    analysis = {
        "domain": "https://example.com",
        "pages": [{
            "url": "https://example.com/about",
            "success": True,
            "content": (
                "About us\nWe build an API platform for developers.\n"
                "Designed for engineering teams.\nContact sales@example.com."
            ),
            "sections": [
                {"heading": "About us", "content": "We build an API platform for developers. Designed for engineering teams."},
                {"heading": "Contact", "content": "Contact sales@example.com."},
            ],
        }],
    }
    evidence = EvidenceBuilder().build(analysis)
    assert {item.field for item in evidence.items} == {
        "company_overview", "target_audience", "contact_information"
    }
    assert all(item.source_type == "company_website" for item in evidence.items)


def test_builder_rejects_pricing_and_testimonial_as_company_evidence():
    analysis = {
        "domain": "https://example.com",
        "pages": [{
            "url": "https://example.com/pricing",
            "success": True,
            "content": (
                "Pricing\nBuilt for AI builders on our Pro plan.\n"
                "Customer story\nJordan Doe, VP of Engineering at Acme, loves us."
            ),
            "sections": [
                {"heading": "Pricing", "content": "Built for AI builders on our Pro plan."},
                {"heading": "Customer story", "content": "Jordan Doe, VP of Engineering at Acme, loves us."},
            ],
        }],
    }
    assert EvidenceBuilder().build(analysis).items == []


def test_builder_uses_direct_company_description_for_overview():
    analysis = {
        "domain": "https://example.com",
        "pages": [{
            "url": "https://example.com/company",
            "success": True,
            "content": "About the company\nWe provide a platform for developers to manage APIs.",
            "sections": [
                {"heading": "Product features", "content": "Automated workflows and integrations."},
                {"heading": "About the company", "content": "We provide a platform for developers to manage APIs."},
            ],
        }],
    }

    overview = EvidenceBuilder().build(analysis).for_goal("company_overview")

    assert len(overview) == 1
    assert overview[0].value.startswith("We provide a platform")


def test_builder_does_not_promote_testimonial_people_to_leadership():
    analysis = {
        "domain": "https://example.com",
        "pages": [{
            "url": "https://example.com/customers/acme",
            "success": True,
            "content": "Customer story\nJordan Doe, VP of Engineering at Acme, uses the platform.",
            "sections": [{"heading": "Customer story", "content": "Jordan Doe, VP of Engineering at Acme, uses the platform."}],
        }],
    }

    assert EvidenceBuilder().build(analysis).for_goal("leadership") == []


def test_builder_preserves_first_party_linkedin_profile_urls_for_leadership():
    analysis = {
        "domain": "https://example.com",
        "pages": [{
            "url": "https://example.com/team",
            "success": True,
            "content": "Meet the team\nJane Doe\nChief Executive Officer",
            "sections": [{
                "heading": "Meet the team",
                "content": "Jane Doe\nChief Executive Officer",
            }],
            "links": [{
                "href": "https://www.linkedin.com/in/jane-doe/",
                "text": "Jane Doe",
            }],
        }],
    }

    leadership = EvidenceBuilder().build(analysis).for_goal("leadership")

    assert len(leadership) == 1
    assert "https://www.linkedin.com/in/jane-doe/" in leadership[0].value


def test_builder_rejects_customer_story_overview_by_path_and_quote_context():
    analysis = {
        "domain": "https://example.com",
        "pages": [{
            "url": "https://example.com/customers/lovable",
            "success": True,
            "content": (
                "We never bought software for that. We just used Example Platform to create it.\n"
                "Aleksei Petrov, Lead Engineer, Lovable"
            ),
            "sections": [],
        }],
    }

    assert EvidenceBuilder().build(analysis).for_goal("company_overview") == []


def test_builder_rejects_sales_form_prompt_as_overview():
    analysis = {
        "domain": "https://example.com",
        "pages": [{
            "url": "https://example.com/sales",
            "success": True,
            "content": "How can we help you?*\nContact sales\nWork email",
            "sections": [],
        }],
    }

    assert EvidenceBuilder().build(analysis).for_goal("company_overview") == []
