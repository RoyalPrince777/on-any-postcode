# ruff: noqa: SIM115
from flask import Flask

from mission_control import global_transport_views


def _app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-transport-csrf-only"
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
    assert b"Logistics" in home.data
    assert b"Guardian" in home.data
    assert b"Operators" in home.data
    assert b"Control Center" in home.data
    assert home.headers["Cache-Control"] == "no-store, private"

    payload = client.get("/transport/status").get_json()
    assert payload["front_door"] == "/transport"
    assert payload["public_doors"] == [
        "journey", "move", "ride", "logistics", "guardian", "operators", "control_center"
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
        'id="ride-pickup"',
        'id="ride-destination"',
        'action="/movement/workspace#book-title"',
        'sessionStorage.setItem("oap_transport_ride_draft"',
        'href="/transport/ride/rider"',
        'href="/transport/ride/driver"',
        'href="/oap-map"',
        'href="/transport/ride/current"',
        'href="/transport/ride/guardian/status"',
        'href="/pay/bank"',
        'href="/eats"',
        "Where to?",
    ):
        assert marker in body
    assert "Software surface active." not in body
    assert "Choose pickup" not in body
    assert "Choose destination" not in body


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



def test_transport_cards_route_to_real_app_destinations():
    client = _app().test_client()
    response = client.get("/transport")
    body = response.get_data(as_text=True)
    for href in (
        "/travel",
        "/movement/workspace",
        "/transport/ride",
        "/transport/logistics",
        "/transport/guardian",
        "/transport/operators",
        "/transport/control-center",
    ):
        assert f'href="{href}"' in body
    assert "/transport/status#" not in body


def test_transport_status_exposes_seven_doors_and_legacy_route_compatibility():
    payload = _app().test_client().get("/transport/status").get_json()
    assert len(payload["public_doors"]) == 7
    assert set(payload["public_routes"]) == set(payload["public_doors"])
    assert payload["public_routes"]["journey"] == "/travel"
    assert payload["public_routes"]["ride"] == "/transport/ride"
    assert payload["public_routes"]["logistics"] == "/transport/logistics"
    assert payload["public_routes"]["guardian"] == "/transport/guardian"
    assert payload["public_routes"]["operators"] == "/transport/operators"
    assert payload["public_routes"]["control_center"] == "/transport/control-center"
    assert payload["legacy_public_routes"]["drive"] == "/oap-map?profile=driving"
    assert payload["legacy_public_routes"]["cargo"] == "/distribution"
    assert payload["legacy_public_routes"]["deliver"] == "/movement/workspace#book-title"
    assert payload["legacy_public_routes"]["fleet"] == "/transport/ride/driver"
    assert set(payload["door_groups"]) == set(payload["public_doors"])
    grouped = [cap for members in payload["door_groups"].values() for cap in members]
    assert len(grouped) == 21
    assert len(set(grouped)) == 21
    assert set(grouped) == set(payload["capabilities"])


