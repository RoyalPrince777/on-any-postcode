from __future__ import annotations

from pathlib import Path

from mission_control import on_any_place_routes


def test_default_london_route_anchors_are_deterministic():
    mitcham = on_any_place_routes._route_location("Mitcham")
    bridge = on_any_place_routes._route_location("London Bridge")

    assert mitcham["postcode"] == "CR4"
    assert mitcham["borough"] == "Merton"
    assert mitcham["country"] == "United Kingdom"
    assert mitcham["latitude"] == 51.4036
    assert mitcham["longitude"] == -0.1687

    assert bridge["postcode"] == "SE1"
    assert bridge["borough"] == "Southwark"
    assert bridge["country"] == "United Kingdom"
    assert bridge["latitude"] == 51.5079
    assert bridge["longitude"] == -0.0877


def test_unknown_route_place_still_uses_location_intelligence(monkeypatch):
    observed = {}

    def fake_lookup(value):
        observed["value"] = value
        return {"latitude": 1.0, "longitude": 2.0}

    monkeypatch.setattr(
        on_any_place_routes.location_intelligence,
        "lookup",
        fake_lookup,
    )

    result = on_any_place_routes._route_location("Begoro")

    assert observed["value"] == "Begoro"
    assert result == {"latitude": 1.0, "longitude": 2.0}


def test_mobile_map_is_full_viewport_with_floating_controls():
    template = Path(
        "mission_control/templates/local_map.html"
    ).read_text(encoding="utf-8")
    css = Path(
        "mission_control/static/oap_map_navigation.css"
    ).read_text(encoding="utf-8")

    assert 'class="map-wrap"' in template
    assert 'id="route-svg"' in template
    assert 'class="search-card"' in template
    assert 'id="trip-bar"' in template
    assert ".map-app,.map-wrap{position:relative;width:100%;height:100dvh" in css
    assert ".side{" not in css


def test_public_map_door_uses_visible_first_party_renderer():
    source = Path(
        "mission_control/on_any_place_routes.py"
    ).read_text(encoding="utf-8")

    assert '@bp.get("/on-any-place")' in source
    assert 'render_template("local_map.html", local_map=local_map)' in source
    assert "'/map-intelligence/road-geometry/" in Path(
        "mission_control/templates/local_map.html"
    ).read_text(encoding="utf-8")


def test_road_network_loads_without_successful_route():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")

    assert "if(from.value.trim()&&to.value.trim())route();else loadRoadNetwork(defaultBounds,profile.value);" in template
    assert 'id="road-source-state"' in template
    assert "if(request!==roadRequest)return 0;" in template
    assert "if(batchAttempt<1)" in template
    assert "loadRoadNetwork(b,mode,batchAttempt+1,request)" in template
    assert "clearBoot();setRenderState('degraded');showRoadStatus('Road network unavailable — route guidance may still work.');" in template


def test_route_failure_preserves_independent_road_layer():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    route_section = template.split("async function route(", 1)[1].split(
        "form.addEventListener('submit'", 1
    )[0]

    assert "roadLayer.innerHTML=''" not in route_section
    assert "if(request!==roadRequest||!d||!Array.isArray(d.lines))return;" in template
    assert "if(request!==roadRequest)return 0;" in template
    assert "profile.addEventListener('change'" in template


def test_oap_os_generation_zero_map_binding_stays_non_visual_and_consent_safe():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    bridge = Path("mission_control/static/oap_os_map_bridge.js").read_text(encoding="utf-8")
    documentation = Path("docs/OAP_OPERATING_SYSTEM_V0.md").read_text(encoding="utf-8")

    assert 'id="oap-os-map-runtime"' not in template
    assert "oap_os_map_bridge.js" in template
    assert "android-web" in bridge
    assert "installed web shell" in bridge
    assert "unverified" in bridge
    assert "MutationObserver" in bridge
    assert "geolocation." not in bridge
    assert "serviceWorker.register" not in bridge
    assert "Android/Linux host kernel" in documentation


def test_road_network_loader_reaches_a_terminal_state_when_a_tile_stalls():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")

    assert "const ROAD_TILE_TIMEOUT_MS=3000;" in template
    assert "const controller=new AbortController();" in template
    assert "signal:controller.signal" in template
    assert "finally{clearTimeout(timeout)}" in template
    assert "const renderPayload=d=>" in template
    assert "const queue=[...tiles];" in template
    assert "const worker=async()=>{while(queue.length&&request===roadRequest&&count<180)" in template
    assert "Math.min(4,tiles.length)" in template
    assert "roadLayer.replaceChildren(staged);" in template
    assert "showRoadStatus('');clearBoot();setRenderState('stable');" in template
    assert "Road network unavailable — route guidance may still work." in template


