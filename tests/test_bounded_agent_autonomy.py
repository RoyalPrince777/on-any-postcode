from mission_control.agents import (
    AGENT_REGISTRY,
    LOCKED_FAMILY_IDS,
    validate_agent_registry,
)
from oap.registry import RegistryEngine


def _registry() -> RegistryEngine:
    return RegistryEngine(AGENT_REGISTRY, LOCKED_FAMILY_IDS)


def test_all_78_agents_are_bounded_autonomous_advisors():
    status = _registry().status()

    assert status["agents"] == 78
    assert status["active_agents"] == 78
    assert status["bounded_autonomous_agents"] == 78
    assert status["provider_assignments"] == 0
    assert status["independent_execute"] is False
    assert status["final_authority"] == "Human Authority"


def test_general_work_uses_neo_as_default_coordinator():
    selection = _registry().select_advisors("GENERAL")

    assert selection.agent_ids == ("NEO-001",)
    assert "Bounded autonomous" in selection.reason


def test_architecture_work_routes_only_to_neo_and_matrix_family():
    selection = _registry().select_advisors("ARCHITECTURE")
    passports = {
        agent["agent_id"]: agent for agent in AGENT_REGISTRY
    }

    assert len(selection.agent_ids) == 7
    assert selection.agent_ids[0] == "NEO-001"
    assert {
        passports[agent_id]["family_id"] for agent_id in selection.agent_ids
    } == {"matrix"}


def test_autonomy_cannot_be_mutated_into_execution_authority():
    original = next(agent for agent in AGENT_REGISTRY if agent["name"] == "Nirmata")
    unsafe = {
        **original,
        "autonomy": {**original["autonomy"], "can_execute": True},
    }
    registry = tuple(
        unsafe if agent["agent_id"] == original["agent_id"] else agent
        for agent in AGENT_REGISTRY
    )

    result = validate_agent_registry(agents=registry)

    assert result["passed"] is False
    assert result["ready_for_activation"] is False
    assert result["checks"]["unsafe_authority"] == 1
    assert any("Unsafe agent authority" in error for error in result["errors"])

