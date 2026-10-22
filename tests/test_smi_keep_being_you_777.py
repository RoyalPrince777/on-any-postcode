"""Contract checks for the read-only SMI personality policy."""

from mission_control.smi_keep_being_you_777 import personality_policy


def test_policy_keeps_identity_and_humour():
    policy = personality_policy()
    assert "preserve_specialist_identity" in policy["principles"]
    assert "preserve_distinct_humour" in policy["principles"]
    assert "learn_from_corrections" in policy["principles"]


def test_policy_does_not_grant_authority_or_claim_runtime():
    policy = personality_policy()
    assert policy["mode"] == "advisory_only"
    assert policy["agent_runtime_activated"] is False
    assert policy["authority_granted"] is False
    assert policy["live_votes_verified"] is False
    assert policy["overall_vpi"] is None


def test_policy_preserves_security_boundaries():
    policy = personality_policy()
    assert "never_dismiss_verified_security_evidence_as_a_joke" in policy["principles"]
    assert "founder_final_guardian_hrm_remain_authoritative" in policy["principles"]
    assert "no_duplicate_agent_hierarchy" in policy["principles"]


def test_returned_principles_are_not_shared_mutable_state():
    first = personality_policy()
    first["principles"].clear()
    assert personality_policy()["principles"]
