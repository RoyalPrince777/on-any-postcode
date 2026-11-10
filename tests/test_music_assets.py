from flask import Flask

from mission_control import music_assets, product_core_views


def test_music_asset_audio_validation_accepts_supported_magic_and_rejects_mismatch():
    music_assets._validate_magic(b"ID3" + b"x" * 32, "audio/mpeg")
    music_assets._validate_magic(b"OggS" + b"x" * 32, "audio/ogg")
    music_assets._validate_magic(b"RIFF" + b"1234" + b"WAVE" + b"x" * 16, "audio/wav")

    try:
        music_assets._validate_magic(b"not-a-real-mp3", "audio/mpeg")
    except ValueError as exc:
        assert str(exc) == "audio_content_mismatch"
    else:
        raise AssertionError("mismatched audio bytes must fail closed")


def test_music_asset_contract_is_first_party_bounded():
    assert music_assets.MAX_AUDIO_BYTES == 6 * 1024 * 1024
    assert music_assets.MAX_OWNER_STORAGE_BYTES == 250 * 1024 * 1024
    joined = "\n".join(music_assets.SCHEMA_STATEMENTS)
    assert music_assets.MUSIC_ASSET_MIGRATION_VERSION == "0013_oap_music_assets"
    assert "oap_music_assets" in joined
    assert "owner_identity_id UUID NOT NULL" in joined
    assert "media BYTEA NOT NULL" in joined
    assert "track_id UUID NOT NULL UNIQUE" in joined


def test_music_upload_player_and_radio_routes_are_registered():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    rules = {rule.rule: set(rule.methods) for rule in app.url_map.iter_rules()}

    assert rules["/mission/organs/tune/releases/<release_id>/upload"] >= {"POST"}
    assert rules["/mission/organs/tune/assets"] >= {"GET"}
    assert rules["/mission/organs/tune/assets/<asset_id>/audio"] >= {"GET"}
    assert rules["/mission/organs/tune/releases/<release_id>/review"] >= {"POST"}
    assert rules["/mission/organs/radio/stations"] >= {"POST"}
    assert rules["/mission/organs/radio/stations/<station_id>/shows"] >= {"POST"}
    assert rules["/mission/organs/radio/stations/<station_id>/schedule"] >= {"POST"}
    assert rules["/mission/organs/radio/stations/<station_id>/rotation"] >= {"POST"}
    assert rules["/mission/organs/radio/stations/<station_id>/stop"] >= {"POST"}


def test_music_creator_surface_exposes_real_governed_controls():
    with open("mission_control/templates/oap_music.html", encoding="utf-8") as handle:
        template = handle.read()
    for control_id in (
        "release-form",
        "upload-form",
        "review-form",
        "station-form",
        "rotation-form",
        "show-form",
        "schedule-form",
        "stop-form",
    ):
        assert f'id="{control_id}"' in template
    assert "/tune/releases/" in template
    assert "/radio/stations/" in template
    assert "broadcast not auto-started" not in template
    assert "schedule-form" in template
