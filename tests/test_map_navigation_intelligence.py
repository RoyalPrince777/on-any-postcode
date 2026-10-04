from pathlib import Path

from mission_control import mobility_provider_intelligence

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "mission_control" / "templates" / "local_map.html"
NAV = ROOT / "mission_control" / "static" / "oap_map_navigation.js"
CSS = ROOT / "mission_control" / "static" / "oap_map_navigation.css"
ROUTES = ROOT / "mission_control" / "on_any_place_routes.py"


def test_map_screen_is_low_noise_and_map_first():
    page = MAP.read_text(encoding="utf-8")
    assert 'class="map-app"' in page
    assert 'class="search-card"' in page
    assert 'id="turn-card"' in page
    assert 'id="trip-bar"' in page
    assert 'id="details-sheet"' in page
    assert "People Intelligence" not in page
    assert "Route Intelligence" not in page
    assert "ETA Intelligence" not in page
    assert "Live Pattern" not in page
    assert "Source intelligence" not in page
    assert "Master Map Intelligence" not in page
    assert "Manage Certified Merchant listings" not in page
    assert "OAP OS · Map web runtime" not in page


def test_drive_runtime_updates_turns_and_follows_position():
    script = NAV.read_text(encoding="utf-8")
    for marker in (
        "navigator.geolocation.watchPosition",
        "activeStep(progress)",
        "updateTurn(progress)",
        "driveMode",
        "viewCenter=[lastProjected[0],Math.min(610,lastProjected[1]+70)]",
        "setZoom",
        "storesPreciseLocation:false",
        "individualPeopleTracking:false",
        "lowNoise:true",
        "driveFollow:true",
        "progressiveTurnGuidance:true",
    ):
        assert marker in script


def test_noise_heavy_chrome_is_removed():
    css = CSS.read_text(encoding="utf-8")
    for removed in (
        ".intel-strip",
        ".intel-chip",
        ".map-mode-rail",
        ".map-source-drawer",
        ".footer-nav",
    ):
        assert removed not in css
    for kept in (
        ".search-card",
        ".turn-card",
        ".trip-bar",
        ".details-sheet",
        ".vehicle-marker",
    ):
        assert kept in css


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


def test_first_party_renderer_has_sparse_road_hierarchy_and_labels():
    page = MAP.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    assert "labelCount<18" in page
    assert "feature.name" in page
    assert "poly.setAttribute('class',isMajor?'major':isSecondary?'secondary':'local')" in page
    assert ".road-svg polyline.local" in css
    assert ".road-svg polyline.secondary" in css
    assert ".road-svg polyline.major" in css
    assert ".road-label" in css


def test_drive_camera_is_heading_up_without_rotating_controls():
    script = NAV.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    assert "lastHeading" in script
    assert "perspective(900px) rotateX(22deg)" in script
    assert "if(driveMode)applyView()" in script
    assert "roadsSvg.style.transform=mapTransform" in script
    assert "routeSvg.style.transform=mapTransform" in script
    assert 'body[data-map-mode="drive"] .road-label{opacity:.58' in css
    assert "transform-origin:50% 50%" in css


def test_drive_runtime_has_bounded_off_route_reroute_without_location_storage():
    script = NAV.read_text(encoding="utf-8")
    page = MAP.read_text(encoding="utf-8")
    routes = ROUTES.read_text(encoding="utf-8")

    for marker in (
        "OFF_ROUTE_METERS=80",
        "REROUTE_SAMPLES=3",
        "REROUTE_COOLDOWN_MS=15000",
        "oap-map-reroute-request",
        "offRouteReroute:true",
        "storesPreciseLocation:false",
    ):
        assert marker in script

    assert "from_lat" in page
    assert "from_lon" in page
    assert "cache:'no-store'" in page
    assert "Current position" in routes
    assert "route_origin_coordinates_incomplete" in routes
    assert "route_origin_coordinates_invalid" in routes


def test_reroute_requires_drive_mode_and_sustained_deviation():
    script = NAV.read_text(encoding="utf-8")
    assert "if(!driveMode||!currentRoute||!Number.isFinite(distanceM))return;" in script
    assert "distanceM>OFF_ROUTE_METERS?offRouteSamples+1:0" in script
    assert "offRouteSamples<REROUTE_SAMPLES" in script


def test_map_voice_guidance_is_user_controlled_and_non_persistent():
    script = NAV.read_text(encoding="utf-8")
    page = MAP.read_text(encoding="utf-8")
    assert 'id="voice-toggle"' in page
    assert "voiceEnabled=false" in script
    assert "voiceToggle?.addEventListener('click',()=>setVoice(!voiceEnabled))" in script
    assert "SpeechSynthesisUtterance" in script
    assert "utterance.lang='en-GB'" in script
    assert "voiceTurnGuidance:true" in script
    assert "voiceUserControlled:true" in script
    assert "voiceAudioStored:false" in script
    assert "cancelGuidanceVoice()" in script
    assert "window.addEventListener('pagehide'" in script


