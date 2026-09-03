from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from mission_control import link_presence_routes

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "mission_control" / "templates" / "linkup.html"
SCRIPT = ROOT / "static" / "linkup_presence.js"


def test_presence_visibility_state_route_is_authenticated_coarse_and_no_store(
    client, monkeypatch
):
    peer_id = "11111111-1111-1111-1111-111111111111"
    monkeypatch.setattr(
        link_presence_routes,
        "_visibility_state",
        lambda _identity, _peer: {"around_now": True, "live_spot": False},
    )

    response = client.get(f"/linkup/presence/visibility/{peer_id}")

    assert response.status_code == 200
    assert response.get_json() == {"around_now": True, "live_spot": False}
    assert response.headers["Cache-Control"] == "no-store"


def test_linkup_surface_exposes_oap_presence_controls_without_external_provider():
    template = TEMPLATE.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")

    assert "linkup_presence.js" in template
    assert "data-oap-around-control" in template
    assert "data-oap-share-spot-control" in template
    assert "data-oap-live-spot-control" in template
    assert "data-oap-live-spot-stop" in template
    assert "data-oap-presence-status" in template

    assert "/linkup/presence/status" in script
    assert "/linkup/presence/visibility/" in script
    assert "/linkup/presence/heartbeat" in script
    assert "/linkup/live-spot" in script
    assert "navigator.geolocation.getCurrentPosition" in script
    assert "navigator.geolocation.watchPosition" in script
    assert "navigator.geolocation.clearWatch" in script
    assert "credentials: \"same-origin\"" in script
    assert "cache: \"no-store\"" in script
    assert "http://" not in script
    assert "https://" not in script


def test_location_permission_is_only_reached_from_user_action_helpers():
    script = SCRIPT.read_text(encoding="utf-8")

    assert "const positionOnce = () =>" in script
    assert "shareSpotControls.forEach" in script
    assert "liveSpotControls.forEach" in script
    assert 'control.addEventListener("click"' in script
    assert "positionOnce()" in script
    assert "watchPosition(" in script
    assert "api(\"/linkup/presence/status\")" in script


def test_presence_browser_controller_has_valid_javascript_syntax():
    node = shutil.which("node")
    if node is None:
        return

    subprocess.run(
        [node, "--check", str(SCRIPT)],
        check=True,
        capture_output=True,
        text=True,
    )
