"""Domain-specific Raffles Mind tests: no Matrix engine or generic audit duplication."""
from oap.raffles_mind import REQUIRED, Triage, assess


def complete_evidence():
    return {key: "unverified-document-reference" for key in REQUIRED}


def test_free_draw_missing_documents_requests_evidence():
    result = assess(territory="uk", kind="free_draw", sponsor_funded=True)
    assert result.decision == Triage.REQUEST_EVIDENCE
    assert result.missing == REQUIRED
    assert not result.execution_granted


def test_complete_claims_escalate_not_approve():
    result = assess(territory="uk", kind="free_draw",
                    evidence=complete_evidence(), sponsor_funded=True)
    assert result.decision == Triage.ESCALATE
    assert not result.evidence_verified
    assert not result.founder_approved
    assert result.actual_matrix_votes == ()
    assert not result.execution_granted


def test_paid_model_stays_blocked_with_evidence():
    for kind in ("paid_skill", "dual_route"):
        result = assess(territory="uk", kind=kind, evidence=complete_evidence(),
                        sponsor_funded=True)
        assert result.decision == Triage.BLOCK
        assert "paid_model_requires_separate_authorisation" in result.reasons


def test_property_requires_independent_title_review():
    result = assess(territory="uk", kind="property_prize",
                    evidence=complete_evidence(), sponsor_funded=True)
    assert result.decision == Triage.BLOCK
    assert "property_title_transfer_and_tax_review_required" in result.reasons


def test_global_is_not_automatic_worldwide_eligibility():
    result = assess(territory="global", kind="free_draw",
                    evidence=complete_evidence(), sponsor_funded=True)
    assert result.decision == Triage.BLOCK
    assert "country_specific_eligibility_review_required" in result.reasons


def test_zero_capital_and_unfunded_supplier_fail_closed():
    result = assess(territory="uk", kind="free_draw",
                    evidence=complete_evidence(), cash_required=True)
    assert result.decision == Triage.BLOCK
    assert "zero_capital_requirement_violated" in result.reasons
    assert "sponsor_funding_unconfirmed" in result.reasons


def test_unsupported_and_malformed_inputs_fail_closed():
    for territory, kind in (("unknown", "free_draw"), ("uk", "unknown")):
        result = assess(territory=territory, kind=kind, sponsor_funded=True)
        assert result.decision == Triage.BLOCK
    result = assess(territory="uk", kind="free_draw", evidence={"fulfilment": 42},
                    sponsor_funded=True)
    assert "fulfilment" in result.missing