def test_rider_driver_dashboards_preserved_under_seven_door_navigation():
    client = _app().test_client()
    for path, marker in (
        ("/transport/ride/rider", b"Request Journey"),
        ("/transport/ride/driver", b"Incoming Journey"),
        ("/transport/my", b"Rider"),
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert marker in response.data


def test_transport_inside_doors_are_html_not_technical_json():
    client = _app().test_client()
    for path, title, expected_links in (
        ("/transport/guardian", "Guardian", ("/transport/ride/current", "/transport/ride/guardian/status")),
        ("/transport/operators", "Operators", ("/transport/shared-bikes/mitcham", "/transport/shared-bikes/status")),
        ("/transport/control-center", "Control Center", ("/transport/control-center/readiness", "/transport/control-center/capabilities")),
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert response.mimetype == "text/html"
        assert response.headers["Cache-Control"] == "no-store, private"
        html = response.get_data(as_text=True)
        assert f"<h1>{title}</h1>" in html
        assert 'href="/transport"' in html
        for href in expected_links:
            assert f'href="{href}"' in html


def test_original_transport_truth_apis_preserved_after_ui_upgrade():
    client = _app().test_client()
    for path in (
        "/transport/status",
        "/transport/capabilities",
        "/transport/execution-readiness",
        "/transport/shared-bikes/status",
    ):
        response = client.get(path)
        assert response.mimetype == "application/json"
        assert response.headers["Cache-Control"] == "no-store, private"


def test_guardian_status_stays_protected_not_a_public_menu_api():
    app = _app()
    routes = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/transport/ride/guardian/status" in routes
    assert global_transport_views.status()["public_routes"]["guardian"] == "/transport/guardian"


def test_transport_front_menu_has_one_clear_seven_door_navigation():
    response = _app().test_client().get("/transport")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'aria-label="Global Transport main menu"' in html
    assert 'href="/world"' in html
    assert 'href="/transport/my"' in html
    assert "My Transport · Customer controls" in html
    assert "One World → One Front Door → Many Transport Systems Inside." not in html
    assert "Software surface ready" not in html
    assert html.count('class="card" href=') == 7
    for name, _, href in global_transport_views.PUBLIC_DOORS:
        assert f"<strong>{name}</strong>" in html
        assert f'href="{href}"' in html


def test_public_and_founder_worlds_reuse_customer_transport_without_leaking_controls():
    from pathlib import Path

    public = Path("templates/home.html").read_text(encoding="utf-8")
    android_world = Path("templates/world.html").read_text(encoding="utf-8")
    founder = Path("templates/my_world.html").read_text(encoding="utf-8")
    assert 'href="/transport"' in public
    assert 'href="/transport"' in android_world
    assert 'href="/transport/my"' in founder
    assert 'href="/my-world"' not in _app().test_client().get("/transport/my").get_data(as_text=True)


def test_execution_readiness_human_page_preserves_json_api_and_truth_boundaries(monkeypatch):
    from mission_control import global_transport_views as views

    sample = {
        "product": "OAP Global Transport",
        "software_execution_layer_ready": True,
        "live_execution_authorised": False,
        "evidence_store_reachable": True,
        "software_verified_external_authenticity": False,
        "human_authority_final": True,
        "areas": {
            "ride_dispatch": {
                "software_ready": True,
                "live_execution_authorised": False,
                "requires": ["eligible_driver_binding", "vehicle_evidence", "dispatch_receipt"],
                "verified": ["eligible_driver_binding"],
                "missing": ["vehicle_evidence", "dispatch_receipt"],
            }
        },
    }
    monkeypatch.setattr(views, "execution_readiness", lambda: sample)
    client = _app().test_client()
    page = client.get("/transport/control-center/readiness")
    assert page.status_code == 200
    assert page.mimetype == "text/html"
    assert page.headers["Cache-Control"] == "no-store, private"
    html = page.get_data(as_text=True)
    assert "Execution Readiness" in html
    assert "Not authorised" in html
    assert "1/3 recorded" in html
    assert "Eligible driver binding" in html
    assert "Verified reference recorded" in html
    assert "Vehicle evidence" in html
    assert "Missing" in html
    assert 'href="/transport/control-center"' in html

    api = client.get("/transport/execution-readiness")
    assert api.status_code == 200
    assert api.mimetype == "application/json"
    assert api.get_json() == sample


def test_execution_readiness_page_is_unknown_not_falsely_green_when_store_unreachable(monkeypatch):
    from mission_control import global_transport_views as views

    monkeypatch.setattr(views, "execution_readiness", lambda: {
        "software_execution_layer_ready": True,
        "live_execution_authorised": False,
        "evidence_store_reachable": False,
        "areas": {
            "vehicle_control": {
                "requires": ["vehicle_identity_binding", "device_or_oem_authority", "command_receipt"],
                "verified": [],
                "missing": ["vehicle_identity_binding", "device_or_oem_authority", "command_receipt"],
                "live_execution_authorised": False,
            },
        },
    })
    html = _app().test_client().get("/transport/control-center/readiness").get_data(as_text=True)
    assert "Unknown · blocked" in html
    assert "Evidence store not reachable" in html
    assert "Evidence unavailable" in html
    assert "not confirmed missing records" in html
    assert "Requirements recorded" not in html


def test_transport_noise_stripped_without_removing_seven_doors_or_authority_gates():
    client = _app().test_client()
    response = client.get("/transport")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert html.count('class="card" href=') == 7
    assert "Travel, ride and move through your world." not in html
    assert "Checking install support" not in html
    assert "Software surface ready" not in html
    assert "Where to?" in html
    for name, _, href in global_transport_views.PUBLIC_DOORS:
        assert f"<strong>{name}</strong>" in html
        assert f'href="{href}"' in html
    assert '<span>{{ description }}</span>' not in html
    status = client.get("/transport/status").get_json()
    assert status["capability_count"] == 21
    assert status["human_authority_final"] is True
    assert status["physical_operations_in_scope"] is False
    inside = client.get("/transport/control-center")
    assert inside.status_code == 200
    assert "Live services require verified availability and authorisation." in inside.get_data(as_text=True)


def test_transport_mobile_alignment_and_uncluttered_install_placeholder():
    """Both seven-door home and specialist menus keep readable touch targets."""
    from pathlib import Path

    source = Path("mission_control/global_transport_views.py").read_text(encoding="utf-8")
    page = _app().test_client().get("/transport").get_data(as_text=True)
    assert 'min-height:80px;min-width:0' in source
    assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in source
    assert '@media(max-width:320px){.grid{grid-template-columns:1fr}' in source
    assert 'overflow-wrap:break-word' in source
    assert '.install:has(> button[hidden]):has(> [role=status]:empty){display:none}' in source
    assert 'data-oap-install-status role="status" aria-live="polite"></span>' in page
    assert page.count('class="card" href=') == 7
    assert "Software surface ready" not in page
    assert 'href="/transport/ride"' in page

    for route in ("/transport/guardian", "/transport/operators", "/transport/control-center"):
        response = _app().test_client().get(route)
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert 'min-height:84px;min-width:0' in html
        assert 'min-height:44px' in html
        assert 'aria-label=' in html


def test_logistics_has_real_public_front_door_without_exposing_private_distribution():
    """A first-party Logistics tile must not link directly to a private JSON API."""
    client = _app().test_client()
    response = client.get("/transport")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'href="/transport/logistics"' in html
    assert 'class="card" href="/distribution"' not in html
    logistics = client.get("/transport/logistics")
    assert logistics.status_code == 200
    html = logistics.get_data(as_text=True)
    assert "<h1>Logistics</h1>" in html
    for label, path in (("Cargo", "/distribution"), ("Deliver", "/movement/workspace?service=delivery#book-title"), ("Fleet", "/transport/ride/driver")):
        assert f"<strong>{label}</strong>" in html
        assert f'href="{path}"' in html
    assert "Sign-in required" in html
    assert global_transport_views.status()["capability_count"] == 21


def test_specialist_menu_alignment_and_truthful_destination_labels():
    client = _app().test_client()
    for route, title in (
        ("/transport/logistics", "Logistics"),
        ("/transport/guardian", "Guardian"),
        ("/transport/operators", "Operators"),
        ("/transport/control-center", "Control Center"),
    ):
        response = client.get(route)
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert f"<h1>{title}</h1>" in html
        assert html.count('class="card" href=') == 3
        assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in html
        assert "overflow-wrap:anywhere" in html
        assert 'href="/transport"' in html
        assert 'href="/transport/my"' in html
        assert "<h1>" in html and "</h1><p>" not in html
        assert "Live services require verified availability and authorisation." in html
    logistics = client.get("/transport/logistics").get_data(as_text=True)
    assert "Sign-in required" in logistics
    operators = client.get("/transport/operators").get_data(as_text=True)
    assert "Technical availability data" in operators
    control = client.get("/transport/control-center").get_data(as_text=True)
    assert "View the 21 capability groups" in control
    assert "Evidence-gated operational status" in control
    assert global_transport_views.status()["capability_count"] == 21
    assert global_transport_views.status()["human_authority_final"] is True


def test_human_readable_control_center_preserves_legacy_json_and_all_gates(monkeypatch):
    from mission_control import global_transport_views as views

    client = _app().test_client()
    caps = client.get("/transport/control-center/capabilities")
    assert caps.status_code == 200
    assert caps.mimetype == "text/html"
    assert caps.headers["Cache-Control"] == "no-store, private"
    content = caps.get_data(as_text=True)
    assert 'aria-label="21 grouped transport capabilities"' in content
    for group in views.DOOR_GROUPS:
        assert group.replace("_", " ").title() in content
    assert sum(map(len, views.DOOR_GROUPS.values())) == 21
    assert "not permissions to operate" in content
    assert client.get("/transport/capabilities").mimetype == "application/json"

    sample = {
        "software_execution_layer_ready": True,
        "evidence_store_reachable": False,
        "live_execution_authorised": False,
        "areas": {"vehicle_control": {"live_execution_authorised": False, "missing": [], "verified": [], "requires": ["vehicle_identity_binding"]}},
    }
    monkeypatch.setattr(views, "execution_readiness", lambda: sample)
    page = client.get("/transport/control-center/status")
    assert page.status_code == 200
    assert page.mimetype == "text/html"
    assert page.headers["Cache-Control"] == "no-store, private"
    html = page.get_data(as_text=True)
    assert "Unknown · blocked" in html
    assert "Guardian, HRM and Founder Final remain in force." in html
    assert "independently verified authority" in html
    assert "Human Authority remains final" in html
    assert "Not authorised · 0 requirements outstanding" not in html
    assert client.get("/transport/execution-readiness").mimetype == "application/json"
    assert client.get("/transport/status").mimetype == "application/json"


def test_global_transport_offline_shell_preserves_seven_doors_without_private_data():
    client = _app().test_client()
    response = client.get("/transport/offline")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert response.headers["Cache-Control"] == "public, max-age=3600"
    assert "Set-Cookie" not in response.headers
    html = response.get_data(as_text=True)
    for name, _, _ in global_transport_views.PUBLIC_DOORS:
        assert f'class="tile">{name}</div>' in html
    assert html.count('class="tile"') == 7
    assert "Offline shell only" in html
    assert "Unknown · blocked" in html
    assert "Guardian, HRM and" in html
    assert "Founder Final restrictions remain in force." in html
    assert "No actions are queued or executed offline." in html
    assert 'href="/transport"' in html
    assert '<form' not in html.lower()
    assert 'data-oap-install' not in html
    assert "live transport data unavailable" in html


def test_offline_transport_worker_precaches_only_public_snapshot():
    from pathlib import Path

    worker = Path("static/oap-os-sw.js").read_text(encoding="utf-8")
    assert '"/transport/offline"' in worker
    assert 'const offlineFallback = transportPage ? "/transport/offline" : "/offline";' in worker
    assert 'fetch(request).catch(() => caches.match(offlineFallback))' in worker
    assert 'request.method !== "GET"' in worker
    assert "isPrivatePath(url.pathname)" in worker
    assert "cache.put" not in worker
    assert '"/transport/status"' not in worker.split("const PRIVATE_PREFIXES", 1)[0]
    assert '"/transport/ride/current"' not in worker.split("const PRIVATE_PREFIXES", 1)[0]


def test_founder_transport_control_is_denied_to_anonymous(anonymous_client):
    response = anonymous_client.get("/my-world/transport-control", follow_redirects=False)
    assert response.status_code in {302, 303}
    assert response.headers["Location"].startswith("/enter-my-world?next=/my-world/transport-control")
    assert "Global Transport Control Room" not in response.get_data(as_text=True)


def test_founder_transport_control_denies_authenticated_non_founder(client, monkeypatch):
    from mission_control import web_security

    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: False)
    response = client.get("/my-world/transport-control")
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "human_authority_required"


def test_founder_transport_control_uses_actual_gates_and_governed_routes(client, monkeypatch):
    from pathlib import Path

    from mission_control import web_security

    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: True)
    monkeypatch.setattr(global_transport_views, "execution_readiness", lambda: {
        "evidence_store_reachable": True,
        "live_execution_authorised": False,
        "software_verified_external_authenticity": False,
        "areas": {
            "ride_dispatch": {
                "live_execution_authorised": False,
                "missing": ["provider_authority", "dispatch_receipt"],
                "verified": [],
                "requires": ["provider_authority", "dispatch_receipt"],
            }
        },
    })
    page = client.get("/my-world/transport-control")
    assert page.status_code == 200
    assert page.mimetype == "text/html"
    assert page.headers["Cache-Control"] == "no-store, private"
    assert page.headers["X-Content-Type-Options"] == "nosniff"
    html = page.get_data(as_text=True)
    assert "Global Transport" in html and "Control Room" in html
    assert "Not authorised" in html
    assert "Locked · 2 requirements outstanding" in html
    assert 'href="/mission/all-in-ai/app"' in html
    assert 'fetch("/mission/all-in-ai/mission/latest"' in html
    assert 'data-mission-status role="status"' in html
    assert 'method: "GET"' in html
    assert 'No execution authority' in html
    for destination in (
        "/mission/ollama", "/mission/war-room", "/movement/workspace",
        "/distribution", "/transport/guardian", "/transport/control-center/readiness",
        "/mission/smi/brain/receipts", "/mission/judgement",
        "/transport/my",
    ):
        assert f'href="{destination}"' in html
    assert "<form" not in html
    founder = Path("templates/my_world.html").read_text(encoding="utf-8")
    assert 'href="/my-world/transport-control"' in founder
    assert 'href="/transport/my"' in founder
    assert 'href="/my-world/transport-control"' not in client.get("/transport").get_data(as_text=True)
    assert '/mission/all-in-ai/app' in {rule.rule for rule in client.application.url_map.iter_rules()}


