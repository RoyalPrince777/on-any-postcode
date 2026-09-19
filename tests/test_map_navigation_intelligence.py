from pathlib import Path

from mission_control import mobility_provider_intelligence

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "mission_control" / "templates" / "local_map.html"
NAV = ROOT / "mission_control" / "static" / "oap_map_navigation.js"
CSS = ROOT / "mission_control" / "static" / "oap_map_navigation.css"
ROUTES = ROOT / "mission_control" / "on_any_place_routes.py"


def test_major_app_navigation_modes_are_visible():
    page = MAP.read_text(encoding="utf-8")
    for mode in ("explore", "journey", "drive", "cockpit"):
        assert f'data-map-mode="{mode}"' in page
    for marker in (
        "Navigation intelligence",
        "ETA Intelligence",
        "Route Intelligence",
        "People Intelligence",
        "Live Pattern",
        "Mobility",
    ):
        assert marker in page


def test_navigation_runtime_is_truth_first_and_privacy_safe():
    script = NAV.read_text(encoding="utf-8")
    assert "navigator.geolocation.watchPosition" in script
    assert "storesPreciseLocation:false" in script
    assert "individualPeopleTracking:false" in script
    assert "aggregate only" in script
    assert "oap-map-route-ready" in script
    assert "/map-intelligence/oap-adapter" in script


def test_drive_and_cockpit_strip_sidebar_noise():
    css = CSS.read_text(encoding="utf-8")
    assert 'body[data-map-mode="drive"] .side' in css
    assert 'body[data-map-mode="cockpit"] .side' in css
    assert ".nav-hud" in css
    assert ".vehicle-marker" in css


def test_map_route_allows_only_same_origin_embedding_and_consented_location():
    source = ROUTES.read_text(encoding="utf-8")
    assert '"X-Frame-Options"] = "SAMEORIGIN"' in source
    assert "frame-ancestors 'self'" in source
    assert '"camera=(), microphone=(), geolocation=(self), payment=()"' in source
    assert '"X-OAP-Precise-Location-Stored"] = "false"' in source


def test_uber_provider_is_fail_closed_without_approval(monkeypatch):
    monkeypatch.delenv("OAP_UBER_API_APPROVED", raising=False)
    monkeypatch.delenv("OAP_UBER_ACCESS_TOKEN", raising=False)
    status = mobility_provider_intelligence.status()
    uber = next(item for item in status["providers"] if item["id"] == "uber")
    assert uber["live_ready"] is False
    result = mobility_provider_intelligence.estimates(
        start_latitude=51.4,
        start_longitude=-0.16,
        end_latitude=51.5,
        end_longitude=-0.08,
    )
    assert result["state"] == "locked"
    assert result["live_ready"] is False
    assert status["component"] == "OAP Adapter · Mobility Intelligence"
    assert status["individual_people_tracking"] is False
    assert status["precise_device_location_stored"] is False
