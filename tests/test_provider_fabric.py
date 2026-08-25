from __future__ import annotations

import json

from mission_control import location_intelligence, provider_fabric


def test_provider_fabric_has_locked_capability_slots_and_read_only_adapters():
    validation = provider_fabric.validate_provider_fabric()

    assert validation["passed"] is True
    assert validation["errors"] == []
    assert validation["checks"] == {
        "slots": 8,
        "wired_adapters": 3,
        "duplicate_slot_ids": 0,
        "duplicate_adapter_ids": 0,
        "unknown_slot_links": 0,
        "mutation_adapters": 0,
        "privileged_controls_enabled": 0,
    }
    assert {item["id"] for item in provider_fabric.PROVIDER_SLOTS} == {
        "postcode",
        "geocoding",
        "weather",
        "routing",
        "telecom",
        "payments",
        "dispatch",
        "communications",
    }
    assert all(
        adapter["mode"] == "read_only" and adapter["mutation_enabled"] is False
        for adapter in provider_fabric.WIRED_ADAPTERS
    )


def test_runtime_evidence_is_separate_from_wiring(monkeypatch):
    monkeypatch.setattr(
        location_intelligence,
        "status",
        lambda: {
            "postcode_provider_verified": True,
            "global_provider_verified": False,
            "weather_provider_verified": True,
        },
    )

    fabric = provider_fabric.get_private_provider_fabric()
    by_id = {item["id"]: item for item in fabric["slots"]}

    assert fabric["summary"] == {
        "slots": 8,
        "wired": 3,
        "runtime_verified": 2,
        "provider_required": 5,
    }
    assert by_id["postcode"]["wired"] is True
    assert by_id["postcode"]["runtime_verified"] is True
    assert by_id["postcode"]["status"] == "Runtime verified"
    assert by_id["geocoding"]["wired"] is True
    assert by_id["geocoding"]["runtime_verified"] is False
    assert by_id["geocoding"]["status"] == "Wired · awaiting runtime evidence"
    assert by_id["routing"]["wired"] is False
    assert by_id["routing"]["status"] == "Provider required"


def test_consequential_provider_controls_fail_closed():
    assert provider_fabric.HUMAN_APPROVAL_REQUIRED is True
    assert provider_fabric.CONSEQUENTIAL_CONTROLS
    assert not any(provider_fabric.CONSEQUENTIAL_CONTROLS.values())


def test_unknown_slot_and_mutation_adapter_are_rejected():
    bad_adapter = {
        "id": "bad",
        "slot_id": "unknown",
        "name": "Bad",
        "host": "example.invalid",
        "mode": "write",
        "wired": True,
        "mutation_enabled": True,
        "credential_required": True,
    }
    validation = provider_fabric.validate_provider_fabric(
        adapters=(*provider_fabric.WIRED_ADAPTERS, bad_adapter)
    )

    assert validation["passed"] is False
    assert validation["checks"]["unknown_slot_links"] == 1
    assert validation["checks"]["mutation_adapters"] == 1


def test_provider_projection_never_contains_secret_material(monkeypatch):
    monkeypatch.setattr(location_intelligence, "status", lambda: {})
    serialized = json.dumps(provider_fabric.get_private_provider_fabric()).lower()

    for forbidden in (
        "api_key",
        "access_token",
        "password",
        "credential_value",
        "activation_code",
        "iccid",
        "imsi",
    ):
        assert forbidden not in serialized


def test_private_provider_dashboard_is_read_only(client, monkeypatch):
    monkeypatch.setattr(location_intelligence, "status", lambda: {})

    response = client.get("/mission/providers")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "OAP Provider Fabric" in page
    assert "Capability contracts" in page
    assert "UK Postcode Service" in page
    assert "Global Place Service" in page
    assert "Live Weather Service" in page
    assert "Telecom / eSIM" in page
    assert "Payments" in page
    assert "Fleet / dispatch" in page
    assert "No approved adapter wired." in page
    assert "Configuration never counts as proof by itself." in page
    assert 'method="post"' not in page.lower()
    assert client.post("/mission/providers").status_code == 405


def test_provider_status_is_coarse_and_non_operational(client, monkeypatch):
    monkeypatch.setattr(
        location_intelligence,
        "status",
        lambda: {
            "postcode_provider_verified": True,
            "global_provider_verified": True,
            "weather_provider_verified": True,
        },
    )

    response = client.get("/mission/providers/status")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload == {
        "architecture_passed": True,
        "slots": 8,
        "wired": 3,
        "runtime_verified": 3,
        "consequential_execution_enabled": False,
        "human_authority_required": True,
    }


def test_mission_control_links_to_provider_fabric(client):
    page = client.get("/mission").get_data(as_text=True)

    assert 'href="/mission/providers"' in page
    assert ">Provider Fabric</a>" in page
