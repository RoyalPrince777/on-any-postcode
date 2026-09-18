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


def test_mobile_map_canvas_is_above_controls():
    template = Path(
        "mission_control/templates/local_map.html"
    ).read_text(encoding="utf-8")

    assert ".map-wrap{order:1;min-height:64vh" in template
    assert ".side{order:2;" in template
    assert 'class="map-wrap"' in template
    assert 'id="route-svg"' in template
    assert "Greater London · first-party routing" in template


def test_public_map_door_uses_visible_first_party_renderer():
    source = Path(
        "mission_control/on_any_place_routes.py"
    ).read_text(encoding="utf-8")

    assert '@bp.get("/on-any-place")' in source
    assert 'render_template("local_map.html", local_map=local_map)' in source
    assert "'/map-intelligence/road-geometry/" in Path(
        "mission_control/templates/local_map.html"
    ).read_text(encoding="utf-8")
