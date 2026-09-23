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

    assert "loadRoadNetwork(defaultBounds,profile.value);" in template
    assert "if(from.value.trim()&&to.value.trim())route();" in template
    assert template.index("loadRoadNetwork(defaultBounds,profile.value);") < template.index(
        "if(from.value.trim()&&to.value.trim())route();"
    )
    assert 'id="road-source-state"' in template
    assert "showRoadStatus(count?'': 'Road network unavailable" in template


def test_route_failure_preserves_independent_road_layer():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    route_section = template.split("async function route(){", 1)[1].split(
        "form.addEventListener('submit'", 1
    )[0]

    assert "roadLayer.innerHTML=''" not in route_section
    assert "if(request!==roadRequest)return;" in template
    assert "if(request===roadRequest)" in template
    assert "profile.addEventListener('change'" in template


def test_oap_os_generation_zero_map_binding_is_truthful_and_consent_safe():
    template = Path("mission_control/templates/local_map.html").read_text(encoding="utf-8")
    bridge = Path("mission_control/static/oap_os_map_bridge.js").read_text(encoding="utf-8")
    documentation = Path("docs/OAP_OPERATING_SYSTEM_V0.md").read_text(encoding="utf-8")

    assert 'id="oap-os-map-runtime"' in template
    assert "oap_os_map_bridge.js" in template
    assert "android-web" in bridge
    assert "installed web shell" in bridge
    assert "unverified" in bridge
    assert "MutationObserver" in bridge
    assert "geolocation." not in bridge
    assert "serviceWorker.register" not in bridge
    assert "Android/Linux host kernel" in documentation
