from mission_control import oap_host


def test_oap_host_fails_closed_without_runtime_evidence(monkeypatch):
    for name in (
        "OAP_HOST_NODE_ID",
        "OAP_SOVEREIGN_INFRA_SELF_HOSTED",
        "OAP_SOVEREIGN_DATA_SELF_HOSTED",
        "OAP_SOVEREIGN_NETWORK_EGRESS_CONTROLLED",
        "OAP_SOVEREIGN_OBSERVABILITY_FIRST_PARTY",
        "OAP_SOVEREIGN_RECOVERY_PROVEN",
        "OAP_SOVEREIGN_SUPPLY_CHAIN_ATTESTED",
        "OAP_HOST_DEPLOY_ROLLBACK_PROVEN",
    ):
        monkeypatch.delenv(name, raising=False)

    state = oap_host.status()

    assert state["architecture_ready"] is True
    assert state["runtime_ready"] is False
    assert state["self_hosted_claim"] is False
    assert state["deployment_execution_enabled"] is False


def test_registry_contains_required_host_classes():
    services = {item["service_id"]: item for item in oap_host.service_registry()}

    assert "public-app" in services
    assert "smi" in services
    assert "database" in services
    assert "routing-scotland" in services
    assert "routing-northern-ireland" in services


def test_deployment_review_denies_unverified_host_even_with_all_flags_true(monkeypatch):
    monkeypatch.setenv("OAP_HOST_NODE_ID", "oap-host-01")
    for name in (
        "OAP_SOVEREIGN_INFRA_SELF_HOSTED",
        "OAP_SOVEREIGN_DATA_SELF_HOSTED",
        "OAP_SOVEREIGN_NETWORK_EGRESS_CONTROLLED",
        "OAP_SOVEREIGN_OBSERVABILITY_FIRST_PARTY",
        "OAP_SOVEREIGN_RECOVERY_PROVEN",
        "OAP_SOVEREIGN_SUPPLY_CHAIN_ATTESTED",
        "OAP_HOST_DEPLOY_ROLLBACK_PROVEN",
    ):
        monkeypatch.setenv(name, "true")
    monkeypatch.delenv("OAP_SOVEREIGN_HALT", raising=False)

    review = oap_host.deployment_review(
        service_id="public-app",
        exact_commit="abcdef1234567890",
        rollback_ref="1234567abcdef",
        health_proven=True,
        human_authority_approved=True,
    )

    state = oap_host.status()
    assert state["host_attestation"]["configuration_declared_ready"] is True
    assert state["host_attestation"]["independent_runtime_evidence_verified"] is False
    assert state["runtime_ready"] is False
    assert state["self_hosted_claim"] is False
    assert review["allowed"] is False
    assert "host_runtime_ready" in review["failed_checks"]
    assert review["execution_performed"] is False
    assert review["traffic_changed"] is False
