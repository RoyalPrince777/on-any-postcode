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
    catalogue = client.get("/search?q=music")
    assert catalogue.status_code == 200
    assert "OAP Music" in catalogue.get_data(as_text=True)
    assert 'href="/koradaso/web-search?q=music"' in catalogue.get_data(as_text=True)


def test_koradaso_intelligence_automatic_public_shell_updates_without_private_data(client):
    """Browser updater checks public worker and never overwrites active conversations."""
    response = client.get("/studio?source=koradaso")
    assert response.status_code == 200
    source = Path("templates/studio_public.html").read_text(encoding="utf-8")
    homepage = SOURCE.read_text(encoding="utf-8")
    updater = Path("static/koradaso_auto_update.js").read_text(encoding="utf-8")
    assert '<script src="/static/koradaso_auto_update.js" defer></script>' in homepage
    assert '{% if koradaso_mode %}<script src="/static/koradaso_auto_update.js" defer></script>{% endif %}' in source
    assert 'id="smi-update"' not in source
    assert 'navigator.serviceWorker.register("/service-worker.js", {scope: "/"})' in updater
    assert 'registration.update()' in updater
    assert '"online", check' in updater
    assert '"visibilitychange", check' in updater
    assert 'window.setInterval(check, periodMs)' in updater
    assert 'messages.children.length' in updater
    assert 'window.location.reload()' in updater
    assert 'refreshing || !isIdle()' in updater
    assert 'href="/studio?source=koradaso"' in homepage


def test_koradaso_public_offline_shell_reuses_oap_worker_without_private_caching(client):
    """Source contract only; does not certify disconnected-host or virtual AOSP boot."""
    page = client.get("/koradaso")
    worker_response = client.get("/service-worker.js")
    assert page.status_code == worker_response.status_code == 200
    source = SOURCE.read_text(encoding="utf-8")
    worker = Path("static/oap-os-sw.js").read_text(encoding="utf-8")
    assert '<script src="/static/koradaso_auto_update.js" defer></script>' in source
    assert 'navigator.serviceWorker.register("/service-worker.js", {scope: "/"})' in Path(
        "static/koradaso_auto_update.js"
    ).read_text(encoding="utf-8")
    assert '"/koradaso",' in worker
    assert '"/static/oap/koradaso_internet_logo.jpg",' in worker
    assert 'url.pathname === "/koradaso"' in worker
    assert 'caches.match("/koradaso")' in worker
    assert 'caches.match("/offline")' in worker
    assert 'if (isPrivatePath(url.pathname)) return;' in worker
    assert 'request.method !== "GET" || url.origin !== self.location.origin' in worker
    assert '"/my-world"' in worker
    assert '"/auth"' in worker
    assert '"/mission"' in worker


def test_koradaso_offline_worker_executes_public_fallback_without_private_interception():
    """Execute the actual worker in Node: no browser/device or AOSP acceptance claim."""
    import subprocess

    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const handlers = {};
