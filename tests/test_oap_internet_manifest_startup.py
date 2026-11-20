"""Regression contract for installed OAP Internet launch routing.

This static contract does not prove Android startup or absence of a cached flash.
"""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def test_installed_app_opens_koradaso_home_without_root_redirect():
    manifest = json.loads((ROOT / "static" / "manifest.webmanifest").read_text(encoding="utf-8"))
    start = urlsplit(manifest["start_url"])
    assert start.path == "/koradaso"
    assert parse_qs(start.query).get("source") == ["oap-os"]
    assert manifest["scope"] == "/"
    assert manifest["id"] == "/"


def test_installed_app_does_not_start_in_market():
    manifest = json.loads((ROOT / "static" / "manifest.webmanifest").read_text(encoding="utf-8"))
    start = urlsplit(manifest["start_url"])
    assert "market" not in start.path.lower()
    assert start.path != "/"


def test_installed_launch_serves_koradaso_browser_home(client):
    response = client.get("/koradaso?source=oap-os")
    assert response.status_code == 200
    assert b"KORADASO Internet" in response.data
    assert b'aria-label="KORADASO destinations"' in response.data
    assert b'href="/world?source=oap-os"' in response.data

def test_world_remains_accessible_from_browser_home(client):
    response = client.get("/world?source=oap-os")
    assert response.status_code == 200
    assert b"<title>OAP World</title>" in response.data
    assert b"Places, people and services across OAP." in response.data


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
        'WWW Index results are not connected',
        'allowedRoutes=new Set(',
        'if(window.confirm("OPEN WEB — "+url.hostname+" is outside OAP. Continue?"))',
    ):
        assert marker in page, marker
    assert page.count('href="/my-world"') == 1
    assert '"/my-world"' not in page.split("const allowedRoutes=new Set(", 1)[1].split(");", 1)[0]
    assert "addJavascriptInterface" not in page
    assert 'readList(sessionStorage,recentKey,12)' in page
    assert 'renderList("recent-place-list",sessionStorage,recentKey,12)' in page

    launch = client.get("/world?source=oap-os")
    assert launch.status_code == 200
    assert 'href="/koradaso"' in launch.get_data(as_text=True)
    assert 'href="/store" data-oap-world-apps' in launch.get_data(as_text=True)
    assert 'href="/search" data-oap-world-search' in launch.get_data(as_text=True)

def test_public_browser_back_fallback_stays_on_koradaso_home(client):
    page = client.get("/koradaso").get_data(as_text=True)
    assert 'note.textContent="KORADASO is home.' in page
    assert 'location.assign("/world?source=oap-os");' not in page


def test_public_oap_world_commerce_route_also_exposes_koradaso_browse_and_apps(client):
    """The public /world route is a different template from /world?source=oap-os."""
    world = client.get("/world")
    assert world.status_code == 200
    html = world.get_data(as_text=True)
    assert 'aria-label="Browse and Apps across OAP World"' in html
    assert html.count('href="/koradaso"') == 1
    assert 'href="/store" data-oap-world-apps' in html
    assert 'href="/search" data-oap-world-search' in html
    assert 'href="/enter-my-world?next=/"' in html
    assert 'href="/mission/smi"' not in html

    shell = client.get("/world?source=oap-os")
    assert shell.status_code == 200
    assert 'aria-label="Browse and Apps across OAP World"' in shell.get_data(as_text=True)

def test_world_browse_and_apps_share_one_layout_and_primary_navigation(client):
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    shared = (root / "static/oap-browse-apps.css").read_text(encoding="utf-8")
    assert ".oap-browse-apps" in shared
    assert "@media(max-width:560px)" in shared

    for route in ("/world", "/world?source=oap-os"):
        response = client.get(route)
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert 'class="oap-browse-apps"' in html
        assert html.count('data-oap-browse-koradaso') == 1
        assert html.count('data-oap-world-apps') == 1
        assert html.count('data-oap-world-search') == 1
        assert '/static/oap-browse-apps.css' in html
        assert html.count('href="/koradaso"') == 1
        assert 'href="/mission/smi"' not in html

    shop = client.get("/world").get_data(as_text=True)
    assert shop.index('data-oap-browse-koradaso') < shop.index('class="counter"')
    shell = client.get("/world?source=oap-os").get_data(as_text=True)
    assert 'class="world-web-extra"' in shell
    assert 'id="world-search"' in shell  # Old web action remains on demand.


def test_store_search_and_koradaso_keep_accessible_nav_and_compact_extras(client):
    store = client.get("/store").get_data(as_text=True)
    assert 'aria-label="OAP Store navigation"' in store
    assert 'href="/koradaso"' in store
    assert 'class="app-info"' in store
    assert store.count('<summary>Access details</summary>') > 0
    assert 'data-oap-koradaso-integrated' in store
    assert "Install KORADASO Internet" not in store

    search = client.get("/search?q=koradaso").get_data(as_text=True)
    assert 'aria-label="OAP Search navigation"' in search
    assert 'href="/koradaso"' in search
    assert 'href="/store"' in search
    assert "KORADASO Internet" in search

    page = client.get("/koradaso").get_data(as_text=True)
    assert page.count("WWW Index results are not connected") == 1
    assert 'aria-label="KORADASO destinations"' in page
    assert 'href="/my-world"' in page
    assert "No offline private-data access." not in page
    assert 'window.confirm("OPEN WEB — "+url.hostname+' in page

