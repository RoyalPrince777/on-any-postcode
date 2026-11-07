"""Focused protection against forged evidence and false Green Gate claims."""

import pytest

from oap.smi.oap_mind import OAPEvidence, assess_oap_evidence, assess_smi_agent_claim


def test_missing_proof_investigates_instead_of_inventing_green() -> None:
    result = assess_oap_evidence("Octopus runs on device", ())
    assert result.verdict == "INVESTIGATE"
    assert result.missing_proof == ("source",)
    assert result.confidence == "UNVERIFIED"
    assert result.next_evidence_action == "RETRIEVE_AND_AUTHENTICATE_OAP_PROOF"
    assert result.advisory_only and result.founder_final
    assert not result.runtime_certified


def test_unverified_record_does_not_create_verified_confidence() -> None:
    evidence = (
        OAPEvidence("repo:octopus-definition", "source", "Octopus mapped"),
    )
    result = assess_oap_evidence("Octopus mapped", evidence)
    assert result.verdict == "INVESTIGATE"
    assert result.unverified_references == ("repo:octopus-definition",)


def test_contradiction_holds_even_with_claimed_receipts() -> None:
    evidence = (
        OAPEvidence("ci:pass", "ci", "CI passed", verified_receipt=True),
        OAPEvidence(
            "ci:fail", "ci", "CI passed", supports_claim=False,
            verified_receipt=True,
        ),
    )
    result = assess_oap_evidence("CI passed", evidence, required_kinds=("ci",))
    assert result.verdict == "HOLD"
    assert result.confidence == "CONFLICTED_UNVERIFIED"
    assert result.next_evidence_action == "RESOLVE_CONTRADICTORY_OAP_RECORDS"
    assert result.contradicting_references == ("ci:fail",)


def test_forged_receipt_boolean_cannot_make_claim_review_ready() -> None:
    evidence = (
        OAPEvidence("source:sha", "source", "Capability mapped", verified_receipt=True),
        OAPEvidence("ci:run", "ci", "Capability mapped", verified_receipt=True),
    )
    result = assess_oap_evidence(
        "Capability mapped", evidence, required_kinds=("source", "ci")
    )
    assert result.verdict == "INVESTIGATE"
    assert result.confidence == "UNVERIFIED"
    assert result.missing_proof == ("source", "ci")
    assert result.unverified_references == ("source:sha", "ci:run")
    assert not result.runtime_certified
    assert result.advisory_only and result.founder_final


@pytest.mark.parametrize(
    "claim,evidence,required",
    [
        ("", (), ("source",)),
        ("ok", (), ()),
        ("ok", (OAPEvidence("", "source", "ok"),), ("source",)),
        ("ok", (OAPEvidence("id", "source", ""),), ("source",)),
        ("ok", (OAPEvidence("id", "unknown", "ok"),), ("source",)),
        (
            "ok",
            (OAPEvidence("id", "source", "ok"),
             OAPEvidence("id", "ci", "ok")),
            ("source",),
        ),
        ("ok", (OAPEvidence("id", "source", "ok", supports_claim="yes"),), ("source",)),
        ("ok", [OAPEvidence("id", "source", "ok")], ("source",)),
    ],
)
def test_invalid_or_ambiguous_inputs_fail_closed(claim, evidence, required) -> None:
    with pytest.raises(ValueError):
        assess_oap_evidence(claim, evidence, required_kinds=required)


def test_unrelated_claim_cannot_count_as_evidence() -> None:
    result = assess_oap_evidence(
        "Runtime verified",
        (OAPEvidence("source:123", "source", "Code exists", verified_receipt=True),),
    )
    assert result.verdict == "INVESTIGATE"
    assert result.missing_proof == ("source",)
    assert result.supporting_references == ()


def test_cross_agent_claim_remains_advisory_and_unverified() -> None:
    review = assess_smi_agent_claim(
        "Neo",
        "Neo deployed",
        (OAPEvidence("agent:claimed", "runtime", "Neo deployed", verified_receipt=True),),
        required_kinds=("runtime",),
    )
    assert review.agent_name == "Neo"
    assert review.assessment.verdict == "INVESTIGATE"
    assert review.assessment.missing_proof == ("runtime",)
    assert review.independent_review_required
    assert not review.independent_review_verified
    assert not review.permissions_granted
    assert not review.council_vote_recorded
    assert review.assessment.founder_final


def test_octopus_cannot_self_certify() -> None:
    review = assess_smi_agent_claim(
        "Octopus", "OAP MIND is production ready",
        (OAPEvidence("caller:receipt", "ci", "OAP MIND is production ready",
                     verified_receipt=True),),
        required_kinds=("ci",),
    )
    assert review.assessment.verdict != "REVIEW_READY"
    assert not review.independent_review_verified
    assert not review.assessment.runtime_certified


def test_cross_agent_contradiction_holds_and_empty_agent_rejected() -> None:
    records = (OAPEvidence("test:failure", "test", "Agent works", False),)
    review = assess_smi_agent_claim("Owl", "Agent works", records)
    assert review.assessment.verdict == "HOLD"
    with pytest.raises(ValueError):
        assess_smi_agent_claim(" ", "Agent works", records)
