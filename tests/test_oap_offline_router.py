from mission_control import oap_offline_router as router


EXPECTED_DOMAINS = (
    "infrastructure",
    "trust_identity",
    "world_spot",
    "link_up",
    "music",
    "commerce_market",
    "sika",
    "post_core",
    "movement",
    "media_studio",
    "youth",
    "nature",
    "arena",
    "intelligence_governance",
)


def test_all_oap_domains_have_one_offline_route():
    status = router.status()

    assert status["domain_count"] == 14
    assert status["domains"] == EXPECTED_DOMAINS
    assert status["unique_domains"] is True
    assert status["all_domains_have_offline_mode"] is True


def test_local_capability_stays_local_without_external_authority():
    result = router.route_for("commerce_market", "unit_economics")

    assert result["decision"] == "LOCAL"
    assert result["external_action_permitted"] is False


def test_sync_later_capability_is_queued_not_executed():
    result = router.route_for("link_up", "message_send_intent")

    assert result["decision"] == "QUEUE"
    assert result["requires_reconciliation"] is True
    assert result["external_action_permitted"] is False


def test_live_dependent_capability_is_blocked_offline():
    result = router.route_for("sika", "money_transfer")

    assert result["decision"] == "BLOCK"
    assert result["external_action_permitted"] is False


def test_unknown_capability_fails_closed():
    result = router.route_for("arena", "invented_action")

    assert result["decision"] == "BLOCK"


def test_unknown_domain_fails_closed():
    result = router.route_for("unknown-organ", "anything")

    assert result["decision"] == "BLOCK"
    assert result["reason"] == "unknown_domain"


def test_smi_and_hormozi_can_analyse_locally_but_not_self_approve():
    smi = router.route_for("intelligence_governance", "smi_local_reasoning")
    hormozi = router.route_for("intelligence_governance", "hormozi_offline")
    approval = router.route_for("intelligence_governance", "self_approval")

    assert smi["decision"] == "LOCAL"
    assert hormozi["decision"] == "LOCAL"
    assert approval["decision"] == "BLOCK"


def test_reconciliation_never_silently_overwrites():
    policy = router.reconciliation_policy()

    assert policy["silent_overwrite_allowed"] is False
    assert policy["stale_claim_promoted_to_live"] is False
    assert policy["queued_intent_equals_execution"] is False
    assert policy["human_authority_final"] is True
