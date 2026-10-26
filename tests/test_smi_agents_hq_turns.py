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


def test_founder_chat_uses_real_governed_facade(monkeypatch):
    from mission_control import smi_chat_runtime
    from mission_control.smi_agents_hq_turns import founder_council_chat
    calls = []

    def fake_chat(message, identity_id, display_name, conversation_id=None):
        calls.append((message, identity_id, display_name, conversation_id))
        return {"response": "bounded SMI response", "guardian": "REVIEWED"}

    monkeypatch.setattr(smi_chat_runtime, "chat", fake_chat)
    result = founder_council_chat(
        message="Challenge the proposal", identity_id="authenticated-founder",
        display_name="Founder", founder_authenticated=True,
        conversation_id="existing-conversation",
    )
    assert calls == [("Challenge the proposal", "authenticated-founder", "Founder", "existing-conversation")]
    assert result["reply_source"] == "existing_governed_smi_runtime"
    assert not result["individual_agent_reply_verified"]
    assert not result["agent_to_agent_conversation_proven"]


def test_founder_chat_blocks_unauthenticated_before_model_call(monkeypatch):
    from mission_control import smi_chat_runtime
    from mission_control.smi_agents_hq_turns import founder_council_chat

    def no_call(*args, **kwargs):
        pytest.fail("unauthenticated caller reached inference")

    monkeypatch.setattr(smi_chat_runtime, "chat", no_call)
    with pytest.raises(PermissionError, match="founder_authentication_required"):
        founder_council_chat(
            message="hello", identity_id="claimed-founder",
            display_name="Founder", founder_authenticated=False,
        )


def test_founder_chat_requires_bound_identity():
    from mission_control.smi_agents_hq_turns import founder_council_chat
    with pytest.raises(ValueError, match="bound_founder_identity_required"):
        founder_council_chat(
            message="hello", identity_id="", display_name="Founder",
            founder_authenticated=True,
        )
