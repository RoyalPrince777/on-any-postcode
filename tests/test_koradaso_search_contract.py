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
    assert 'window.location.assign("/koradaso/web-search?q="+encodeURIComponent(raw))' in source
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
    assert '<a href="/world?source=oap-os">🌍 World</a>' in source



def test_oap_world_menu_keeps_marketplace_as_a_destination(client):
    menu = client.get("/world?source=oap-os")
    marketplace = client.get("/world")
    assert menu.status_code == marketplace.status_code == 200
    menu_html = menu.get_data(as_text=True)
    market_html = marketplace.get_data(as_text=True)
    assert '<strong>🛍️ Marketplace</strong>' in menu_html
    assert 'href="/world"' in menu_html
    assert "One World. One Front Door." in menu_html
    assert "YOUR LOCAL" in market_html
    assert "MARKETPLACE." in market_html


def test_koradaso_shortcuts_keep_ready_world_market_search_and_settings(client):
    page = client.get("/koradaso")
    assert page.status_code == 200
    source = SOURCE.read_text(encoding="utf-8")
    assert '<a class="tile" href="/world"><span class="ico"' in source
    assert '<strong>Market</strong><span>OAP Marketplace</span>' in source
    assert 'href="/world?source=oap-os"' in source
    assert 'href="/search"' in source
    assert 'href="#browser-settings"' in source
    for label in ("Maps", "Mail"):
        assert f"<strong>{label}</strong><span>Reserved · Not ready</span>" in source
    assert client.get("/world").status_code == 200
    assert client.get("/world?source=oap-os").status_code == 200


def test_koradaso_original_logo_and_core_boundary(client):
    source = SOURCE.read_text(encoding="utf-8")
    response = client.get("/koradaso")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    logo_path = "/static/oap/koradaso_internet_logo.jpg"
    assert f'<img src="{logo_path}"' in html
    logo = client.get(logo_path)
    assert logo.status_code == 200
    assert logo.mimetype == "image/jpeg"
    assert 'class="smi-entry"' not in html
    for prefix in ("/auth", "/mission", "/smi"):
        assert f'href="{prefix}' not in html
    assert 'action="/search" method="get"' in html
    assert 'id="address" name="q"' in html
    assert 'href="/arena"' in html
    assert '<strong>Arena</strong>' in html
    assert 'id="bookmark-list"' in html
    assert 'id="settings-tile" href="#browser-settings"' in html
    assert 'class="royal-menu"' in html
    assert '<a href="#browser-settings">⚙ Settings &amp; Privacy</a>' in source
    assert '<span class="menu-unavailable" aria-disabled="true">⬇ Downloads · Not ready</span>' in source
    assert "<strong>Downloads</strong><span>Reserved · Not ready</span>" in source
    assert 'id="browser-settings"' in source
    assert 'id="address-form"' in source
    assert client.get("/arena").status_code in (200, 302)
    assert "https://duckduckgo.com" not in source


def test_koradaso_arena_and_discovery_tabs_are_truthful(client):
    html = client.get("/koradaso").get_data(as_text=True)
    assert 'class="tile arena-tile" href="/arena"' in html
    assert "Play OAP games · Challenge hub" in html
    assert 'class="discovery-strip"' in html
    assert '<a href="/search">All OAP</a>' in html
    assert '<a href="/koradaso/web-search">WWW Index</a>' in html
    assert "Images · Soon" in html
    assert "Videos · Soon" in html
    assert 'title="Image indexing not yet available"' in html
    assert 'title="Video indexing not yet available"' in html

    arena = client.get("/arena")
    assert arena.status_code == 200
    arena_html = arena.get_data(as_text=True)
    assert 'OAP <span class="arena-gold">ARENA</span>' in arena_html
    for route in ("/arena/connect4/room", "/arena/chess/room",
                  "/arena/oware/room", "/arena/ludo/room"):
        assert f'href="{route}"' in arena_html


