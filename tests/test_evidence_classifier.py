from src.evidence_classifier import EvidenceClassifier


def test_page_can_support_multiple_goals():
    classifier = EvidenceClassifier()

    text = """
    Our leadership team includes our CEO and founders.
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