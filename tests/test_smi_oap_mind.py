"""Focused source tests for Octopus OAP MIND's evidence assessment contract."""

import pytest

from oap.smi.oap_mind import OAPEvidence, assess_oap_evidence


def test_missing_proof_investigates_instead_of_inventing_green() -> None:
    result = assess_oap_evidence("Octopus runs on device", ())
    assert result.verdict == "INVESTIGATE"
    assert result.missing_proof == ("source",)
    assert result.confidence == "INSUFFICIENT"
    assert result.advisory_only and result.founder_final
    assert not result.runtime_certified


def test_unverified_record_does_not_create_verified_confidence() -> None:
    evidence = (
        OAPEvidence("repo:octopus-definition", "source", "Octopus mapped"),
    )
    result = assess_oap_evidence("Octopus mapped", evidence)
    assert result.verdict == "INVESTIGATE"
    assert result.unverified_references == ("repo:octopus-definition",)


def test_contradiction_holds_even_with_a_supporting_receipt() -> None:
    evidence = (
        OAPEvidence("ci:pass", "ci", "CI passed", verified_receipt=True),
        OAPEvidence(
            "ci:fail", "ci", "CI passed", supports_claim=False,
            verified_receipt=True,
        ),
    )
    result = assess_oap_evidence("CI passed", evidence, required_kinds=("ci",))
    assert result.verdict == "HOLD"
    assert result.confidence == "CONFLICTED"
    assert result.contradicting_references == ("ci:fail",)


def test_receipts_only_make_claim_review_ready_not_runtime_certified() -> None:
    evidence = (
        OAPEvidence("source:sha", "source", "Capability mapped", verified_receipt=True),
        OAPEvidence("ci:run", "ci", "Capability mapped", verified_receipt=True),
    )
    result = assess_oap_evidence(
        "Capability mapped", evidence, required_kinds=("source", "ci")
    )
    assert result.verdict == "REVIEW_READY"
    assert result.confidence == "RECEIPTS_PRESENT_NOT_INDEPENDENTLY_VERIFIED"
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
