"""Regression contract for installed OAP Internet launch routing.

This static contract does not prove Android startup or absence of a cached flash.
"""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def test_installed_app_opens_world_without_root_redirect():
    manifest = json.loads((ROOT / "static" / "manifest.webmanifest").read_text(encoding="utf-8"))
    start = urlsplit(manifest["start_url"])
    assert start.path == "/world"
    assert parse_qs(start.query).get("source") == ["oap-os"]
    assert manifest["scope"] == "/"
    assert manifest["id"] == "/"


def test_installed_app_does_not_start_in_market():
    manifest = json.loads((ROOT / "static" / "manifest.webmanifest").read_text(encoding="utf-8"))
    start = urlsplit(manifest["start_url"])
    assert "market" not in start.path.lower()
    assert start.path != "/"


def test_installed_launch_serves_world_front_door(client):
    response = client.get("/world?source=oap-os")
    assert response.status_code == 200
    assert b"<title>OAP World</title>" in response.data
    assert b"One World. One Front Door." in response.data


def test_normal_world_route_remains_available(client):
    response = client.get("/world")
    assert response.status_code == 200