def test_founder_transport_evidence_unavailable_never_shows_green(client, monkeypatch):
    from mission_control import web_security

    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: True)
    monkeypatch.setattr(global_transport_views, "execution_readiness", lambda: {
        "evidence_store_reachable": False,
        "live_execution_authorised": False,
        "software_verified_external_authenticity": False,
        "areas": {"carrier_dispatch": {"live_execution_authorised": False, "missing": [], "requires": []}},
    })
    body = client.get("/my-world/transport-control").get_data(as_text=True)
    assert "Unknown · blocked" in body
    assert "Missing proof never becomes Green" in body


def test_transport_ride_draft_flows_to_existing_movement_booking_fields():
    from pathlib import Path

    ride = _app().test_client().get("/transport/ride").get_data(as_text=True)
    workspace = Path("mission_control/templates/movement_workspace.html").read_text(encoding="utf-8")
    assert 'id="ride-pickup"' in ride
    assert 'id="ride-destination"' in ride
    assert 'action="/movement/workspace#book-title"' in ride
    assert 'sessionStorage.setItem("oap_transport_ride_draft"' in ride
    assert 'sessionStorage.getItem("oap_transport_ride_draft")' in workspace
    assert 'sessionStorage.removeItem("oap_transport_ride_draft")' in workspace
    assert 'id="pickup-query"' in workspace
    assert 'id="destination-query"' in workspace
    assert 'service.value = draft.service === "ebike" ? "ebike" : "ride"' in workspace
    assert "10 * 60 * 1000" in workspace