const cached = new Map();
const cache = {
  addAll: async (paths) => {
    paths.forEach(path => cached.set(path, {source: "cache", path}));
  }
};
const caches = {
  open: async () => cache,
  match: async path => cached.get(path),
  keys: async () => [],
  delete: async () => true
};
const self = {
  location: {origin: "https://onanypostcode.global"},
  addEventListener: (name, fn) => {handlers[name] = fn;},
  skipWaiting: async () => {},
  clients: {claim: async () => {}}
};
let offline = true;
let networkCalls = 0;
const fetch = async request => {
  networkCalls++;
  if (offline) throw Error("upstream_unavailable");
  return {source: "network", path: new URL(request.url).pathname};
};
const worker = fs.readFileSync(process.argv[1], "utf8");
vm.runInNewContext(worker, {self, caches, fetch, URL, Promise}, {timeout: 1500});
async function dispatch(url, method = "GET", mode = "navigate") {
  let response;
  const event = {
    request: {url, method, mode},
    respondWith: value => {response = value;}
  };
  handlers.fetch(event);
  return response ? await response : undefined;
}
(async () => {
  let installation;
  handlers.install({waitUntil: value => {installation = value;}});
  await installation;
  assert.equal(cached.has("/koradaso"), true);
  assert.equal(cached.has("/static/oap/koradaso_internet_logo.jpg"), true);
  assert.equal(cached.has("/linkup"), false);
  assert.equal(cached.has("/my-world"), false);
  assert.equal((await dispatch("https://onanypostcode.global/koradaso")).path, "/koradaso");
  assert.equal((await dispatch("https://onanypostcode.global/koradaso")).source, "cache");
  assert.equal((await dispatch("https://onanypostcode.global/linkup")).path, "/offline");
  assert.equal(await dispatch("https://onanypostcode.global/my-world"), undefined);
  assert.equal(await dispatch("https://other.example/koradaso"), undefined);
  assert.equal(await dispatch("https://onanypostcode.global/koradaso", "POST"), undefined);
  offline = false;
  assert.equal((await dispatch("https://onanypostcode.global/koradaso")).source, "network");
  assert.equal(networkCalls, 4);
})().catch(error => {console.error(error);process.exitCode = 1;});
"""
    result = subprocess.run(
        ["node", "-e", script, "static/oap-os-sw.js"],
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_koradaso_traffic_boundary_keeps_open_web_access_without_page_leak(client):
    """First-party response hardening, not device-wide network isolation proof."""
    response = client.get("/koradaso")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "geolocation=()" in response.headers["Permissions-Policy"]
    assert "camera=()" in response.headers["Permissions-Policy"]
    source = SOURCE.read_text(encoding="utf-8")
    assert '<meta name="referrer" content="no-referrer">' in source
    assert 'window.location.assign(url.href)' in source
    assert 'window.confirm("OPEN WEB — "+url.hostname' in source
    assert 'window.location.assign("/koradaso/web-search?q="+encodeURIComponent(raw))' in source


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
    for route in ('/maps', '/the-link', '/the-spot/market', '/library'):
        assert f'href="{route}"' not in source
    assert 'class="tile is-reserved"' not in source
    assert '<strong>Maps</strong>' not in source
    assert '<strong>Mail</strong>' not in source
    assert 'href="/world?source=oap-os"' in source
    assert 'href="/search"' in source
    assert 'name="search-mode"' not in source
    assert 'id="clear-browser-preferences"' in source
    assert 'localStorage.removeItem(bookmarkKey)' in source
    assert 'localStorage.removeItem(preferencesKey)' in source


def test_right_drawer_and_search_feedback_have_real_controls(client):
    """Visible error feedback and accessible menu; not mobile-device proof."""
    html = client.get("/koradaso").get_data(as_text=True)
    header = html.split('<header class="top">', 1)[1].split("</header>", 1)[0]
    assert 'id="drawer-close" aria-label="Close browser menu"' in header
    assert 'id="drawer-bookmarks"' in header
    assert 'id="settings-downloads"' in header
    assert 'id="settings-privacy"' in header
    assert 'id="address-note" role="status" aria-live="polite"' in html
    assert 'class="note address-feedback"' in html
    assert '.address-feedback:empty{display:none}' in html
    assert 'height:100dvh' in html
    assert 'document.getElementById("drawer-close").addEventListener("click"' in html
    assert '<strong>Downloads</strong>' not in html
    assert '<strong>Settings</strong>' not in html


def test_royal_home_keeps_search_and_navigation_functional(client):
    page = client.get("/koradaso")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert '<nav class="royal-tabs"' not in body
    assert 'target="_blank"' not in body
    assert "New tab" not in body
    assert 'href="/arena"' in body
    assert 'href="/search"' in body
    assert 'id="bookmark-list"' in body
    assert 'aria-label="Browser menu"' in body
    assert 'id="address-form"' in body
    assert 'id="trust-state"' in body


def test_termux_runner_preserves_existing_server_and_routes():
    source = Path("scripts/koradaso_termux_local.sh").read_text(encoding="utf-8")
    assert 'OAP_KORADASO_PORT:-5052' in source
    assert 'required = {"/koradaso", "/world", "/search", "/koradaso/web-search", "/arena"}' in source
    assert 'sock.bind(("127.0.0.1", port))' in source
    assert 'port {port} is already occupied; existing server untouched.' in source
    assert '--host 127.0.0.1' in source
    assert 'OAP_SURFACE_ROLE:-' in source
    assert "reset --hard" not in source


def test_termux_auto_opens_only_after_real_branded_http_response():
    source = Path("scripts/koradaso_termux_local.sh").read_text(encoding="utf-8")
    assert 'OAP_KORADASO_OPEN_BROWSER:-1' in source
    assert 'curl --noproxy' in source
    assert 'OPEN_PATH=/koradaso' in source
    assert 'url="http://127.0.0.1:$PORT$OPEN_PATH"' in source
    assert 'KORADASO Internet · ON ANY POSTCODE' in source
    assert 'id="address-form"' in source
    assert 'termux-open-url "$url"' in source
    assert 'live branded $OPEN_PATH page not verified.' in source
    assert 'PORT=5052\n    OPEN_PATH=/arena' in source
    assert '<title>OAP Arena</title>' in source
    assert 'id="arena-games"' in source



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
    assert '<a href="/world?source=oap-os">🌍 OAP World</a>' in source



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
    assert 'aria-label="Browser menu"' in source
    for label in ("Maps", "Mail"):
        assert f"<strong>{label}</strong>" not in source
    assert 'id="settings-downloads"' in source
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
    assert 'class="public-smi" href="/studio?source=koradaso"' in html
    for prefix in ("/auth", "/mission", "/smi"):
        assert f'href="{prefix}' not in html
    assert 'action="/search" method="get"' in html
    assert 'id="address" name="q"' in html
    assert 'href="/arena"' in html
    assert '<strong>Arena</strong>' in html
    assert 'id="bookmark-list"' in html
    assert 'aria-label="Browser menu"' in html
    assert 'class="royal-menu"' in html
    header = html.split('<header class="top">', 1)[1].split("</header>", 1)[0]
    assert 'id="browser-settings"' in header
    assert '<summary aria-label="Browser menu"' in header
    assert 'id="settings-downloads"' in header
    assert 'id="drawer-bookmarks"' in header
    assert "Use your authenticated OAP Core workspace to access SMI." not in header
    assert 'id="address-form"' in source
    assert client.get("/arena").status_code in (200, 302)
    assert "https://duckduckgo.com" not in source


def test_koradaso_arena_and_discovery_tabs_are_truthful(client):
    html = client.get("/koradaso").get_data(as_text=True)
    assert 'class="tile arena-tile" href="/arena"' in html
    assert "Play OAP games · Challenge hub" in html
    assert 'class="discovery-strip"' in html
    assert '<a href="/search">OAP Search</a>' in html
    assert '<a href="/koradaso/web-search">Web Index</a>' in html
    assert "Images · Soon" not in html
    assert "Videos · Soon" not in html

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
    assert 'name="search-mode"' not in source
    assert 'name="search-mode"' not in source
    assert 'href="/world?source=oap-os"' in source


def test_koradaso_uses_only_first_party_www_search(client, monkeypatch):
    monkeypatch.delenv("OAP_KORADASO_WEB_INDEX", raising=False)
    source = SOURCE.read_text(encoding="utf-8")
    assert "DuckDuckGo" not in source
    assert "duckduckgo.com" not in source
    assert 'window.location.assign("/koradaso/web-search?q="+encodeURIComponent(raw))' in source
    missing = client.get("/koradaso/web-search?q=test")
    assert missing.status_code == 503
    assert b"Web index unavailable." in missing.data
    assert b"No indexed results can be confirmed." in missing.data
    assert b'href="/search?q=test"' in missing.data


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
    import subprocess
    import sys

    db = tmp_path / "koradaso.sqlite3"
    result = subprocess.run(
        [sys.executable, "scripts/koradaso_index_public.py",
         "--source", "scripts/koradaso_starter_pages.jsonl", "--db", str(db)],
        capture_output=True, text=True, check=False, timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    monkeypatch.setenv("OAP_KORADASO_WEB_INDEX", str(db))
    response = client.get("/koradaso/web-search?q=mitcham")
    assert response.status_code == 200
    for title in (b"Mitcham Library", b"Mitcham Junction Tram Stop", b"Mitcham Junction Station"):
        assert title in response.data
    assert b'href="/search?q=mitcham"' in response.data


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


def test_koradaso_www_shows_query_snippet_for_existing_crawl(tmp_path, monkeypatch, client):
    from mission_control.koradaso_web_index import ingest_public_page

    db = tmp_path / "existing-index.sqlite3"
    monkeypatch.setenv("OAP_KORADASO_WEB_INDEX", str(db))
    ingest_public_page(
        db, url="https://example.org/library", title="Mitcham Library",
        description=(
            "Skip to main content rgb(255,255,255) Home Indoor venues "
            "Mitcham Library can be hired out of hours for community activities. "
            + "The library has spaces for local events and community groups. " * 4
            + "Wheelchair access is available from London Road."
        ),
    )
    response = client.get("/koradaso/web-search?q=wheelchair")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert '<small>example.org</small>' in page
    assert 'href="https://example.org/library"' in page
    assert "Wheelchair access is available from London Road." in page
    assert "rgb(255,255,255)" not in page
    snippet = page.split('<article class="result">', 1)[1].split("<p>", 1)[1].split("</p>", 1)[0]
    assert len(snippet) <= 170


def test_koradaso_www_prefers_full_title_phrase(tmp_path, monkeypatch):
    from mission_control.koradaso_web_index import (
        ingest_public_page,
        search_public_pages,
    )

    db = tmp_path / "ranking.sqlite3"
    monkeypatch.setenv("OAP_KORADASO_WEB_INDEX", str(db))
    ingest_public_page(db, url="https://example.org/a", title="Library services in Mitcham")
    ingest_public_page(db, url="https://example.org/z", title="Mitcham Library | Council")

    results, ready = search_public_pages("Mitcham Library")
    assert ready
    assert [result["url"] for result in results] == [
        "https://example.org/z", "https://example.org/a",
    ]
