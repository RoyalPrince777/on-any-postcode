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


def test_spot_apps_entry_remains_available_after_world_startup(client):
    response = client.get("/the-spot")
    assert response.status_code == 200
    assert b'data-spot-apps-entry' in response.data
    assert b'href="/store"' in response.data


def test_koradaso_links_to_existing_store_and_spot_without_duplicate_install_claim(client):
    response = client.get("/koradaso")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'href="/store" data-koradaso-store-entry' in body
    assert 'href="/the-spot"' in body
    assert 'href="/the-spot/market"' in body
    assert 'href="/oap-store"' not in body
    assert "signed APK" not in body

    store = client.get("/store")
    assert store.status_code == 200
    assert "OAP Store" in store.get_data(as_text=True)


def test_my_world_uses_the_existing_public_browser_with_separate_permissions(
    anonymous_client,
):
    """One browser entry; no public rendering of the private Founder interface."""
    private_html = (ROOT / "templates" / "my_world.html").read_text(encoding="utf-8")
    assert 'aria-label="Public OAP destinations"' in private_html
    assert private_html.count('href="/koradaso"') == 1
    assert private_html.count('href="/world"') == 1
    assert 'href="/"' not in private_html.split('</header>', 1)[0]

    browser = anonymous_client.get("/koradaso")
    assert browser.status_code == 200
    assert browser.headers["Cache-Control"] == "no-store"
    page = browser.get_data(as_text=True)
    assert page.count('href="/my-world"') == 1
    assert "Enter My World" in page
    assert 'href="/store" data-koradaso-store-entry' in page
    assert "Founder identity" not in page
    assert "Leave My World" not in page
    assert "WWW Index results are not connected" in page
    assert 'window.confirm("OPEN WEB' in page

    founder = anonymous_client.get("/my-world")
    assert founder.status_code == 302
    assert "/enter-my-world?next=" in founder.headers["Location"]
    # The login gate returns a redirect, not the private Founder page.
    assert b"Founder identity" not in founder.data
    assert b"Leave My World" not in founder.data


def test_koradaso_royal_compass_restores_useful_public_extras_without_private_data(client):
    page = client.get("/koradaso").get_data(as_text=True)
    for marker in (
        'koradaso_internet_logo.jpg',
        'id="browser-settings"',
        'id="open-place-add"',
        'id="place-route"',
        'id="open-place-list"',
        'id="bookmark-add"',
        'id="bookmark-list"',
        'id="recent-place-list"',
        'id="quiet-appearance"',
        'id="reduce-motion"',
        'id="clear-browser-preferences"',
        'id="browser-back"',
        'aria-label="KORADASO destinations"',
        'href="/studio?source=koradaso"',
        'href="/arena"',
        'href="/library"',
        'href="/oap-map"',
        'href="/search"',
        'href="/the-spot"',
        'WWW Index — not connected',
        'allowedRoutes=new Set(',
        'if(window.confirm("OPEN WEB — "+url.hostname+" is outside OAP. Continue?"))',
    ):
        assert marker in page, marker
    assert page.count('href="/my-world"') == 1
    assert '"/my-world"' not in page.split("const allowedRoutes=new Set(", 1)[1].split(");", 1)[0]
    assert "addJavascriptInterface" not in page

    launch = client.get("/world?source=oap-os")
    assert launch.status_code == 200
    assert 'href="/koradaso"' in launch.get_data(as_text=True)
