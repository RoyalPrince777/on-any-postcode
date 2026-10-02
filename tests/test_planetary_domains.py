from mission_control import planetary_domains


def test_planetary_domains_are_exactly_seven_and_ordered():
    snapshot = planetary_domains.status()
    assert snapshot["operational_domain_count"] == 7
    assert tuple(item["id"] for item in snapshot["operational_domains"]) == (
        "underground",
        "water",
        "land",
        "air",
        "space",
        "spectrum",
        "energy",
    )


def test_cyber_is_cross_cutting_not_an_eighth_domain():
    snapshot = planetary_domains.status()
    assert snapshot["cyber_fabric"]["cross_cutting"] is True
    assert tuple(snapshot["cyber_fabric"]["domain_ids"]) == planetary_domains.DOMAIN_ORDER
    assert "cyber" not in planetary_domains.DOMAIN_ORDER


def test_smi_is_single_fusion_brain_and_human_authority_is_final():
    snapshot = planetary_domains.status()
    assert snapshot["smi_fusion"]["single_brain"] is True
    assert snapshot["execution_granted"] is False
    assert snapshot["approval_granted"] is False
    assert snapshot["human_authority_final"] is True


def test_domain_dashboards_do_not_claim_live_external_runtime():
    for domain_id in planetary_domains.DOMAIN_ORDER:
        domain = planetary_domains.domain_status(domain_id)
        assert domain["dashboard_ready"] is True
        assert domain["live_external_sources_proven"] is False
        assert domain["control_execution_granted"] is False
        assert domain["network_calls_made"] is False
