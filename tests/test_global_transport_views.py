# ruff: noqa: SIM115
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
    assert state["mission_scope"] == "software_plus_evidence_gated_execution"
    assert state["physical_operations_in_scope"] is False
    assert all(value is False for value in state["live_execution_gates"].values())


def test_global_transport_public_routes_are_registered():
    app = _app()
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/transport" in rules
    assert "/global-transport" in rules
    assert "/transport/status" in rules
    assert "/transport/capabilities" in rules
    assert "/transport/shared-bikes/status" in rules
    assert "/transport/shared-bikes/mitcham" in rules


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


def test_oap_ride_aliases_reuse_durable_movement_routes():
    app = _app()
    client = app.test_client()
    assert client.post("/transport/ride/request", follow_redirects=False).status_code == 307
    assert client.post("/transport/ride/driver/availability", follow_redirects=False).status_code == 307
    booking = "00000000-0000-0000-0000-000000000001"
    proposal = "00000000-0000-0000-0000-000000000002"
    response = client.post(f"/transport/ride/{booking}/match", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["Location"].endswith(f"/movement/bookings/{booking}/match")
    response = client.post(f"/transport/ride/matches/{proposal}/accept", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["Location"].endswith(f"/movement/matches/{proposal}/accept")


def test_oap_ride_runtime_declares_durable_owner_and_no_physical_dispatch():
    payload = _app().test_client().get("/transport/ride/runtime").get_json()
    assert payload["durable_owner"] == "OAP Movement"
    assert payload["certified_driver_matching"] is True
    assert payload["race_safe_match_acceptance"] is True
    assert payload["tracking_consent_store"] is True
    assert payload["payment_intent_store"] is True
    assert payload["trip_link_binding"] is True
    assert payload["physical_operations_in_scope"] is False
    assert payload["external_dispatch_performed"] is False


def test_execution_readiness_unlocks_software_without_false_live_claims():
    state = global_transport_views.execution_readiness()
    assert state["software_execution_layer_ready"] is True
    assert state["live_execution_authorised"] is False
    assert set(state["areas"]) == {
        "carrier_dispatch",
        "ride_dispatch",
        "ticket_issuance",
        "fare_capture",
        "payment_movement",
        "customs_clearance",
        "external_tracking_feed",
        "vehicle_control",
    }
    assert all(item["software_ready"] is True for item in state["areas"].values())
    assert all(
        item["live_execution_authorised"] is False
        for item in state["areas"].values()
    )
    assert all(item["requires"] for item in state["areas"].values())


def test_execution_readiness_route_is_no_store():
    client = _app().test_client()
    response = client.get("/transport/execution-readiness")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store, private"
    payload = response.get_json()
    assert payload["software_execution_layer_ready"] is True
    assert payload["live_execution_authorised"] is False


def test_execution_readiness_uses_verified_evidence_per_area(monkeypatch):
    monkeypatch.setattr(
        global_transport_views.transport_execution_evidence,
        "status",
        lambda: {
            "store_reachable": True,
            "areas": {
                "ride_dispatch": {
                    "verified": [
                        "eligible_driver_binding",
                        "vehicle_evidence",
                        "dispatch_receipt",
                    ],
                    "missing": [],
                    "live_execution_authorised": True,
                },
                "payment_movement": {
                    "verified": ["regulated_payment_executor"],
                    "missing": ["submission_evidence", "settlement_evidence"],
                    "live_execution_authorised": False,
                },
            },
        },
    )

    state = global_transport_views.execution_readiness()
    assert state["areas"]["ride_dispatch"]["live_execution_authorised"] is True
    assert state["areas"]["ride_dispatch"]["missing"] == []
    assert state["areas"]["payment_movement"]["live_execution_authorised"] is False
    assert state["areas"]["payment_movement"]["missing"] == [
        "submission_evidence",
        "settlement_evidence",
    ]
    assert state["live_execution_authorised"] is False


def test_live_execution_gates_fail_closed_for_unproven_areas(monkeypatch):
    monkeypatch.setattr(
        global_transport_views.transport_execution_evidence,
        "status",
        lambda: {
            "store_reachable": True,
            "areas": {
                "ride_dispatch": {
                    "verified": [
                        "eligible_driver_binding",
                        "vehicle_evidence",
                        "dispatch_receipt",
                    ],
                    "missing": [],
                    "live_execution_authorised": True,
                },
            },
        },
    )

    gates = global_transport_views.live_execution_gates()
    assert gates["ride_dispatch"] is True
    assert gates["carrier_dispatch"] is False
    assert gates["payment_movement"] is False


def test_transport_execution_evidence_source_is_hash_only_for_sensitive_fields():
    source = open("mission_control/transport_execution_evidence.py", encoding="utf-8").read()
    metadata_block = source.split("metadata={", 1)[1].split("}", 1)[0]
    assert '"evidence_ref": ref' not in metadata_block
    assert '"issuer": issuer_value' not in metadata_block
    assert '"scope": scope_value' not in metadata_block
    assert '"evidence_ref_hash"' in metadata_block
    assert '"issuer_hash"' in metadata_block
    assert '"scope_hash"' in metadata_block


def test_mitcham_shared_bike_routes_are_public_read_only(monkeypatch):
    monkeypatch.delenv("OAP_SHARED_BIKE_LIME_GBFS_URL", raising=False)
    monkeypatch.delenv("OAP_SHARED_BIKE_FOREST_GBFS_URL", raising=False)
    monkeypatch.delenv("OAP_SHARED_BIKE_ALLOWED_HOSTS", raising=False)
    client = _app().test_client()

    status_response = client.get("/transport/shared-bikes/status")
    assert status_response.status_code == 200
    assert status_response.headers["Cache-Control"] == "no-store, private"
    status = status_response.get_json()
    assert status["public_discovery_ready"] is True
    assert status["operator_control_authorised"] is False
    assert status["unlock_enabled"] is False

    nearby_response = client.get("/transport/shared-bikes/mitcham")
    assert nearby_response.status_code == 200
    nearby = nearby_response.get_json()
    assert nearby["area"] == "Mitcham"
    assert nearby["postcode"] == "CR4"
    assert nearby["vehicle_count"] == 0
    assert nearby["public_discovery_only"] is True
    assert nearby["operator_control_authorised"] is False


def test_mitcham_shared_bike_route_rejects_oversized_radius():
    response = _app().test_client().get("/transport/shared-bikes/mitcham?radius_km=99")
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_radius_km"



def test_oap_rides_front_door_is_mobile_app_surface():
    client = _app().test_client()
    response = client.get("/transport/ride")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    for marker in (
        'aria-label="OAP Rides navigation"',
        'href="/movement/workspace#book-title"',
        'href="/oap-map"',
        'href="/transport/ride/current"',
        'href="/transport/ride/guardian/status"',
        'href="/pay/bank"',
        'href="/eats"',
        "From this postcode to the next.",
        "Physical vehicle operation and external dispatch remain outside this build.",
    ):
        assert marker in body


def test_oap_rides_app_config_exposes_real_shared_routes():
    client = _app().test_client()
    response = client.get("/transport/ride/app-config")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["navigation"] == {
        "rides": "/transport/ride",
        "world": "/oap-map",
        "journey": "/transport/ride/current",
        "guardian": "/transport/ride/guardian/status",
        "sika": "/pay/bank",
        "eats": "/eats",
    }
    assert payload["rider"] == "/transport/ride/rider"
    assert payload["driver"] == "/transport/ride/driver"
    assert payload["movement_workspace"] == "/movement/workspace"
    assert payload["physical_operations_in_scope"] is False
    assert payload["human_authority_final"] is True


def test_oap_rides_status_moved_off_front_door_without_losing_truth_api():
    client = _app().test_client()
    response = client.get("/transport/ride/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["physical_operations_in_scope"] is False
