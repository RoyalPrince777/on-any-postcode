"""Fox V2 fail-closed advisory checks."""
import pytest

from mission_control.fox_intelligence import (
    assess_mission,
    evidence_valid,
    rank_alternatives,
)


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
    fox = {"agent": "Fox", "mode": "advisory", "production_gate": "blocked", "founder_final": True, "recommended": "route_a"}
    foxy = {"agent": "Foxy", "mode": "advisory", "production_gate": "blocked", "founder_final": True, "recommended": "route_b"}
    result = compare_fox_assessments(fox=fox, foxy=foxy)
    assert result["needs_review"] is True
    assert result["production_gate"] == "blocked"
    assert result["rank_change"] is None
    assert result["agents"]["Fox"]["recommended"] == "route_a"


def test_fox_foxy_rejects_identity_spoofing():
    from mission_control.fox_intelligence import compare_fox_assessments
    with pytest.raises(ValueError):
        compare_fox_assessments(fox={"agent": "Foxy", "mode": "advisory", "production_gate": "blocked"}, foxy={"agent": "Foxy", "mode": "advisory", "production_gate": "blocked"})


def test_comparison_rejects_missing_founder_final():
    from mission_control.fox_intelligence import compare_fox_assessments
    fox = {"agent": "Fox", "mode": "advisory", "production_gate": "blocked", "founder_final": True}
    foxy = {"agent": "Foxy", "mode": "advisory", "production_gate": "blocked"}
    with pytest.raises(ValueError):
        compare_fox_assessments(fox=fox, foxy=foxy)


def test_comparison_rejects_invalid_recommendation():
    from mission_control.fox_intelligence import compare_fox_assessments
    fox = {"agent": "Fox", "mode": "advisory", "production_gate": "blocked", "founder_final": True, "recommended": 5}
    foxy = {"agent": "Foxy", "mode": "advisory", "production_gate": "blocked", "founder_final": True}
    with pytest.raises(ValueError):
        compare_fox_assessments(fox=fox, foxy=foxy)


def test_foxy_uses_same_fail_closed_evidence_gate():
    from mission_control.fox_intelligence import assess_foxy_mission
    result = assess_foxy_mission(evidence={}, alternatives=[], dissent=[], recovery={})
    assert result["agent"] == "Foxy"
    assert result["production_gate"] == "blocked"
    assert result["founder_final"] is True


def test_foxy_can_disagree_with_fox_without_execution():
    from mission_control.fox_intelligence import (
        assess_foxy_mission,
        compare_fox_assessments,
    )
    options = [
        {"name": "safe", "cost": 2, "risk": 1, "dependencies": 1, "reversible": True},
        {"name": "alternate", "cost": 1, "risk": 2, "dependencies": 1, "reversible": True},
    ]
    fox = assess_mission(evidence={}, alternatives=options, dissent=[], recovery={})
    foxy = assess_foxy_mission(evidence={}, alternatives=[options[1]], dissent=[], recovery={})
    result = compare_fox_assessments(fox=fox, foxy=foxy)
    assert result["needs_review"] is True
    assert result["recommendations"] == {"Fox": "safe", "Foxy": "alternate"}
    assert result["production_gate"] == "blocked"


def test_fox_route_reconnaissance_skips_blocked_route():
    from mission_control.fox_intelligence import assess_fox_routes

    routes = [
        {"name": "blocked", "cost": 0, "risk": 0, "dependencies": 0, "reversible": True},
        {"name": "alternative", "cost": 2, "risk": 1, "dependencies": 1, "reversible": True},
    ]
    result = assess_fox_routes(routes=routes, blocked_route_names=["blocked"])
    assert result["agent"] == "Fox"
    assert result["recommended"] == "alternative"
    assert result["blocked_routes"] == ["blocked"]
    assert result["production_gate"] == "blocked"
    assert result["route_data_verified"] is False


def test_fox_routes_fail_closed_on_duplicate_names():
    from mission_control.fox_intelligence import assess_fox_routes

    route = {"name": "a", "cost": 1, "risk": 1, "dependencies": 1, "reversible": True}
    with pytest.raises(ValueError):
        assess_fox_routes(routes=[route, route])


def test_fox_routes_no_candidates_never_claim_navigation():
    from mission_control.fox_intelligence import assess_fox_routes

    result = assess_fox_routes(routes=[])
    assert result["recommended"] is None
    assert "live_navigation_proof" in result["missing"]


def test_foxy_prefers_reversible_contingency_and_fox_prefers_low_risk():
    from mission_control.fox_intelligence import compare_route_strategies

    routes = [
        {"name": "low-risk", "cost": 1, "risk": 0, "dependencies": 0, "reversible": False},
        {"name": "reversible", "cost": 2, "risk": 1, "dependencies": 0, "reversible": True},
    ]
    result = compare_route_strategies(routes=routes)
    assert result["recommendations"] == {"Fox": "low-risk", "Foxy": "reversible"}
    assert result["needs_review"] is True
    assert result["production_gate"] == "blocked"


def test_foxy_route_exclusions_share_fox_validation():
    from mission_control.fox_intelligence import assess_foxy_routes

    routes = [
        {"name": "closed", "cost": 0, "risk": 0, "dependencies": 0, "reversible": True},
        {"name": "open", "cost": 1, "risk": 1, "dependencies": 0, "reversible": True},
    ]
    result = assess_foxy_routes(routes=routes, blocked_route_names=["closed"])
    assert result["recommended"] == "open"
    assert result["blocked_routes"] == ["closed"]
    assert result["route_data_verified"] is False
    assert result["founder_final"] is True


@pytest.mark.parametrize("missing", [
    "source", "reference", "observation", "backup_reference",
    "rollback_procedure", "test_passed", "runtime_observed", "human_approved",
])
def test_each_missing_production_proof_blocks_independently(missing):
    evidence = {"source": "CI", "reference": "run-1", "observation": "passed"}
    recovery = {"backup_reference": "bundle", "rollback_procedure": "restore bundle"}
    flags = {"test_passed": True, "runtime_observed": True, "human_approved": True}
    if missing in evidence:
        evidence[missing] = " "
    elif missing in recovery:
        recovery[missing] = " "
    else:
        flags[missing] = False
    result = assess_mission(evidence=evidence, alternatives=[], dissent=[], recovery=recovery, **flags)
    assert result["production_gate"] == "blocked"
    assert result["founder_final"] is True
    assert result["missing"]
