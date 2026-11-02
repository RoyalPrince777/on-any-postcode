"""Safety invariants for fictional SMI specialist overlays."""
from mission_control import agents
from mission_control.intelligence_alliances import get_founder_alliance_board


def test_specialist_overlay_preserves_registry_and_authority():
    before = tuple((a["agent_id"], a["name"]) for a in agents.AGENT_REGISTRY)
    board = get_founder_alliance_board()
    profiles = board["specialist_research"]
    assert [p["name"] for p in profiles] == ["M3GAN", "AMELIA", "BLACK BOX"]
    assert len(profiles) == 3
    assert profiles[0]["identity"] == "one_identity_with_2_0_upgrade"
    assert profiles[1]["identity"] == "separate_adversarial_profile"
    assert profiles[2]["identity"] == "non_agent_capability"
    assert all(p["world_id"] == "matrix" for p in profiles)
    assert all(p["agent_id"] is None and not p["ranking_eligible"] for p in profiles)
    assert all(not p["execution_enabled"] and not p["can_approve"] for p in profiles)
    assert all(not p["can_change_permissions"] and p["requires_human_authority"] for p in profiles)
    assert all(p["status"] == "advisory_design_only" for p in profiles)
    assert board["human_authority"] == "Founder Final"
    assert board["oversight"] == ("Guardian", "HRM Core")
    assert tuple((a["agent_id"], a["name"]) for a in agents.AGENT_REGISTRY) == before