def test_map_voice_does_not_open_microphone_or_store_precise_location():
    script = NAV.read_text(encoding="utf-8")
    assert "getUserMedia" not in script
    assert "SpeechRecognition" not in script
    assert "storesPreciseLocation:false" in script
    assert "individualPeopleTracking:false" in script


def test_public_map_uses_allowlisted_public_navigation_assets(client):
    page = client.get("/on-any-place")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "/map-intelligence/assets/oap_map_navigation.css" in body
    assert "/map-intelligence/assets/oap_map_navigation.js" in body
    assert "/map-intelligence/assets/oap_os_map_bridge.js" in body
    assert 'data-oap-os-map-runtime' not in body
    assert "/mission/static/oap_map_navigation.css" not in body

    css = client.get("/map-intelligence/assets/oap_map_navigation.css")
    js = client.get("/map-intelligence/assets/oap_map_navigation.js")
    bridge = client.get("/map-intelligence/assets/oap_os_map_bridge.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert bridge.status_code == 200
    assert css.headers["X-Content-Type-Options"] == "nosniff"

    assert client.get("/map-intelligence/assets/mission_control.css").status_code == 404
    assert client.get("/map-intelligence/assets/../views.py").status_code == 404


def test_map_hud_exposes_truth_gated_live_traffic_state():
    page = MAP.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    assert 'id="traffic-state"' in page
    assert "live_claim_allowed" in page
    assert "reroute_recommended" in page
    assert '#traffic-state[data-live="true"]' in css


def test_map_page_has_server_visible_shell_without_install_service_worker(client):
    page = client.get("/on-any-place")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert 'id="oap-map-critical"' in body
    assert 'id="oap-map-boot"' in body
    assert "On Any Postcode Maps · loading roads" in body
    assert "/assets/oap-os.js" not in body
    assert "oap_luxury.css" not in body
    assert "_oap_install_head.html" not in body


def test_unique_oap_map_door_renders_same_real_map_shell(client):
    page = client.get("/oap-map")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert 'class="map-app"' in body
    assert 'id="roads-svg"' in body
    assert 'id="map-form"' in body
    assert 'id="oap-map-boot"' in body
    assert "/map-intelligence/assets/oap_map_navigation.css" in body


def test_map_runtime_assets_are_versioned_and_revalidated(client):
    page = client.get("/oap-map")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "oap_map_navigation.css?v=map-runtime-v4" in body
    assert "oap_map_navigation.js?v=map-runtime-v4" in body
    assert "oap_os_map_bridge.js?v=map-runtime-v4" in body

    css = client.get("/map-intelligence/assets/oap_map_navigation.css?v=map-runtime-v4")
    js = client.get("/map-intelligence/assets/oap_map_navigation.js?v=map-runtime-v4")
    assert css.status_code == 200
    assert js.status_code == 200
    assert css.headers["Cache-Control"] == "no-cache, max-age=0, must-revalidate"
    assert js.headers["Cache-Control"] == "no-cache, max-age=0, must-revalidate"


def test_map_render_is_atomic_and_has_no_timeout_fake_ready():
    page = MAP.read_text(encoding="utf-8")

    assert "roadLayer.replaceChildren(staged)" in page
    assert "document.createDocumentFragment()" in page
    assert "setRenderState('stable')" in page
    assert "setRenderState('degraded')" in page
    assert "await loadRoadNetwork(bounds,profile.value)" in page
    assert "if(from.value.trim()&&to.value.trim())route();else loadRoadNetwork(defaultBounds,profile.value)" in page
    assert "setTimeout(clearBoot,5000)" not in page
    assert ".oap-map-boot[hidden]{display:none!important}" in page


def test_route_waits_for_road_context_before_exposing_complete_map():
    page = MAP.read_text(encoding="utf-8")

    assert "svg.hidden=true;setRenderState('loading')" in page
    assert "const roadCount=await loadRoadNetwork(bounds,profile.value)" in page
    assert "svg.hidden=false" in page
    assert "setRenderState(roadCount>0?'stable':'degraded')" in page


def test_route_sets_loading_before_async_fetch_to_prevent_stale_stable_race():
    page = MAP.read_text(encoding="utf-8")
    route = page.split("async function route(options={}){", 1)[1].split(
        "form.addEventListener('submit'", 1
    )[0]

    loading_index = route.index("setRenderState('loading')")
    fetch_index = route.index("fetch('/map-intelligence/route?")
    assert loading_index < fetch_index
