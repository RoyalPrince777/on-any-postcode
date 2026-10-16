"""Regression checks for NIRMATA's bounded structural review."""

from mission_control.nirmata_research import research_blueprint
from mission_control.nirmata_review_alliance import (
    NIRMATA_OVERSIGHT_SYSTEMS,
    NIRMATA_REVIEW_ROLES,
    inspect_nirmata_blueprint,
    nirmata_review_plan,
)


def _record(sources=None):
    return research_blueprint(
        question="What improves recovery?",
        domain="software",
        sources={"source-1": "Reference, 2025"} if sources is None else sources,
        hypotheses=["Redundancy may help"],
        lenses=["structure", "repair"],
    )


def test_review_is_structural_not_scientific_or_autonomous():
    result = inspect_nirmata_blueprint(_record())
    assert result["passed"] is True
    assert result["findings"] == []
    assert result["scientific_validity_verified"] is False
    assert result["external_sources_verified"] is False
    assert result["specialist_votes_executed"] == 0
    assert result["earned_stars"] is None


def test_missing_sources_fail_closed():
    result = inspect_nirmata_blueprint(_record({}))
    assert result["passed"] is False
    assert {f["code"] for f in result["findings"]} >= {
        "EVIDENCE_MISSING_OR_UNEXPECTED",
        "NO_SOURCE_REFERENCES",
    }


def test_tampering_and_authority_violation_are_rejected():
    record = _record()
    record["execution_authorised"] = True
    record["medical_diagnosis_authorised"] = True
    record["identity_issuance_authorised"] = True
    result = inspect_nirmata_blueprint(record)
    assert result["passed"] is False
    assert {f["code"] for f in result["findings"]} >= {
        "INTEGRITY_NOT_VERIFIED",
        "EXECUTION_BOUNDARY_VIOLATION",
        "MEDICAL_BOUNDARY_VIOLATION",
        "IDENTITY_BOUNDARY_VIOLATION",
    }


def test_invalid_record_fails_closed():
    result = inspect_nirmata_blueprint(None)
    assert result["passed"] is False
    assert result["findings"] == [
        {"reviewer_role": "agent_smith", "code": "INVALID_RECORD"}
    ]


def test_registry_is_advisory_and_organs_remain_systems():
    plan = nirmata_review_plan()
    assert plan["execution_authorised"] is False
    assert plan["reviews_executed"] == 0
    assert plan["verified_votes"] == 0
    assert plan["earned_stars"] is None
    assert "neo" in NIRMATA_REVIEW_ROLES
    assert "living_kernel" in NIRMATA_OVERSIGHT_SYSTEMS
    assert "living_kernel" not in NIRMATA_REVIEW_ROLES
    assert "aegis" not in NIRMATA_REVIEW_ROLES