def test_koradaso_mobile_layout_keeps_omnibox_and_controls_accessible():
    source = SOURCE.read_text(encoding="utf-8")
    assert "Redmi A5 responsive polish" in source
    assert "@media(max-width:520px)" in source
    assert ".search input{min-width:0;width:0;flex:1 1 0;" in source
    assert ".search button{flex:0 0 auto;min-height:46px;" in source
    assert ".royal-tab{min-height:42px;" in source
    assert 'id="address-form"' in source
    assert 'name="search-mode" value="oap"' in source
    assert 'name="search-mode" value="web"' in source
    assert 'href="/world?source=oap-os"' in source


def test_koradaso_uses_only_first_party_www_search(client, monkeypatch):
    monkeypatch.delenv("OAP_KORADASO_WEB_INDEX", raising=False)
    source = SOURCE.read_text(encoding="utf-8")
    assert "DuckDuckGo" not in source
    assert "duckduckgo.com" not in source
    assert 'window.location.assign("/koradaso/web-search?q="+encodeURIComponent(raw))' in source
    missing = client.get("/koradaso/web-search?q=test")
    assert missing.status_code == 503
    assert b"First-party index not configured" in missing.data


def test_koradaso_sqlite_index_real_results_without_external_provider(tmp_path, monkeypatch, client):
    from mission_control import koradaso_web_index

    db_path = tmp_path / "public_index.sqlite3"
    monkeypatch.setenv("OAP_KORADASO_WEB_INDEX", str(db_path))
    koradaso_web_index.ingest_public_page(
        db_path, url="https://example.org/announcements",
        title="Community announcements",
        description="Public events and activities",
    )
    response = client.get("/koradaso/web-search?q=community")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Community announcements" in html
    assert "https://example.org/announcements" in html
    assert "DuckDuckGo" not in html
    assert client.get("/koradaso/web-search?q=unmatched").status_code == 200


def test_koradaso_index_rejects_unsafe_public_urls(tmp_path):
    import pytest

    from mission_control.koradaso_web_index import ingest_public_page

    for url in ("http://example.com", "https://127.0.0.1/",
                "https://localhost/", "https://user:secret@example.org",
                "javascript://example.com"):
        with pytest.raises(ValueError, match="invalid_public_page_metadata"):
            ingest_public_page(tmp_path / "index.db", url=url, title="Unsafe")


def test_koradaso_curated_import_creates_real_local_index(tmp_path, monkeypatch, client):
    import json
    import subprocess
    import sys

    source_file = tmp_path / "reviewed.jsonl"
    source_file.write_text(json.dumps({
        "url": "https://example.org/public",
        "title": "Public historical directory",
        "description": "Independent archives",
    }) + "\n", encoding="utf-8")
    db = tmp_path / "koradaso.sqlite3"
    result = subprocess.run(
        [sys.executable, "scripts/koradaso_index_public.py",
         "--source", str(source_file), "--db", str(db)],
        capture_output=True, text=True, check=False, timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    monkeypatch.setenv("OAP_KORADASO_WEB_INDEX", str(db))
    response = client.get("/koradaso/web-search?q=historical")
    assert response.status_code == 200
    assert b"Public historical directory" in response.data


def test_koradaso_www_ranks_title_relevance_before_newer_description(tmp_path, monkeypatch):
    from mission_control.koradaso_web_index import (
        ingest_public_page,
        search_public_pages,
    )

    db = tmp_path / "ranking.sqlite3"
    monkeypatch.setenv("OAP_KORADASO_WEB_INDEX", str(db))
    ingest_public_page(
        db,
        url="https://example.org/oware-guide",
        title="Oware strategy guide",
        description="Board game rules",
    )
    ingest_public_page(
        db,
        url="https://example.org/community-list",
        title="Community bulletin",
        description="Meetup about Oware strategy",
    )
    results, ready = search_public_pages("oware strategy")
    assert ready is True
    assert [item["url"] for item in results] == [
        "https://example.org/oware-guide",
        "https://example.org/community-list",
    ]
    # Reserved SQL wildcard characters remain literal search terms.
    assert search_public_pages("%_")[0] == []
