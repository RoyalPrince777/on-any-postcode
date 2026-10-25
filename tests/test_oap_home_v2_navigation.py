"""Home V2 navigation must not change the existing OAP World front door."""
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "templates" / "home_v2.html"
WORLD = ROOT / "templates" / "world.html"


def test_home_v2_keeps_one_tap_destinations():
    html = HOME.read_text(encoding="utf-8")
    for route in ("/store", "/ptt", "/world", "/the-spot", "/the-link"):
        assert f'href="{route}"' in html
    assert 'aria-label="OAP Home navigation"' in html
    assert "env(safe-area-inset-bottom)" in html
    assert "focus-visible" in html


def test_home_v2_does_not_claim_unverified_device_capabilities():
    html = HOME.read_text(encoding="utf-8")
    assert "separately verified Android integration" in html
    assert "No live weather or calendar data is claimed" in html
    assert "Your postcode community inside OAP World" in html
    assert "Browse OAP apps" in html
    assert "Install OAP apps" not in html


def test_world_keeps_store_outside_its_reference_ui():
    html = WORLD.read_text(encoding="utf-8")
    assert "OAP Store" not in html


def test_home_v2_route_serves_existing_template(client):
    response = client.get("/home-v2")
    assert response.status_code == 200
    assert b"OAP HOME" in response.data
    assert b'OAP Home navigation' in response.data


def test_home_v2_search_is_large_accessible_and_uses_existing_public_search():
    html = HOME.read_text(encoding="utf-8")
    assert '<form class="home-search" role="search" method="get" action="/search">' in html
    assert '<label class="visually-hidden" for="home-search-query">' in html
    assert 'id="home-search-query" type="search" name="q" maxlength="120"' in html
    assert "min-height:64px" in html
    assert "Private messages and Founder tools are not searched." in html
    assert 'aria-label="Explore from search"' in html
    for destination in (
        "/arena/connect4",
        "/search?q=market",
        "/search?q=library",
        "/search?q=music",
        "/store",
    ):
        assert f'href="{destination}"' in html


def test_home_v2_search_finds_connect4_and_can_return_to_home(client):
    home = client.get("/home-v2")
    assert home.status_code == 200
    assert b'role="search"' in home.data
    results = client.get("/search?q=connect+4")
    assert results.status_code == 200
    body = results.get_data(as_text=True)
    assert "OAP Connect 4" in body
    assert 'href="/arena/connect4"' in body
    assert 'href="/home-v2"' in body
    assert 'href="/store"' in body
    assert "public OAP app catalogue only" in body


def test_home_v2_keeps_personal_name_distinct_from_internet_and_home_node(client):
    html = HOME.read_text(encoding="utf-8")
    assert "<title>OAP Home V2 · Personal Dashboard</title>" in html
    assert "<h1>♛ OAP HOME V2</h1>" in html
    assert 'aria-label="Separate OAP product identities"' in html
    assert "OAP Internet</strong> is a separate Android browser application" in html
    assert "OAP Home Node</strong> is the separate local SMI worker runtime" in html
    assert "Home V2 does not automatically start, stop or certify it" in html
    response = client.get("/home-v2")
    assert response.status_code == 200
    assert b"OAP HOME V2" in response.data
    assert b"OAP Internet" in response.data


def test_native_oap_internet_label_keeps_distinct_app_identity():
    """A label change must not change the existing native app package or Home Node."""
    manifest = ROOT / "android" / "oapworld" / "src" / "main" / "AndroidManifest.xml"
    root = ElementTree.parse(manifest).getroot()
    application = root.find("application")
    assert application is not None
    assert application.get("{http://schemas.android.com/apk/res/android}label") == "OAP Internet"
    build = (ROOT / "android" / "oapworld" / "build.gradle").read_text(encoding="utf-8")
    assert "applicationId 'com.onanypostcode.oapworld'" in build
    assert (ROOT / "scripts" / "oap_home_node_supervisor.py").is_file()
