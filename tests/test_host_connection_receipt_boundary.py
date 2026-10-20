"""Receipt issuance is not authenticated host ownership or readiness proof."""
from mission_control import home_node_bridge, oap_host
from mission_control.home_node_views import bp
from flask import Flask


def test_receipt_endpoint_requires_bridge_auth(monkeypatch):
    monkeypatch.setenv("OAP_HOME_NODE_BRIDGE_SECRET", "a" * 48)
    app = Flask(__name__)
    app.register_blueprint(bp)
    client = app.test_client()
    for headers in ({}, {"X-OAP-Home-Node-Token": "wrong"}):
        response = client.post("/home-node/connection/receipt", headers=headers)
        assert response.status_code == 404
        assert response.json == {"error": "not_found"}
        assert response.headers["Cache-Control"] == "no-store"


def test_authenticated_receipt_does_not_establish_host_readiness(monkeypatch):
    monkeypatch.setenv("OAP_HOME_NODE_BRIDGE_SECRET", "a" * 48)
    monkeypatch.setenv("OAP_HOST_NODE_ID", "oap-host-01")
    for key in (
        "OAP_SOVEREIGN_INFRA_SELF_HOSTED",
        "OAP_SOVEREIGN_DATA_SELF_HOSTED",
        "OAP_SOVEREIGN_NETWORK_EGRESS_CONTROLLED",
        "OAP_SOVEREIGN_OBSERVABILITY_FIRST_PARTY",
        "OAP_SOVEREIGN_RECOVERY_PROVEN",
        "OAP_SOVEREIGN_SUPPLY_CHAIN_ATTESTED",
        "OAP_HOST_DEPLOY_ROLLBACK_PROVEN",
    ):
        monkeypatch.setenv(key, "true")
    app = Flask(__name__)
    app.register_blueprint(bp)
    response = app.test_client().post(
        "/home-node/connection/receipt",
        headers={"X-OAP-Home-Node-Token": "a" * 48},
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    receipt = response.json["receipt"]
    assert home_node_bridge.consume_connection_receipt(receipt) is True
    assert home_node_bridge.consume_connection_receipt(receipt) is False
    state = oap_host.status()
    assert state["runtime_ready"] is False
    assert state["self_hosted_claim"] is False
    assert state["deployment_execution_enabled"] is False
    assert state["host_attestation"]["runtime_checks"]["authenticated_node_connection_proven"] is False
