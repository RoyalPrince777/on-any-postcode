"""Focused KORADASO search contract; not browser/device acceptance proof."""
from pathlib import Path

SOURCE = Path("templates/koradaso_internet.html")


def test_koradaso_omnibox_routes_queries_to_existing_oap_search(client):
    page = client.get("/koradaso")
    assert page.status_code == 200
    source = SOURCE.read_text(encoding="utf-8")
    assert 'window.location.assign("/search?q="+encodeURIComponent(raw))' in source
    assert 'const explicitScheme=' in source
    assert 'const hostLike=' in source
    assert 'raw.length>120' in source
    assert 'allowedRoutes.has(firstParty.pathname)' in source
    assert 'firstParty.origin===window.location.origin' in source
    assert 'raw.startsWith("/")&&!raw.startsWith("//")' in source
    assert client.get("/search?q=KORADASO%20Internet").status_code == 200


def test_external_search_is_opt_in_and_site_navigation_preserves_consent():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'id="open-web-search"' in source
    assert 'if(currentSearchMode()==="web")' in source
    assert 'window.confirm("OPEN WEB SEARCH' in source
    assert 'encodeURIComponent(raw)' in source
    assert 'url.protocol!=="https:"' in source
    assert 'url.username||url.password' in source
    assert 'window.confirm("OPEN WEB — "+url.hostname' in source


def test_unready_oap_tiles_do_not_navigate_and_settings_are_functional():
    source = SOURCE.read_text(encoding="utf-8")
    for route in ('/maps', '/the-link', '/the-spot/market', '/studio', '/library'):
        assert f'href="{route}"' not in source
    assert 'class="tile is-reserved"' in source
    assert 'aria-disabled="true"' in source
    assert 'href="/world?source=oap-os"' in source
    assert 'href="/search"' in source
    assert 'name="search-mode" value="web"' in source
    assert 'id="clear-browser-preferences"' in source
    assert 'localStorage.removeItem(bookmarkKey)' in source
    assert 'localStorage.removeItem(preferencesKey)' in source


def test_royal_home_keeps_search_and_navigation_functional(client):
    page = client.get("/koradaso")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert 'class="royal-tabs"' in body
    assert 'href="/search"' in body
    assert 'href="#bookmark-list"' in body
    assert 'href="#browser-settings"' in body
    assert 'id="address-form"' in body
    assert 'id="trust-state"' in body


def test_termux_runner_preserves_existing_server_and_routes():
    source = Path("scripts/koradaso_termux_local.sh").read_text(encoding="utf-8")
    assert 'OAP_KORADASO_PORT:-5052' in source
    assert 'required = {"/koradaso", "/world", "/search"}' in source
    assert 'sock.bind(("127.0.0.1", port))' in source
    assert 'port {port} is already occupied; existing server untouched.' in source
    assert '--host 127.0.0.1' in source
    assert 'OAP_SURFACE_ROLE:-' in source
    assert "reset --hard" not in source


def test_termux_auto_opens_only_after_real_branded_http_response():
    source = Path("scripts/koradaso_termux_local.sh").read_text(encoding="utf-8")
    assert 'OAP_KORADASO_OPEN_BROWSER:-1' in source
    assert 'curl --noproxy' in source
    assert '/koradaso" 2>/dev/null || true)' in source
    assert 'KORADASO Internet · ON ANY POSTCODE' in source
    assert 'id="address-form"' in source
    assert 'termux-open-url "http://127.0.0.1:$PORT/koradaso"' in source
    assert 'live branded /koradaso page not verified.' in source



def test_koradaso_startup_does_not_require_optional_map_tile_decoder():
    source = Path("mission_control/road_tile_geometry.py").read_text(encoding="utf-8")
    assert "\nimport mapbox_vector_tile\n" not in source
    assert '    try:\n        # The optional vector decoder' in source
    assert '        import mapbox_vector_tile' in source
    assert 'raise routing.RoutingUnavailable("road_tile_decode_failed")' in source


def test_koradaso_oap_world_opens_menu_not_marketplace(client):
    menu = client.get("/world?source=oap-os")
    assert menu.status_code == 200
    assert "One World. One Front Door." in menu.get_data(as_text=True)
    source = SOURCE.read_text(encoding="utf-8")
    assert 'href="/world?source=oap-os"' in source
    assert 'href="/"\u00a0' not in source
