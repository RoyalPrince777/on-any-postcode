from mission_control import planetary_domains


def test_every_planetary_domain_has_complete_command_structure():
    expected = ("observe", "assets", "risks", "forecasts", "dependencies")
    for domain_id in planetary_domains.DOMAIN_ORDER:
        status = planetary_domains.domain_status(domain_id)
        assert status["command_sections"] == expected
        assert tuple(status["command"]) == expected
        assert all(status["command"][section] for section in expected)


def test_cross_domain_relationships_only_reference_operational_domains():
    snapshot = planetary_domains.status()
    assert snapshot["cross_domain_relationship_count"] == len(
        snapshot["cross_domain_relationships"]
    )
    assert snapshot["cross_domain_relationship_count"] >= 4
    allowed = set(planetary_domains.DOMAIN_ORDER)
    for relationship in snapshot["cross_domain_relationships"]:
        assert relationship["id"]
        assert relationship["name"]
        assert relationship["purpose"]
        assert set(relationship["domains"]) <= allowed


def test_command_depth_does_not_upgrade_runtime_or_execution_claims():
    snapshot = planetary_domains.status()
    assert snapshot["universal_live_runtime_ready"] is False
    assert snapshot["execution_granted"] is False
    assert snapshot["approval_granted"] is False
    assert snapshot["human_authority_final"] is True
    for domain in snapshot["operational_domains"]:
        assert domain["live_external_sources_proven"] is False
        assert domain["control_execution_granted"] is False
