"""Home V2 navigation must not change the existing OAP World front door."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "templates" / "home_v2.html"
WORLD = ROOT / "templates" / "world.html"


def test_home_v2_keeps_one_tap_destinations():
    html = HOME.read_text(encoding="utf-8")
    for route in ("/store", "/ptt", "/world", "/the-link"):
        assert f'href="{route}"' in html
    assert 'aria-label="OAP Home navigation"' in html
    assert "env(safe-area-inset-bottom)" in html
    assert "focus-visible" in html


def test_home_v2_does_not_claim_unverified_device_capabilities():
    html = HOME.read_text(encoding="utf-8")
    assert "separately verified Android integration" in html
    assert "No live weather or calendar data is claimed" in html


def test_world_keeps_store_outside_its_reference_ui():
    html = WORLD.read_text(encoding="utf-8")
    assert "OAP Store" not in html


def test_home_v2_route_serves_existing_template(client):
    response = client.get("/home-v2")
    assert response.status_code == 200
    assert b"OAP HOME" in response.data
    assert b'OAP Home navigation' in response.data
