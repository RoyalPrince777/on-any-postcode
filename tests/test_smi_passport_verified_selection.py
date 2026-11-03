"""Mission selection must respect exact canonical passport status."""

from oap.smi.alliance_selection import (
    select_alliance,
    select_passport_verified_alliance,
)


def test_technical_mission_keeps_registered_specialist():
    original = select_alliance("TECHNICAL", "github code review")
    verified = select_passport_verified_alliance("TECHNICAL", "github code review")
    assert "Neo" in original.specialists
    assert "Neo" in verified.specialists
    assert verified.advisory_only and not verified.authority_granted
    assert verified.founder_final


def test_unregistered_references_never_granted_authority():
    verified = select_passport_verified_alliance(
        "TECHNICAL", "agent governance and adversarial review", high_impact=True
    )
    assert not verified.authority_granted
    assert not set(verified.specialists) & set(verified.excluded_unregistered)
    assert not set(verified.specialists) & set(verified.excluded_inactive)


def test_distributed_mode_remains_explicit_and_advisory():
    normal = select_passport_verified_alliance("TECHNICAL", "swarm parallel agents")
    distributed = select_passport_verified_alliance(
        "TECHNICAL", "swarm parallel agents", distributed_work=True
    )
    assert "Queen Bee" not in normal.specialists
    assert not normal.authority_granted and not distributed.authority_granted


def test_selection_varies_by_mission_and_does_not_duplicate():
    coding = select_passport_verified_alliance("TECHNICAL", "github code review")
    memory = select_passport_verified_alliance("GENERAL", "jog memory history archive")
    assert coding.capabilities != memory.capabilities
    assert len(coding.specialists) == len(set(coding.specialists))
    assert len(memory.specialists) == len(set(memory.specialists))


def test_missing_passport_is_excluded(monkeypatch):
    from mission_control import agents
    original = agents.AGENT_REGISTRY
    monkeypatch.setattr(agents, "AGENT_REGISTRY", tuple(
        agent for agent in original if agent["name"] != "Neo"
    ))
    selection = select_passport_verified_alliance("TECHNICAL", "github code review")
    assert "Neo" not in selection.specialists
    assert "Neo" in selection.excluded_unregistered


def test_proposed_passport_is_not_eligible(monkeypatch):
    from mission_control import agents
    original = agents.AGENT_REGISTRY
    monkeypatch.setattr(agents, "AGENT_REGISTRY", tuple(
        {**agent, "registry_status": "PROPOSED"}
        if agent["name"] == "Neo" else agent
        for agent in original
    ))
    selection = select_passport_verified_alliance("TECHNICAL", "github code review")
    assert "Neo" not in selection.specialists
    assert "Neo" in selection.excluded_inactive


def test_ambiguous_duplicate_passports_fail_closed(monkeypatch):
    from mission_control import agents
    original = agents.AGENT_REGISTRY
    neo = next(agent for agent in original if agent["name"] == "Neo")
    monkeypatch.setattr(agents, "AGENT_REGISTRY", original + ({**neo},))
    selection = select_passport_verified_alliance("TECHNICAL", "github code review")
    assert "Neo" not in selection.specialists
    assert "Neo" in selection.excluded_unregistered
