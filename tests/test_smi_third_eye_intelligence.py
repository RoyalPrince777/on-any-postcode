from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import app as app_module
from mission_control import third_eye_intelligence, web_security

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
    status = third_eye_intelligence.status()
    assert status["founder_private_only"] is True
    assert status["public_route_allowed"] is False
    assert status["sources"]["public_cameras"]["live_feed_proven"] is False
    assert status["sources"]["3d_globe"]["render_proven"] is False
    assert status["upstream_reference"]["upstream_code_imported"] is False
    assert status["full_third_eye_ready"] is False
    assert status["individual_tracking"] is False


def test_fresh_attributed_earth_observation():
    result = third_eye_intelligence.parse_usgs_feed(feed(), now=NOW)
    assert result["feed_verified"] is True
    assert result["freshness"] == "fresh"
    assert result["events"][0]["latitude"] == 51.5
    assert result["full_third_eye_ready"] is False


def test_stale_and_future_provenance_never_count_as_live():
    for generated in (T - 900_001, T + 30_000):
        result = third_eye_intelligence.parse_usgs_feed(feed(generated), now=NOW)
        assert result["freshness"] == "stale"
        assert result["live_claim_allowed"] is False


def test_undated_or_incorrect_feed_fails_closed():
    for payload in ({"type": "FeatureCollection", "metadata": {}, "features": []}, [], {}, None):
        try:
            third_eye_intelligence.parse_usgs_feed(payload, now=NOW)
        except ValueError:
            pass
        else:
            raise AssertionError("unattributed data must fail closed")


def test_invalid_geography_is_ignored_and_events_bounded():
    payload = feed()
    payload["features"] *= 30
    payload["features"][0]["geometry"]["coordinates"] = [900, 91]
    result = third_eye_intelligence.parse_usgs_feed(payload, now=NOW)
    assert result["events"] == []
    assert result["event_count_returned"] == 0


def test_network_failure_returns_unavailable_without_live_claim():
    with patch.object(third_eye_intelligence, "urlopen", side_effect=TimeoutError("No network")):
        result = third_eye_intelligence.latest_earthquakes()
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


def test_founder_authorised_status_is_read_only_and_uncached(client, monkeypatch):
    monkeypatch.setattr(
        web_security, "current_authenticated_user",
        lambda: {"id": "00000000-0000-4000-8000-000000000001"},
    )
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: True)
    response = client.get("/mission/smi/third-eye/status")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    state = response.get_json()
    assert state["founder_private_only"] is True
    assert state["camera_view"]["device_camera_started"] is False
    assert state["sources"]["earthquakes"]["feed_proven"] is False


def test_third_eye_is_one_tool_in_smi_not_a_public_duplicate():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "mission_control"
    template = (root / "templates" / "ollama_chat.html").read_text(encoding="utf-8")
    script = (root / "static" / "smi_third_eye.js").read_text(encoding="utf-8")
    assert "thirdEyeStatusUrl:" in template
    assert "thirdEyeEarthquakesUrl:" in template
    assert "filename='smi_third_eye.js'" in template
    assert "smi-third-eye-menu-button" in script
    assert "attach-menu" in script
    assert "smi-third-eye-panel" in script
    assert "credentials: \"same-origin\"" in script
    assert "cache: \"no-store\"" in script
    assert "events.replaceChildren()" in script
    assert "li.textContent" in script
    assert "getUserMedia" not in script
    assert "getCurrentPosition" not in script
    assert "setInterval" not in script
    assert "Full Third Eye ready" not in script


def test_third_eye_seven_views_are_nested_inside_one_smi_tool():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "mission_control"
    script = (root / "static" / "smi_third_eye.js").read_text(encoding="utf-8")
    css = (root / "static" / "smi_third_eye.css").read_text(encoding="utf-8")

    for name in (
        "Earth Vision",
        "Ground Vision",
        "Air Vision",
        "Space Vision",
        "Earth Intelligence",
        "SMI Analysis",
        "Controls",
    ):
        assert f'name: "{name}"' in script
    assert 'id="smi-third-eye-internal-menu"' in script
    assert 'id="smi-third-eye-back"' in script
    assert "internalMenu.appendChild(button)" in script
    assert script.count("menu.appendChild(menuButton)") == 1
    assert "smi-third-eye-menu-item" in css
    assert 'document.getElementById("faceup-button")' in script
    assert "getUserMedia" not in script
    assert "setInterval" not in script
