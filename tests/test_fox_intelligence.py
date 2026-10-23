"""Fox V2 fail-closed advisory checks."""
import pytest

from mission_control.fox_intelligence import assess_mission, evidence_valid, rank_alternatives


def test_evidence_requires_traceable_observation():
    assert not evidence_valid({"source": "git", "reference": "sha"})
    assert evidence_valid({"source": "git", "reference": "abc", "observation": "diff inspected"})


def test_rank_prefers_low_risk_reversible():
    options = [
        {"name": "risky", "cost": 0, "risk": 4, "dependencies": 0, "reversible": True},
        {"name": "safe", "cost": 3, "risk": 1, "dependencies": 1, "reversible": True},
    ]
    assert rank_alternatives(options)[0]["name"] == "safe"


def test_invalid_scores_fail_closed():
    with pytest.raises(ValueError):
        rank_alternatives([{"name": "bad", "cost": -1, "risk": 0, "dependencies": 0, "reversible": True}])


def test_no_proof_never_green():
    result = assess_mission(evidence={}, alternatives=[], dissent=[], recovery={})
    assert result["production_gate"] == "blocked"
    assert result["founder_final"] is True


def test_dissent_requires_evidence():
    with pytest.raises(ValueError):
        assess_mission(evidence={}, alternatives=[], dissent=[{"agent": "Neo", "reason": "No"}], recovery={})


def test_all_evidence_still_only_eligible_for_human_review():
    result = assess_mission(
        evidence={"source": "CI", "reference": "run-1", "observation": "passed"},
        alternatives=[], dissent=[],
        recovery={"backup_reference": "bundle", "rollback_procedure": "restore bundle"},
        test_passed=True, runtime_observed=True, human_approved=True,
    )
    assert result["production_gate"] == "eligible_for_human_review"


def test_fox_foxy_independent_comparison_blocks_execution():
    from mission_control.fox_intelligence import compare_fox_assessments
    fox = {"agent": "Fox", "mode": "advisory", "production_gate": "blocked", "recommended": "route_a"}
    foxy = {"agent": "Foxy", "mode": "advisory", "production_gate": "blocked", "recommended": "route_b"}
    result = compare_fox_assessments(fox=fox, foxy=foxy)
    assert result["needs_review"] is True
    assert result["production_gate"] == "blocked"
    assert result["rank_change"] is None
    assert result["agents"]["Fox"]["recommended"] == "route_a"


def test_fox_foxy_rejects_identity_spoofing():
    from mission_control.fox_intelligence import compare_fox_assessments
    with pytest.raises(ValueError):
        compare_fox_assessments(fox={"agent": "Foxy", "mode": "advisory", "production_gate": "blocked"}, foxy={"agent": "Foxy", "mode": "advisory", "production_gate": "blocked"})
