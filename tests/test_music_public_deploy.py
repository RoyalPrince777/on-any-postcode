import pytest
from flask import Flask

from mission_control import music_civilization_migration, music_public_views


def test_public_music_route_is_real_and_truth_mode():
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.register_blueprint(music_public_views.bp)
    client = app.test_client()
    response = client.get("/music")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "OAP Music" in body
    assert "Public playback appears only for tracks with current rights and entitlement proof." in body
    assert "Playback stays locked" in body


def test_music_migration_requires_explicit_approval():
    with pytest.raises(RuntimeError, match="Explicit human approval required"):
        music_civilization_migration.apply()


def test_music_migration_versions_are_ordered_and_complete():
    assert [version for version, _ in music_civilization_migration._MIGRATIONS] == [
        "0007_oap_music_evidence_chain",
        "0008_oap_radio_core",
        "0009_oap_records_archive",
        "0010_oap_live_music",
        "0011_oap_music_recovery_manifest",
        "0012_oap_music_acceptance_receipts",
        "0013_oap_music_assets",
        "0014_oap_music_rights_grants",
        "0015_oap_music_entitlements",
    ]


def test_music_migration_applies_base_product_core_first(monkeypatch):
    calls = []

    def fake_base(*, assume_yes=False, dry_run=False):
        calls.append(("base", assume_yes, dry_run))
        return {"schema_ready": True}

    class Connection:
        def __enter__(self):
            calls.append(("music_connect",))
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, sql, params=()):
            if sql.startswith("SELECT pg_advisory_xact_lock"):
                return self
            if sql.startswith("SELECT checksum FROM oap_schema_migrations"):
                return _Result(None)
            if sql.startswith("INSERT INTO oap_schema_migrations"):
                return self
            return self
        def fetchone(self):
            return None
        def commit(self):
            calls.append(("commit",))

    class _Result:
        def __init__(self, row):
            self.row = row
        def fetchone(self):
            return self.row

    monkeypatch.setattr(
        music_civilization_migration.product_cores,
        "init_product_core_schema",
        fake_base,
    )
    monkeypatch.setattr(
        music_civilization_migration.postgres_db,
        "connect",
        lambda **_kwargs: Connection(),
    )
    result = music_civilization_migration.apply(assume_yes=True)
    assert calls[0][0] == "base"
    assert result["base_product_core_ready"] is True
    assert result["base_product_core_migration"] == "0006_music_market_post_office"


def test_public_music_status_is_first_party_only():
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.register_blueprint(music_public_views.bp)
    client = app.test_client()
    response = client.get("/music/api/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["first_party_catalogue_ready"] is True
    assert payload["first_party_discovery_ready"] is True
    assert "open_source_directory_ready" not in payload
    assert "open_source_count" not in payload


def test_public_music_status_does_not_fake_track_or_playback_readiness():
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.register_blueprint(music_public_views.bp)
    response = app.test_client().get("/music/api/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["front_door_ready"] is True
    assert payload["first_party_catalogue_ready"] is True
    assert payload["first_party_discovery_ready"] is True
    assert payload["public_catalogue_track_count"] == 0
    assert payload["public_playback_enabled"] is False
    assert payload["public_radio_streaming_enabled"] is False
    assert payload["rights_verified_by_software"] is False


def test_music_page_controls_have_real_targets_and_no_fake_play_button():
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.register_blueprint(music_public_views.bp)
    body = app.test_client().get("/music").get_data(as_text=True)
    for target in ("catalogue", "genres", "civilization", "creators", "radio", "records"):
        assert f'data-target="{target}"' in body
        assert f'id="{target}"' in body
    for anchor in ("#catalogue", "#civilization", "#radio", "#records", "#player"):
        assert f'href="{anchor}"' in body
    assert 'id="music-search"' in body
    assert "First-Party Discovery" in body
    assert "Free / Open Discovery Sources" not in body
    assert "Open source" not in body
    assert "<button disabled>▶ Play</button>" not in body
    assert "▶ Play locked" in body


def test_first_party_listener_contract_has_no_external_core_dependency():
    contract = music_public_views.music_public_catalogue.listener_contract()
    assert contract["ownership"] == "first_party"
    assert contract["canonical_release_store"] == "oap_music_releases"
    assert contract["canonical_track_store"] == "oap_music_tracks"
    assert contract["canonical_playlist_store"] == "oap_music_playlists"
    assert contract["external_catalogue_dependency"] is False
    assert contract["external_identity_dependency"] is False
    assert contract["external_player_dependency"] is False
    assert contract["external_analytics_dependency"] is False
    assert contract["playback_enabled"] is False


def test_first_party_catalogue_api_fails_closed_when_store_unavailable(monkeypatch):
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.register_blueprint(music_public_views.bp)
    monkeypatch.setattr(
        music_public_views.music_public_catalogue,
        "catalogue",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("db down")),
    )
    response = app.test_client().get("/music/api/catalogue?q=test")
    assert response.status_code == 503
    payload = response.get_json()
    assert payload["ownership"] == "first_party"
    assert payload["items"] == []
    assert payload["playback_enabled"] is False
    assert payload["external_catalogue_dependency"] is False


def test_music_page_is_first_party_listener_surface_not_external_catalogue():
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.register_blueprint(music_public_views.bp)
    body = app.test_client().get("/music").get_data(as_text=True)
    for target in ("home", "catalogue", "artists", "releases", "playlists", "library"):
        assert f'data-target="{target}"' in body
        assert f'id="{target}"' in body
    assert "Search OAP Music" in body
    assert "Search the free/open source directory" not in body
    assert "OAP Music is a first-party catalogue." in body
    assert "/music/api/catalogue?q=" in body


def test_music_has_dedicated_install_manifest_and_identity(client):
    response = client.get("/music/manifest.webmanifest")
    manifest = response.get_json()
    assert response.status_code == 200
    assert response.content_type == "application/manifest+json"
    assert manifest["name"] == "OAP Music"
    assert manifest["id"] == "/music"
    assert manifest["start_url"].startswith("/music")
    assert manifest["scope"] == "/music"
    assert manifest["display"] == "standalone"
    assert manifest["prefer_related_applications"] is False
    assert {item["url"] for item in manifest["shortcuts"]} == {
        "/music#player", "/music#radio", "/music#creators",
    }


def test_music_page_exposes_real_install_contract(client):
    body = client.get("/music").get_data(as_text=True)
    assert 'rel="manifest" href="/music/manifest.webmanifest"' in body
    assert "data-oap-music-install hidden" in body
    assert 'src="/assets/oap-music-install.js"' in body
    assert 'data-oap-music-install-status role="status"' in body
    assert "First-party installable web app" in body


def test_music_install_controller_uses_existing_safe_root_worker(client):
    response = client.get("/assets/oap-music-install.js")
    source = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.content_type.startswith("application/javascript")
    assert 'navigator.serviceWorker.register("/service-worker.js", { scope: "/" })' in source
    assert "beforeinstallprompt" in source
    assert "appinstalled" in source
    assert "OAP Music is ready to install." in source
