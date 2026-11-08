"""A5/A6 percentages are measured; A7 uses grouped Founder gates."""

from mission_control import a7_certification


def test_unreachable_proof_store_has_unknown_percentages(monkeypatch):
    monkeypatch.setattr(
        a7_certification, "_production_counts",
        lambda: {"store_reachable": False, "guardian_passes": 0,
                 **{key: 0 for key in (
                     "a6_independent_proof", "a6_operation_approval",
                     "a6_operation_rollback", "a6_consequential_receipt_chain",
                     "a7_external_audit", "a7_legal_compliance",
                     "a7_emergency_halt", "a7_public_private_boundary",
                     "a7_constitutional_review")}},
    )
    monkeypatch.setattr(
        a7_certification.smi_proof_gate, "status", lambda: {"green": False, "checks": {}}
    )
    monkeypatch.setattr(a7_certification, "_capability_allowlist_ready", lambda: True)
    result = a7_certification.status()
    for level, total in (("a5", 8), ("a6", 11)):
        assert result["readiness"][level]["total"] == total
        assert result["readiness"][level]["percent"] is None
    assert result["readiness"]["a7"]["review"] == "five_grouped_gates"
    assert result["readiness"]["a7"]["percent"] is None
    assert result["readiness"]["a7"]["ready"] is False
    assert all(value is None for value in result["readiness"]["a7"]["gates"].values())
    assert result["readiness"]["evidence_available"] is False
    assert result["certification_granted"] is False


def test_reachable_store_counts_controls_but_never_certifies(monkeypatch):
    counts = {
        "store_reachable": True,
        "guardian_passes": 1,
        "a6_independent_proof": 0,
        "a6_operation_approval": 0,
        "a6_operation_rollback": 0,
        "a6_consequential_receipt_chain": 0,
        "a7_external_audit": 0,
        "a7_legal_compliance": 0,
        "a7_emergency_halt": 0,
        "a7_public_private_boundary": 0,
        "a7_constitutional_review": 0,
    }
    monkeypatch.setattr(a7_certification, "_production_counts", lambda: counts)
    monkeypatch.setattr(
        a7_certification.smi_proof_gate, "status",
        lambda: {"green": False, "checks": {
            "receipt_chain": False,
            "rollback_recovery": False,
            "observability": False,
        }},
    )
    monkeypatch.setattr(a7_certification, "_capability_allowlist_ready", lambda: True)
    result = a7_certification.status()
    assert result["readiness"]["a5"] == {"passed": 2, "total": 8, "percent": 25.0}
    assert result["readiness"]["a6"] == {"passed": 2, "total": 11, "percent": 18.2}
    assert result["readiness"]["a7"] == {
        "review": "five_grouped_gates",
        "gates": {
            "a6_foundation": False,
            "independent_assurance": False,
            "operational_stop": False,
            "privacy_boundary": False,
            "constitutional_founder": False,
        },
        "ready": False,
        "percent": None,
    }
    assert result["a6_proof_complete"] is False
    assert result["a7_enabled"] is False
