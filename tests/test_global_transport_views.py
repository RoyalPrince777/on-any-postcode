from flask import Flask

from mission_control import global_transport_views


def _app():
    app = Flask(__name__)
    app.register_blueprint(global_transport_views.bp)
    return app


def test_global_transport_contract_is_install_ready_without_false_live_claims():
    state = global_transport_views.status()
    assert state["product"] == "OAP Global Transport"
    assert state["software_surface_install_ready"] is True
    assert state["first_party_surface"] is True
    assert state["capability_count"] == 21
    assert state["existing_transport_intelligence_reused"] is True
    assert state["post_core_authoritative_for_parcels"] is True
    assert state["human_authority_final"] is True
    assert state["live_external_transport_execution"] is False
    assert state["mission_scope"] == "software_and_digital_only"
    assert state["physical_operations_in_scope"] is False
    assert all(value is False for value in state["live_execution_gates"].values())


def test_global_transport_public_routes_are_registered():
    app = _app()
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/transport" in rules
    assert "/global-transport" in rules
    assert "/transport/status" in rules
    assert "/transport/capabilities" in rules


def test_global_transport_home_and_status_are_mobile_public_surfaces():
    client = _app().test_client()
    home = client.get("/transport")
    assert home.status_code == 200
    assert b"OAP Global Transport" not in home.data or b"Global Transport" in home.data
    assert b"Journey" in home.data
    assert b"Cargo" in home.data
    assert home.headers["Cache-Control"] == "no-store, private"

    payload = client.get("/transport/status").get_json()
    assert payload["front_door"] == "/transport"
    assert payload["public_doors"] == [
        "journey", "move", "ride", "transit", "drive", "fly", "cargo", "deliver", "fleet"
    ]


def test_global_transport_capability_api_exposes_21_without_execution_authority():
    payload = _app().test_client().get("/transport/capabilities").get_json()
    assert payload["capability_count"] == 21
    assert "guardian_transport" in payload["capabilities"]
    assert "transport_control_center" in payload["capabilities"]
    assert payload["human_authority_final"] is True
    assert payload["live_execution_gates"]["carrier_dispatch"] is False
    assert payload["live_execution_gates"]["payment_movement"] is False


def test_global_transport_is_registered_by_main_mission_control_initializer():
    source = open("mission_control/__init__.py", encoding="utf-8").read()
    assert "from .global_transport_views import bp as global_transport_bp" in source
    assert "app.register_blueprint(global_transport_bp)" in source
