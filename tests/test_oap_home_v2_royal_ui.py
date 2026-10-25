"""Founder royal Home V2 UI reference: local assets, real routes and truth states."""
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "templates" / "home_v2.html"
EARTH = ROOT / "static" / "oap" / "home_v2_royal_earth.svg"
SPRITES = ROOT / "static" / "oap" / "home_v2_royal_tiles.svg"
SVG = "{http://www.w3.org/2000/svg}"


def test_royal_art_is_locally_hosted_and_nine_symbols_parse():
    assert ET.parse(EARTH).getroot().tag == SVG + "svg"
    icon_root = ET.parse(SPRITES).getroot()
    symbols = {s.get("id") for s in icon_root.iter(SVG + "symbol")}
    assert symbols == {
        "world", "link", "sika", "maps", "mail",
        "market", "tv", "arena", "library",
    }
    html = HTML.read_text(encoding="utf-8")
    assert "/static/oap/home_v2_royal_earth.svg" in html
    for symbol in symbols:
        assert 'href="/static/oap/home_v2_royal_tiles.svg#' + symbol + '"' in html


def test_royal_reference_keeps_nine_route_backed_cards():
    html = HTML.read_text(encoding="utf-8")
    expected = (
        ("/world", "OAP WORLD"), ("/linkup", "LINK UP"),
        ("/pay/bank", "SIKA"), ("/oap-map", "OAP MAPS"),
        ("/mail", "OAP MAIL"), ("/market", "OAP MARKET"),
        ("/tv", "OAP TV"), ("/arena/connect4", "OAP ARENA"),
        ("/library", "OAP LIBRARY"),
    )
    for route, title in expected:
        assert 'href="' + route + '"' in html
        assert "<strong>" + title + "</strong>" in html
    assert 'aria-label="Personal quick-launch dock"' in html
    for name in ("Phone", "Messages", "Internet", "Camera", "All Apps"):
        assert "<span>" + name + "</span>" in html
    assert 'aria-label="OAP Home navigation"' in html
    assert 'href="/ptt"' in html
    assert 'href="/store"' in html


def test_royal_information_is_live_or_truthfully_unavailable(client):
    response = client.get("/home-v2")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Live local weather not connected" in html
    assert "Calendar not connected" in html
    assert 'data-timezone="Europe/London"' in html
    assert 'data-timezone="America/New_York"' in html
    assert 'data-timezone="Asia/Dubai"' in html
    assert 'data-timezone="Africa/Accra"' in html
    assert 'action="/search"' in html
    assert 'href="/mission/smi"' in html
    assert "Home V2 does not automatically start, stop or certify it" in html
    assert 'data-dialog="internet-dialog"' in html
    assert 'data-dialog="camera-dialog"' in html
    assert 'role="search"' in html
    assert "19:30" not in html
    assert "16°C" not in html
    assert 'aria-label="Separate OAP product identities"' in html


def test_royal_art_routes_served_as_static_assets(client):
    for path in (
        "/static/oap/home_v2_royal_earth.svg",
        "/static/oap/home_v2_royal_tiles.svg",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert b"<svg" in response.data