def test_route_draw_preserves_existing_road_layer():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    draw_section = template.split("async function draw(coords){", 1)[1].split(
        "function lon2x", 1
    )[0]

    assert "await loadRoadNetwork(bounds,profile.value)" in draw_section
    assert "if(!roadLayer.querySelector('polyline'))loadRoadNetwork(bounds,profile.value);" not in draw_section


def test_map_boot_clears_only_after_terminal_road_state():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    assert "showRoadStatus('');clearBoot();setRenderState('stable');" in template
    assert "clearBoot();setRenderState('degraded')" in template
    assert "setTimeout(clearBoot,5000);" not in template


def test_road_tiles_are_prioritised_and_bounded_instead_of_flooded():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    assert "tiles.sort((a,b)=>" in template
    assert "const batchSize=4,batchStart=batchAttempt*batchSize;" in template\n    assert "tiles=tiles.slice(batchStart,batchStart+batchSize);" in template
    assert "Math.min(4,tiles.length)" in template
    assert "for(let attempt=0;attempt<1;attempt++)" in template
    assert "response.status!==503" in template


def test_on_any_postcode_maps_public_identity_and_navigation_camera():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    css = Path("mission_control/static/oap_map_navigation.css").read_text(encoding="utf-8")
    nav = Path("mission_control/static/oap_map_navigation.js").read_text(encoding="utf-8")
    assert "<title>On Any Postcode Maps</title>" in template
    assert 'aria-label="On Any Postcode Maps"' in template
    assert 'id="route-casing"' in template
    assert "history.replaceState(null,'','/oap-map?" in template
    assert "perspective(900px) rotateX(22deg)" in nav
    assert "perspectiveDriveCamera:true" in nav
    assert "routeCasing:true" in nav
    assert ".route-svg #route-casing" in css


def test_road_network_has_bounded_batch_level_cold_start_recovery():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    assert "async function loadRoadNetwork(b,mode,batchAttempt=0,requestToken=null)" in template
    assert "request=requestToken===null?++roadRequest:requestToken" in template
    assert "if(batchAttempt<1)" in template
    assert "1000*(batchAttempt+1)" in template
    assert "loadRoadNetwork(b,mode,batchAttempt+1,request)" in template
    assert "setRenderState('loading')" in template


def test_road_network_does_not_self_cancel_slow_successful_batches():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    assert "const ROAD_TILE_TIMEOUT_MS=3000;" in template
    assert "recoveryTimer" not in template
    assert "const batchSize=4,batchStart=batchAttempt*batchSize;" in template\n    assert "tiles=tiles.slice(batchStart,batchStart+batchSize)" in template
    assert "Math.min(4,tiles.length)" in template
    assert "request===roadRequest&&count<180" in template
    assert "loadRoadNetwork(b,mode,batchAttempt+1,request)" in template
    assert "},6000):null;" not in template
    assert "if(recoveryTimer)clearTimeout(recoveryTimer);" not in template


def test_nearby_place_requests_cannot_restore_stale_results():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    assert "placeRequest=0,placeController=null" in template
    assert "const request=++placeRequest;" in template
    assert "if(placeController)placeController.abort();" in template
    assert "cache:'no-store',signal:placeController.signal" in template
    assert "if(request!==placeRequest)return;" in template
    assert "error?.name==='AbortError'||request!==placeRequest" in template
    assert "places.replaceChildren();" in template


def test_map_master_visibility_contract():
    css = Path("mission_control/static/oap_map_navigation.css").read_text(encoding="utf-8")
    assert "--route:#ffd85a" in css
    assert ".road-svg polyline.local{stroke:#4d5966;stroke-width:2.2;opacity:.9}" in css
    assert ".road-svg polyline.secondary{stroke:#758290;stroke-width:3.2;opacity:.96}" in css
    assert ".road-svg polyline.major{stroke:#a4afb9;stroke-width:4.4;opacity:1}" in css
    assert ".road-label{fill:#f1f4f7;stroke:#07090c;stroke-width:4px;" in css
    assert ".route-svg #route-casing{stroke:#090d12;stroke-width:16;opacity:.98}" in css
    assert ".route-svg #route-line{stroke:var(--route);stroke-width:9}" in css
    assert "body[data-map-mode=\"drive\"] .road-label{opacity:.78;font-size:12px}" in css
    assert ".map-float-btn{width:48px;height:48px" in css
    assert "outline:3px solid #ffd85a" in css
    assert "@media(max-width:700px){.road-svg polyline.local{stroke-width:2.5}" in css


def test_road_network_second_batch_uses_new_nearby_tiles():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    assert "const batchSize=4,batchStart=batchAttempt*batchSize;" in template
    assert "tiles=tiles.slice(batchStart,batchStart+batchSize);" in template
    assert "loadRoadNetwork(b,mode,batchAttempt+1,request)" in template
    assert "if(batchAttempt<1)" in template
