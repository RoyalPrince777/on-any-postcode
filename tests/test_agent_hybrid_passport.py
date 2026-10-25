from mission_control.agent_hybrid_passport import public_passport, founder_passport
from mission_control.agents import AGENT_REGISTRY


def test_public_projection_uses_original_canonical_id():
    original = next(a for a in AGENT_REGISTRY if a["name"] == "Bagheera")
    card = public_passport(original["agent_id"])
    assert card["agent_id"] == original["agent_id"]
    assert card["name"] == "Bagheera"
    assert set(card) == {"agent_id", "name", "family_id", "role", "passport_verified", "runtime_verified"}
    assert not card["passport_verified"]
    assert not card["runtime_verified"]


def test_unknown_or_unregistered_agent_fails_closed():
    for unknown in ("", "FAKE-001", "JUNGLE-MOUSE-001"):
        assert public_passport(unknown) is None
        assert founder_passport(unknown, founder_authorised=True) is None


def test_founder_private_projection_requires_explicit_gate():
    agent_id = next(a["agent_id"] for a in AGENT_REGISTRY if a["name"] == "Gorilla")
    assert founder_passport(agent_id) is None
    assert founder_passport(agent_id, founder_authorised=False) is None
    private = founder_passport(agent_id, founder_authorised=True)
    assert private["founder_final_required"] is True
    assert private["execution_authorised"] is False
    assert private["credential_presented"] is False
    assert private["mission_stars"] is None
    assert private["mission_stars_status"] == "unverified"
