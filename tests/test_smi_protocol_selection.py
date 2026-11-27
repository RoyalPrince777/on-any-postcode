"""Negative boundaries for SMI advisory protocol recommendations."""
from oap.smi.protocol_selection import PROTOCOL_TEAMS, recommend_protocol_team


def test_all_28_protocols_have_unique_leads_and_no_duplicate_members():
    assert len(PROTOCOL_TEAMS) == 28
    for lead, specialists in PROTOCOL_TEAMS.values():
        assert lead
        assert lead not in specialists
        assert len(specialists) == len(set(specialists))


def test_known_team_is_advisory_and_unverified():
    result = recommend_protocol_team("stealth")
    assert result.lead == "Bagheera"
    assert result.status == "PROPOSED_UNVERIFIED"
    assert result.advisory_only
    assert not result.grants_permissions
    assert result.human_authority_final


def test_unknown_protocol_fails_closed():
    result = recommend_protocol_team("unregistered-protocol")
    assert result.lead is None
    assert result.specialists == ()
    assert result.status == "UNRECOGNISED"
    assert not result.grants_permissions


def test_non_string_input_fails_closed():
    assert recommend_protocol_team(None).status == "UNRECOGNISED"
    assert recommend_protocol_team({}).lead is None


def test_auto_mission_roles_are_advisory_and_unverified():
    from oap.smi.protocol_selection import recommend_mission_team

    result = recommend_mission_team("routing recovery", "recovery")
    assert result.lead == "Fox"
    assert result.deputy == "Dozer"
    assert result.challenger == "Shere Khan"
    assert result.verifier == "The Twins"
    assert result.recovery is None
    assert result.status == "PROPOSED_UNVERIFIED"
    assert not result.passport_verified
    assert not result.permissions_verified
    assert not result.evidence_verified
    assert not result.agent_execution_verified
    assert not result.grants_permissions
    assert result.human_authority_final


def test_mission_selection_rejects_unknown_and_invalid_depth():
    from oap.smi.protocol_selection import recommend_mission_team

    for mission, protocol, depth in [
        ("routing", "unknown", "AUTO"),
        ("", "recovery", "AUTO"),
        ("routing", "recovery", "unsafe"),
        (None, "recovery", "AUTO"),
    ]:
        result = recommend_mission_team(mission, protocol, depth)
        assert result.lead is None
        assert result.status == "UNRECOGNISED"
        assert not result.grants_permissions


def test_small_depth_does_not_assign_unneeded_reviewers():
    from oap.smi.protocol_selection import recommend_mission_team

    result = recommend_mission_team("small change", "creation", "3")
    assert result.lead == "NIRMATA"
    assert result.deputy == "Architect"
    assert result.specialists == ()
    assert result.challenger is None
    assert result.verifier is None


def test_candidate_eligibility_fails_closed_without_passport():
    from oap.smi.protocol_selection import check_mission_candidate_eligibility

    class Registry:
        def passport(self, agent_id):
            return None

    result = check_mission_candidate_eligibility("FOX-001", Registry())
    assert result["eligible"] is False
    assert result["reason"] == "PASSPORT_NOT_FOUND"
    assert result["grants_permissions"] is False


def test_candidate_eligibility_requires_active_permission_and_audit():
    from oap.smi.protocol_selection import check_mission_candidate_eligibility

    class Registry:
        def __init__(self, passport):
            self.record = passport

        def passport(self, agent_id):
            return self.record

    passport = {
        "agent_id": "FOX-001", "status": "ACTIVE",
        "permissions": ["ANALYSE"], "audit_required": True,
        "family_id": "recovery", "guardian": "Guardian",
        "memory": {}, "restrictions": [],
    }
    allowed = check_mission_candidate_eligibility("FOX-001", Registry(passport))
    assert allowed["eligible"] is True
    assert allowed["execution_verified"] is False
    assert allowed["performance_verified"] is False
    for update in (
        {"status": "INACTIVE"},
        {"permissions": []},
        {"audit_required": False},
    ):
        denied = check_mission_candidate_eligibility("FOX-001", Registry({**passport, **update}))
        assert denied["eligible"] is False


