"""Network security release admission regression tests."""
from oap.security.network_release_gate import REQUIRED_PROOF, evaluate_network_release


def test_no_evidence_fails_closed_for_both_existing_store_identifiers():
    for app_id in REQUIRED_PROOF:
        result = evaluate_network_release(app_id)
        assert result.admitted is False
        assert set(result.missing) == set(REQUIRED_PROOF[app_id])


def test_user_supplied_evidence_references_do_not_self_certify():
    for app_id, required in REQUIRED_PROOF.items():
        claimed = {name: "self-claimed" for name in required}
        result = evaluate_network_release(app_id, claimed)
        assert result.missing == ()
        assert result.admitted is False
        assert result.reason == "independent_verification_required"


def test_empty_and_whitespace_references_are_not_evidence():
    result = evaluate_network_release("oap.vpn", {"founder_final": "  "})
    assert "founder_final" in result.missing
    assert not result.admitted


def test_unknown_identity_fails_closed():
    result = evaluate_network_release("oap.firewall", {"founder_final": "yes"})
    assert result.admitted is False
    assert result.reason == "unknown_app_fail_closed"


def test_existing_store_entries_remain_locked():
    from mission_control import oap_store
    apps = {app["app_id"]: app for app in oap_store.catalogue()}
    for app_id in REQUIRED_PROOF:
        assert apps[app_id]["release_state"] == "planned"
        assert apps[app_id]["install_enabled"] is False
        assert apps[app_id]["install_url"] is None
        assert apps[app_id]["open_url"] is None
