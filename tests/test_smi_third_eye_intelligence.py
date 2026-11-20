from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import app as app_module
from mission_control import third_eye_intelligence as third_eye
from mission_control import web_security


NOW = datetime(2026, 11, 20, 1, 0, tzinfo=UTC)
T = int(NOW.timestamp() * 1000)


def feed(generated=T):
    return {
        "type": "FeatureCollection",
        "metadata": {"generated": generated},
        "features": [
            {
                "type": "Feature",
                "properties": {"place": "Near Testville", "mag": 3.2, "time": T},
                "geometry": {"coordinates": [-0.15, 51.5, 4.0]},
            }
        ],
    }


def test_status_never_infers_camera_or_full_runtime():
    status = third_eye.status()
    assert status["founder_private_only"] is True
    assert status["public_route_allowed"] is False
    assert status["sources"]["public_cameras"]["live_feed_proven"] is False
    assert status["sources"]["3d_globe"]["render_proven"] is False
    assert status["upstream_reference"]["upstream_code_imported"] is False
    assert status["full_third_eye_ready"] is False
    assert status["individual_tracking"] is False


def test_fresh_attributed_earth_observation():
    result = third_eye.parse_usgs_feed(feed(), now=NOW)
    assert result["feed_verified"] is True
    assert result["freshness"] == "fresh"
    assert result["events"][0]["latitude"] == 51.5
    assert result["full_third_eye_ready"] is False


def test_stale_and_future_provenance_never_count_as_live():
    for generated in (T - 900_001, T + 30_000):
        result = third_eye.parse_usgs_feed(feed(generated), now=NOW)
        assert result["freshness"] == "stale"
        assert result["live_claim_allowed"] is False


def test_undated_or_incorrect_feed_fails_closed():
    for payload in ({"type": "FeatureCollection", "metadata": {}, "features": []}, [], {}, None):
        try:
            third_eye.parse_usgs_feed(payload, now=NOW)
        except ValueError:
            pass
        else:
            raise AssertionError("unattributed data must fail closed")


def test_invalid_geography_is_ignored_and_events_bounded():
    payload = feed()
    payload["features"] *= 30
    payload["features"][0]["geometry"]["coordinates"] = [900, 91]
    result = third_eye.parse_usgs_feed(payload, now=NOW)
    assert result["events"] == []
    assert result["event_count_returned"] == 0


def test_network_failure_returns_unavailable_without_live_claim():
    with patch.object(third_eye, "urlopen", side_effect=TimeoutError("No network")):
        result = third_eye.latest_earthquakes()
    assert result["feed_verified"] is False
    assert result["events"] == []
    assert result["live_claim_allowed"] is False


def test_private_routes_have_existing_founder_auth_metadata():
    for endpoint in ("alignment.smi_third_eye_status", "alignment.smi_third_eye_earthquakes"):
        view = app_module.app.view_functions[endpoint]
        assert view._oap_login_required is True
        assert view._oap_founder_only is True
        assert view._oap_api is True


def test_anonymous_earth_and_status_requests_are_denied(client, monkeypatch):
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    for path in ("/mission/smi/third-eye/status", "/mission/smi/third-eye/earthquakes"):
        response = client.get(path)
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "authentication_required"
        assert response.headers["Cache-Control"] == "no-store"
