"""No Founder exclusion, no unverified agent speaker trusted as live."""
import pytest

from mission_control.smi_agents_hq_turns import admit_council_turn


def test_founder_can_speak_as_first_class_participant():
    turn = admit_council_turn(
        speaker="Founder", message="I challenge this conclusion.",
        founder_authenticated=True,
    )
    assert turn["speaker"]["type"] == "human"
    assert turn["speaker"]["authority"] == "founder_final"
    assert not turn["vote_recorded"] and not turn["execution_authorised"]


def test_founder_must_be_authenticated():
    with pytest.raises(PermissionError, match="founder_authentication_required"):
        admit_council_turn(speaker="Founder", message="approve deployment")


def test_founder_cannot_claim_agent_origin():
    with pytest.raises(PermissionError, match="founder_cannot_impersonate_agent"):
        admit_council_turn(speaker="Neo", message="hello", founder_authenticated=True)


def test_registered_agent_text_is_unverified_until_sender_attestation():
    turn = admit_council_turn(speaker="Neo", message="check the code")
    assert turn["speaker"]["type"] == "agent_candidate_message"
    assert not turn["runtime_sender_verified"]
    assert not turn["live_agent_dialogue_proven"]
    assert not turn["career_star_awarded"]


def test_unknown_agent_cannot_enter():
    with pytest.raises(PermissionError, match="unique_agent_passport_required"):
        admit_council_turn(speaker="Invented Agent", message="hello")


def test_empty_or_oversized_turn_rejected():
    with pytest.raises(ValueError):
        admit_council_turn(speaker="Founder", message=" ", founder_authenticated=True)
    with pytest.raises(ValueError):
        admit_council_turn(speaker="Founder", message="x" * 2001, founder_authenticated=True)


def test_inactive_passport_rejected(monkeypatch):
    from mission_control import agents
    monkeypatch.setattr(agents, "AGENT_REGISTRY", tuple(
        {**a, "registry_status": "PROPOSED"} if a["name"] == "Neo" else a
        for a in agents.AGENT_REGISTRY
    ))
    with pytest.raises(PermissionError, match="active_agent_passport_required"):
        admit_council_turn(speaker="Neo", message="hello")
