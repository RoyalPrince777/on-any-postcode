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
    assert "No publicly cleared playable track is available yet." in body
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


def test_public_open_source_api_returns_truth_mode_directory():
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.register_blueprint(music_public_views.bp)
    client = app.test_client()
    response = client.get("/music/api/open-sources")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["canonical_catalogue"] == "OAP Music"
    assert len(payload["entries"]) >= 6
    labels = {row["label"] for row in payload["entries"]}
    assert "Free Music Archive" in labels
    assert "ccMixter" in labels
    assert "Musopen" in labels
    assert all(row["connected"] is False for row in payload["entries"])
    assert all(row["licence_verified"] is False for row in payload["entries"])
    assert all(row["bulk_import_allowed"] is False for row in payload["entries"])


def test_public_music_status_does_not_fake_track_or_playback_readiness():
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.register_blueprint(music_public_views.bp)
    response = app.test_client().get("/music/api/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["front_door_ready"] is True
    assert payload["open_source_directory_ready"] is True
    assert payload["open_source_count"] >= 6
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
    assert "source-card" in body
    assert "Open source" in body
    assert "<button disabled>▶ Play</button>" not in body
    assert "▶ Play locked" in body