def test_candidate_eligibility_rejects_mismatched_identity_or_registry():
    from oap.smi.protocol_selection import check_mission_candidate_eligibility

    class Registry:
        def passport(self, agent_id):
            return {"agent_id": "OTHER", "status": "ACTIVE", "permissions": ["ANALYSE"]}

    assert not check_mission_candidate_eligibility("FOX-001", Registry())["eligible"]
    assert not check_mission_candidate_eligibility("FOX-001", object())["eligible"]


def test_team_screening_does_not_assume_names_are_passport_ids():
    from oap.smi.protocol_selection import (
        recommend_mission_team,
        screen_mission_team_candidates,
    )

    team = recommend_mission_team("routing", "recovery")
    screened = screen_mission_team_candidates(team, object())
    assert screened["all_eligible"] is False
    assert screened["candidates"]["Fox"]["reason"] == "PASSPORT_ID_UNRESOLVED"
    assert screened["agent_execution_verified"] is False
    assert screened["founder_final_required"] is True


def test_team_screening_partial_eligibility_never_promotes_team():
    from oap.smi.protocol_selection import (
        recommend_mission_team,
        screen_mission_team_candidates,
    )

    class Registry:
        def passport(self, agent_id):
            return {
                "agent_id": agent_id, "name": "Fox", "status": "ACTIVE",
                "permissions": ["ANALYSE"], "audit_required": True,
                "family_id": "recovery", "guardian": "Guardian",
                "memory": {}, "restrictions": [],
            }

    team = recommend_mission_team("routing", "recovery", "3")
    screened = screen_mission_team_candidates(team, Registry(), agent_ids={"Fox": "FOX-001"})
    assert screened["candidates"]["Fox"]["eligible"] is True
    assert screened["candidates"]["Dozer"]["eligible"] is False
    assert screened["all_eligible"] is False
    assert screened["grants_permissions"] is False


def test_registry_lookup_exception_fails_closed():
    from oap.smi.protocol_selection import check_mission_candidate_eligibility

    class BrokenRegistry:
        def passport(self, agent_id):
            raise RuntimeError("registry unavailable")

    result = check_mission_candidate_eligibility("FOX-001", BrokenRegistry())
    assert result["eligible"] is False
    assert result["reason"] == "REGISTRY_LOOKUP_FAILED"
    assert result["grants_permissions"] is False
    assert result["execution_verified"] is False


def test_candidate_name_must_match_registry_passport():
    from oap.smi.protocol_selection import check_mission_candidate_eligibility

    class Registry:
        def passport(self, agent_id):
            return {
                "agent_id": agent_id, "name": "James Bond", "aliases": ["007"],
                "status": "ACTIVE", "permissions": ["ANALYSE"],
                "audit_required": True, "family_id": "investigation",
                "guardian": "Guardian", "memory": {}, "restrictions": [],
            }

    assert check_mission_candidate_eligibility(
        "BOND-001", Registry(), expected_name="Fox"
    )["reason"] == "PASSPORT_NAME_MISMATCH"
    allowed = check_mission_candidate_eligibility(
        "BOND-001", Registry(), expected_name="007"
    )
    assert allowed["eligible"] is True
    assert allowed["execution_verified"] is False


def test_malformed_passport_fields_fail_closed_without_activation():
    from oap.smi.protocol_selection import check_mission_candidate_eligibility

    class Registry:
        def __init__(self, record):
            self.record = record

        def passport(self, agent_id):
            return self.record

    valid = {
        "agent_id": "FOX-001", "name": "Fox", "aliases": [],
        "status": "ACTIVE", "permissions": ["ANALYSE"],
        "restrictions": [], "audit_required": True,
        "family_id": "recovery", "guardian": "Guardian", "memory": {},
    }
    for changes in (
        {"aliases": 777},
        {"aliases": ["Fox", None]},
        {"permissions": None},
        {"restrictions": None},
        {"memory": None},
    ):
        result = check_mission_candidate_eligibility(
            "FOX-001", Registry({**valid, **changes}), expected_name="Fox"
        )
        assert result["eligible"] is False
        assert result["reason"] == "MALFORMED_PASSPORT"
        assert result["grants_permissions"] is False
        assert result["execution_verified"] is False


