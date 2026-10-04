from __future__ import annotations

import app as app_module

from mission_control import smi_function_health


def test_smi_fixed_navigation_paths_are_registered_get_routes():
    integrity = smi_function_health.ui_route_integrity(app_module.app.url_map)

    assert integrity["all_registered"] is True
    assert integrity["no_404_routing_gap"] is True
    assert integrity["registered_count"] == integrity["expected_count"]
    assert not [item for item in integrity["paths"] if not item["registered"]]


def test_smi_public_workspace_tabs_do_not_404(client):
    for path in (
        "/search?q=OAP",
        "/on-any-place",
        "/oap-map",
        "/movement",
        "/travel/direct",
        "/map-intelligence/status",
    ):
        response = client.get(path)
        assert response.status_code != 404, path


def test_function_health_includes_no_404_ui_integrity(monkeypatch):
    monkeypatch.setattr(
        smi_function_health.smi_chat_runtime,
        "health",
        lambda: {"status": "green", "checks": {}},
    )
    result = smi_function_health.function_health(app_module.app.url_map)

    assert result["ui_route_integrity"]["no_404_routing_gap"] is True
    assert result["ui_route_integrity"]["availability_percent"] == 100.0
