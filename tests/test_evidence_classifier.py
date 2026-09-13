from src.evidence_classifier import EvidenceClassifier


def test_page_can_support_multiple_goals():
    classifier = EvidenceClassifier()

    text = """
    Our leadership team includes Jane Doe, CEO and founder.
    We build solutions for developers and enterprise teams.
    Contact our sales team at sales@example.com.
    """

    signals = classifier.classify(text)
    goals = {signal.goal for signal in signals}

    assert "leadership" in goals
    assert "target_audience" in goals
    assert "contact_information" in goals


def test_contact_email_is_strong_evidence():
    classifier = EvidenceClassifier()

    text = "Contact sales at sales@example.com."

    signals = classifier.classify(text)

    contact_signal = next(
        signal
        for signal in signals
        if signal.goal == "contact_information"
    )

    assert contact_signal.strength == "strong"


def test_personal_email_does_not_complete_generic_contact_goal():
    signals = EvidenceClassifier().classify("Reach Jane at jane.doe@example.com.")

    assert "contact_information" not in {signal.goal for signal in signals}


def test_contact_cta_without_a_generic_email_does_not_complete_goal():
    signals = EvidenceClassifier().classify("Contact our sales team to book a demo.")

    assert "contact_information" not in {signal.goal for signal in signals}


def test_company_leadership_role_is_strong_evidence():
    classifier = EvidenceClassifier()

    text = "Our Chief Technology Officer, Jane Doe, leads the engineering organization."

    signals = classifier.classify(text)

    leadership_signal = next(
        signal
        for signal in signals
        if signal.goal == "leadership"
    )

    assert leadership_signal.strength == "strong"


def test_standalone_external_role_is_not_strong_leadership_evidence():
    classifier = EvidenceClassifier()

    text = "Jane Doe is the Chief Technology Officer."

    signals = classifier.classify(text)

    leadership_signals = [
        signal
        for signal in signals
        if signal.goal == "leadership"
    ]

    assert not leadership_signals


def test_empty_text_returns_no_signals():
    classifier = EvidenceClassifier()

    assert classifier.classify("") == []


def test_sales_qualification_language_is_not_icp_evidence():
    classifier = EvidenceClassifier()
    text = (
        "The self-serve experience is not just for developers who stay self-serve. "
        "It is a demand qualification machine that makes the sales-assisted motion efficient."
    )

    assert "target_audience" not in {signal.goal for signal in classifier.classify(text)}


def test_built_for_developers_is_strong_icp_evidence():
    classifier = EvidenceClassifier()

    signal = next(signal for signal in classifier.classify(
        "Our API platform is built for developers and engineering teams."
    ) if signal.goal == "target_audience")

    assert signal.strength == "strong"


def test_customer_testimonial_cannot_be_company_overview_evidence():
    text = (
        "We never bought software for that. We just used Acme Platform to create it.\n"
        "Aleksei Petrov, Lead Engineer, Lovable"
    )

    signals = EvidenceClassifier().classify(text, "https://example.com/customers/lovable")

    assert "company_overview" not in {signal.goal for signal in signals}


def test_customer_case_study_cannot_be_company_overview_evidence():
    signals = EvidenceClassifier().classify(
        "We provide software for this workflow.",
        "https://example.com/case-studies/acme",
    )

    assert "company_overview" not in {signal.goal for signal in signals}


def test_generic_help_prompt_cannot_be_company_overview_evidence():
    signals = EvidenceClassifier().classify(
        "How can we help you?*",
        "https://example.com/sales",
    )

    assert "company_overview" not in {signal.goal for signal in signals}


def test_cta_and_form_text_cannot_be_company_overview_evidence():
    classifier = EvidenceClassifier()
    text = "Contact sales\nBook a demo\nWork email\nSubmit"

    assert "company_overview" not in {signal.goal for signal in classifier.classify(text)}


def test_legitimate_company_description_remains_overview_evidence():
    signals = EvidenceClassifier().classify(
        "About us\nWe provide a platform for developers to manage APIs.",
        "https://example.com/about",
    )

    assert "company_overview" in {signal.goal for signal in signals}


def test_leadership_heading_without_named_person_and_role_is_not_evidence():
    signals = EvidenceClassifier().classify("Leadership\nMeet the team")

    assert "leadership" not in {signal.goal for signal in signals}