def test_all_protocols_have_bounded_capability_acquisition_plans():
    from oap.smi.protocol_selection import (
        PROTOCOL_CAPABILITIES,
        protocol_capability_plan,
    )

    assert set(PROTOCOL_CAPABILITIES) == set(PROTOCOL_TEAMS)
    for protocol in PROTOCOL_TEAMS:
        plan = protocol_capability_plan(protocol)
        assert plan["status"] == "PROPOSED_UNVERIFIED"
        assert plan["capabilities"] and plan["candidates"] and plan["acceptance_test"]
        assert "independent_review" in plan["required_evidence"]
        assert "hardware_compatibility" in plan["required_evidence"]
        assert plan["installed_verified"] is False
        assert plan["benchmark_verified"] is False
        assert plan["execution_granted"] is False
        assert plan["approval_granted"] is False


def test_capability_plan_rejects_unknown_and_marks_large_coder_server_only():
    from oap.smi.protocol_selection import protocol_capability_plan

    assert protocol_capability_plan("unknown")["candidates"] == ()
    plan = protocol_capability_plan("execution")
    assert plan["server_candidate_only"] == ("Qwen3-Coder-Next",)
    assert "sandbox_test" in plan["required_evidence"]


def test_capability_inventory_distinguishes_presence_from_proof(monkeypatch):
    from oap.smi import protocol_selection

    monkeypatch.setattr(protocol_selection, "version", lambda name: "1.2.3")
    monkeypatch.setattr(protocol_selection, "which", lambda name: "/local/bin/opa")
    inventory = protocol_selection.observe_protocol_capabilities("guardian")
    observations = inventory["observations"]
    assert observations["OPA"]["observation"] == "Executable detected"
    assert observations["Semgrep"]["observation"] == "Metadata present"
    assert "/local/bin/opa" not in str(inventory)
    assert all(item["functional_status"] == "Unknown" for item in observations.values())
    assert all(item["integrity_verified"] is False for item in observations.values())
    assert inventory["commands_executed"] is False
    assert inventory["execution_granted"] is False


def test_capability_inventory_handles_missing_and_unprobed_candidates(monkeypatch):
    from oap.smi import protocol_selection

    def missing(name):
        raise protocol_selection.PackageNotFoundError(name)

    monkeypatch.setattr(protocol_selection, "version", missing)
    monkeypatch.setattr(protocol_selection, "which", lambda name: None)
    assert protocol_selection.observe_protocol_capabilities("guardian")["observations"]["OPA"]["observation"] == "Not detected"
    assert protocol_selection.observe_protocol_capabilities("science")["observations"]["SciPy"]["observation"] == "Not detected"
    assert protocol_selection.observe_protocol_capabilities("execution")["observations"]["Qwen3-Coder-Next"]["observation"] == "Unknown"
    assert protocol_selection.observe_protocol_capabilities("unknown")["observations"] == {}


def test_builtin_capability_baselines():
    from oap.smi.protocol_selection import benchmark_builtin_capability

    for protocol in ("dependencies", "economics", "science", "audit"):
        result = benchmark_builtin_capability(protocol)
        assert result["status"] == "Passed"
        assert result["checks_passed"] == result["checks_total"] == 1
        assert result["elapsed_ms"] >= 0
        assert result["candidate_benchmark_verified"] is False
        assert result["independent_verification"] is False
        assert result["execution_granted"] is False
        assert result["approval_granted"] is False


def test_builtin_capability_baseline_does_not_claim_unimplemented_protocols():
    from oap.smi.protocol_selection import benchmark_builtin_capability

    for protocol in ("execution", "guardian", "unknown"):
        result = benchmark_builtin_capability(protocol)
        assert result["status"] == "Not tested"
        assert result["checks_total"] == 0
        assert result["elapsed_ms"] is None
        assert result["execution_granted"] is False


def test_builtin_capability_baseline_records_failure(monkeypatch):
    from oap.smi import protocol_selection

    monkeypatch.setitem(protocol_selection.BUILTIN_BASELINES, "audit", lambda: False)
    result = protocol_selection.benchmark_builtin_capability("audit")
    assert result["status"] == "Failed"
    assert result["checks_passed"] == 0
    assert result["checks_total"] == 1
    assert result["independent_verification"] is False
