from mission_control import tv_core

def _asset(**overrides):
    data = {
        "asset_id": "asset-1",
        "owner": "oap",
        "rights_holder": "oap",
        "licence_type": "owned",
        "evidence_reference": "receipt-1",
        "allowed_territories": ["global"],
        "requested_territory": "uk",
        "starts_at": "2026-09-26T00:00:00Z",
        "expires_at": "2027-09-26T00:00:00Z",
        "audience_rating": "general",
        "distribution_permissions": ["oap_tv"],
        "rights_status": "certified",
        "human_approved": True,
    }
    data.update(overrides)
    return data

def test_rights_gate_fails_closed_without_evidence():
    result = tv_core.rights_gate(_asset(evidence_reference=""))
    assert result["passed"] is False
    assert result["public_distribution_allowed"] is False
    assert "evidence_reference" in result["missing"]

def test_distribution_gate_requires_rights_territory_entitlement_and_stop_clear():
    ok = tv_core.distribution_gate(
        _asset(),
        stop_active=False,
        entitlement_required=True,
        entitlement_granted=True,
    )
    assert ok["playback_authorised"] is True
    stopped = tv_core.distribution_gate(
        _asset(),
        stop_active=True,
        entitlement_required=True,
        entitlement_granted=True,
    )
    assert stopped["playback_authorised"] is False
    assert stopped["fail_closed"] is True

def test_red_team_never_claims_green_with_missing_runtime_evidence():
    report = tv_core.red_team_report()
    assert report["green"] is False
    assert report["software_readiness_percent"] == 0
    assert set(report["blocked"]) == set(tv_core.RUNTIME_GATES)

def test_status_does_not_claim_unproven_runtime_capabilities():
    state = tv_core.status()
    assert state["truth_mode"] is True
    assert state["live_broadcast_claimed"] is False
    assert state["external_distribution_claimed"] is False
    assert state["device_acceptance_claimed"] is False