def test_ride_map_search_and_fare_do_not_claim_unverified_live_quotes():
    from pathlib import Path

    client = _app().test_client()
    page = client.get("/transport/ride")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert 'src="/oap-map?location=Mitcham&amp;embed=ride"' in html
    assert 'id="ride-pickup"' in html and 'id="ride-destination"' in html
    assert 'action="/movement/workspace#book-title"' in html
    assert "Price unavailable" in html
    assert 'data-mode="ride"' in html
    assert 'data-mode="ebike"' in html
    assert 'data-mode="drive"' in html
    assert 'id="map-alert"' in html
    assert 'id="ride-action"' in html
    assert 'transport/ride/backend/places' in html
    assert 'transport/ride/backend/quote' in html
    assert 'map-intelligence/suggest' not in html
    assert "Verified quote required" in html
    assert "£0" not in html
    assert 'aria-label="OAP Rides navigation"' in html
    assert '<details class="more">' in html
    assert '<section class="grid"' not in html
    assert "Software surface active." not in html
    map_template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    assert "oap-ride-embed" in map_template
    assert ".oap-ride-embed .search-card" in map_template
    assert ".oap-ride-embed .movement-actions" in map_template
    assert ".oap-ride-embed .map-controls" in map_template
    assert 'draft.service!=="drive"' in map_template
    assert 'id="map-from"' in map_template
    assert 'href="/oap-map"' in html
    assert "oap_transport_ride_draft" in html


