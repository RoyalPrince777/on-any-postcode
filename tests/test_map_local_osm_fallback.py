"""Bounded tests for real OSM import reuse and no-fake-live map controls."""
from __future__ import annotations

import json

import pytest

from mission_control import local_osm_roads

_PREFIX = "window.TDA_MITCHAM_OSM = "


def _write(path, data):
    path.write_text(_PREFIX + json.dumps(data) + ";", encoding="utf-8")


def test_first_party_local_mitcham_road_geometry_accepts_import_shapes(
    monkeypatch, tmp_path
):
    source = tmp_path / "map_data.js"
    _write(source, {
        "source": "OpenStreetMap via Overpass", "extractedAt": "2026-11-22T13:59:00Z",
        "features": [
            {"kind": "road", "name": "Road A", "highway": "residential",
             "geometry": [[-0.17, 51.403], [-0.16, 51.409]]},
            {"kind": "road", "name": "Road B", "points": [
                {"lat": 51.404, "lon": -0.18}, {"lat": 51.411, "lon": -0.173},
            ]},
            {"kind": "road", "name": "Road C", "coordinates": [
                [51.404, -0.19], [51.407, -0.185],
            ]},
            {"kind": "building", "geometry": [[-0.17, 51.4], [-0.16, 51.41]]},
            {"kind": "road", "geometry": [[0, 0], [1, 1]]},
        ],
    })
    monkeypatch.setattr(local_osm_roads, "_SOURCE_PATH", source)
    data = local_osm_roads.road_lines(
        west=-0.235, south=51.37, east=-0.13, north=51.43
    )
    assert data["road_count"] == 3
    assert data["source"] == "existing_tda_osm_import"
    assert data["routing_verified"] is False
    assert data["live_traffic_verified"] is False
    assert data["coverage"] == "central_mitcham_only"
    assert all(
        -0.235 <= point[0] <= -0.13
        for road in data["lines"] for point in road["points"]
    )


def test_no_source_and_unsupported_import_never_create_fake_roads(monkeypatch, tmp_path):
    path = tmp_path / "missing.js"
    monkeypatch.setattr(local_osm_roads, "_SOURCE_PATH", path)
    with pytest.raises(local_osm_roads.LocalRoadsUnavailable):
        local_osm_roads.road_lines(
            west=-0.235, south=51.37, east=-0.13, north=51.43
        )
    _write(path, {"source": "unknown", "features": [
        {"kind": "road", "geometry": [[-0.17, 51.4], [-0.16, 51.41]]},
    ]})
    with pytest.raises(local_osm_roads.LocalRoadsUnavailable):
        local_osm_roads.road_lines(
            west=-0.235, south=51.37, east=-0.13, north=51.43
        )


def test_mitcham_fallback_route_returns_real_source_only(client, monkeypatch, tmp_path):
    path = tmp_path / "map_data.js"
    monkeypatch.setattr(local_osm_roads, "_SOURCE_PATH", path)
    url = "/map-intelligence/local-roads?west=-0.235&south=51.37&east=-0.13&north=51.43"
    unavailable = client.get(url)
    assert unavailable.status_code == 503
    assert unavailable.get_json()["routing_verified"] is False
    _write(path, {"source": "OpenStreetMap contributors", "features": [
        {"kind": "road", "name": "Local lane",
         "geometry": [[-0.17, 51.403], [-0.16, 51.409]]},
    ]})
    ready = client.get(url)
    assert ready.status_code == 200
    assert ready.get_json()["road_count"] == 1
    assert ready.headers["X-OAP-Map-Source"] == "existing-local-osm-import"
    assert ready.headers["Cache-Control"] == "private, no-store"
    assert client.get("/map-intelligence/local-roads?west=-10").status_code == 400


def test_car_browser_keeps_hazards_and_gps_consent_evidence(client):
    from pathlib import Path

    html = client.get("/oap-map?view=car").get_data(as_text=True)
    assert 'id="oap-car-gps"' in html
    assert 'id="oap-hazard-list"' in html
    assert "No verified alert information for this route" in html
    nav = Path("mission_control/static/oap_map_navigation.js").read_text(
        encoding="utf-8"
    )
    assert "window.isSecureContext" in nav
    assert "carGps?.addEventListener('click',startLocation)" in nav
    assert "renderHazards(currentRoute.live_pattern_reports)" in nav
    assert "Community report · unverified" in nav
    assert "TfL source report" in nav
    assert "source==='existing_tda_osm_import'" not in nav
    local_map = Path("mission_control/templates/local_map.html").read_text(
        encoding="utf-8"
    )
    assert "loadLocalOsmRoads(b,request)" in local_map
    assert "data.source!=='existing_tda_osm_import'" in local_map
    assert "Mitcham OSM roads · navigation graph unavailable" in local_map
