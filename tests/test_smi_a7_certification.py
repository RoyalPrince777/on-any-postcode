from __future__ import annotations

import pytest

from mission_control import a7_certification


def _all_counts(value: int = 1) -> dict[str, object]:
    return {
        "store_reachable": True,
        "guardian_passes": value,
        "a6_independent_proof": value,
        "a6_operation_approval": value,
        "a6_operation_rollback": value,
        "a6_consequential_receipt_chain": value,
        "a7_external_audit": value,
        "a7_legal_compliance": value,
        "a7_emergency_halt": value,
        "a7_public_private_boundary": value,
        "a7_constitutional_review": value,
        "error": None,
    }


def _green_lower_gate() -> dict[str, object]:
    return {
        "green": True,
        "checks": {
            "receipt_chain": True,
            "rollback_recovery": True,
            "observability": True,
        },
    }


def test_a7_emergency_halt_denies_new_work_and_requires_human_resume():
    proof = a7_certification._emergency_halt_exercise()

    assert proof["passed"] is True
    assert proof["halt_signal_observed"] is True
    assert proof["new_work_denied"] is True
    assert proof["safe_state_reached"] is True
    assert proof["human_resume_required"] is True
    assert proof["automatic_resume_allowed"] is False
    assert proof["production_state_mutated"] is False
    assert proof["execution_authority_expanded"] is False


def test_a7_gate_can_be_ready_without_enabling_a7(monkeypatch):
    monkeypatch.setattr(a7_certification, "_production_counts", lambda: _all_counts())
    monkeypatch.setattr(a7_certification.smi_proof_gate, "status", _green_lower_gate)
    monkeypatch.setattr(a7_certification, "_capability_allowlist_ready", lambda: True)

    snapshot = a7_certification.status()

    assert snapshot["a6_proof_complete"] is True
    assert snapshot["ready_for_founder_certification"] is True
    assert snapshot["a7_missing"] == ()
    assert snapshot["certification_granted"] is False
    assert snapshot["a7_enabled"] is False
    assert snapshot["execution_granted"] is False
    assert snapshot["authority_moves_with_level"] is False
    assert snapshot["human_authority_final"] is True


def test_a7_fails_closed_when_external_assurance_is_missing(monkeypatch):
    counts = _all_counts()
    counts["a7_external_audit"] = 0
    monkeypatch.setattr(a7_certification, "_production_counts", lambda: counts)
    monkeypatch.setattr(a7_certification.smi_proof_gate, "status", _green_lower_gate)
    monkeypatch.setattr(a7_certification, "_capability_allowlist_ready", lambda: True)

    snapshot = a7_certification.status()

    assert snapshot["ready_for_founder_certification"] is False
    assert snapshot["a7_checks"]["external_audit"] is False
    assert "external_audit" in snapshot["a7_missing"]
    assert snapshot["a7_enabled"] is False


def test_external_evidence_requires_external_attestor_before_database_use():
    with pytest.raises(ValueError, match="external_attestor_required"):
        a7_certification.record_evidence_reference(
            identity_id="00000000-0000-0000-0000-000000000001",
            assurance="a7_external_audit",
            evidence_ref="audit-report-1",
            evidence_hash="a" * 64,
            issuer="Example Auditor",
            scope="SMI A7",
            attestor_type="HUMAN_AUTHORITY",
        )


def test_evidence_reference_requires_sha256_before_database_use():
    with pytest.raises(ValueError, match="evidence_hash_must_be_sha256"):
        a7_certification.record_evidence_reference(
            identity_id="00000000-0000-0000-0000-000000000001",
            assurance="a7_legal_compliance",
            evidence_ref="legal-opinion-1",
            evidence_hash="not-a-hash",
            issuer="Example Legal Assessor",
            scope="SMI A7",
            attestor_type="EXTERNAL",
        )
