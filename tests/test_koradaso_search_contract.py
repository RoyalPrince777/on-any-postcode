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
    assert 'href="/world"' in source
    assert 'href="/search"' in source
    assert 'name="search-mode" value="web"' in source
    assert 'id="clear-browser-preferences"' in source
    assert 'localStorage.removeItem(bookmarkKey)' in source
    assert 'localStorage.removeItem(preferencesKey)' in source