def test_self_owned_backend_bridge_is_disconnected_without_local_service(monkeypatch):
    monkeypatch.delenv("OAP_RIDE_BACKEND_URL", raising=False)
    client = _app().test_client()
    result = client.get("/transport/ride/backend/status")
    assert result.status_code == 503
    assert result.get_json()["production_ready"] is False
    assert result.get_json()["connected"] is False
    assert result.headers["Cache-Control"] == "no-store"
    assert client.get("/transport/ride/backend/places?q=Mitcham").status_code == 503
    monkeypatch.setenv("OAP_RIDE_BACKEND_URL", "https://unapproved.example/api")
    assert client.get("/transport/ride/backend/status").status_code == 503


def test_self_owned_backend_bridge_checks_real_osrm_quote(monkeypatch):
    from mission_control import oap_ride_backend_bridge as bridge
    from mission_control import web_security

    calls = []

    def fake_read(path, body=None):
        calls.append((path, body))
        if path == "/healthz":
            return {
                "service": "oap_ride_phase1",
                "status": "database_and_redis_ready",
                "route_engine_configured": True,
                "demo_mode": True,
            }
        if path == "/v1/platform/readiness":
            return {"phase": 1, "production_ready": False}
        if path.startswith("/v1/places?"):
            return {"geocoder": "local_seed_only", "results": [
                {"label": "Mitcham", "lat": 51.4, "lon": -0.17},
            ]}
        if path == "/v1/rides/quote":
            return {
                "quote_status": "estimate_not_firm_fare",
                "source": "self_hosted_osrm",
                "currency": "GBP", "amount_minor": 1234,
                "distance_m": 2500, "duration_s": 600,
                "licensed_payment_connected": False,
                "live_dispatch_confirmed": False,
            }
        raise AssertionError(path)

    monkeypatch.setattr(bridge, "_read", fake_read)
    client = _app().test_client()
    status = client.get("/transport/ride/backend/status")
    assert status.status_code == 200
    assert status.get_json()["connected"] is True
    assert status.get_json()["quote_ready"] is False
    assert status.get_json()["production_ready"] is False

    places = client.get("/transport/ride/backend/places?q=Mitcham")
    assert places.status_code == 200
    assert places.get_json()["source"] == "self_hosted_seed"
    assert places.get_json()["results"][0]["lat"] == 51.4

    body = {"vehicle_class": "car", "pickup_lat": 51.4,
            "pickup_lon": -0.17, "drop_lat": 51.41, "drop_lon": -0.16}
    assert client.post("/transport/ride/backend/quote", json=body).status_code == 403
    with client.session_transaction() as s:
        s[web_security.CSRF_SESSION_KEY] = "test-quote-token" * 4
    assert client.post(
        "/transport/ride/backend/quote",
        json={**body, "drop_lat": float("nan")},
        headers={"X-OAP-CSRF": "test-quote-token" * 4},
    ).status_code == 400
    quoted = client.post(
        "/transport/ride/backend/quote", json=body,
        headers={"X-OAP-CSRF": "test-quote-token" * 4},
    )
    assert quoted.status_code == 200
    assert quoted.get_json()["amount_minor"] == 1234
    assert quoted.get_json()["live_dispatch_confirmed"] is False
    assert ("/v1/rides/quote", body) in calls
    assert not any(path == "/v1/rides" for path, _ in calls)
