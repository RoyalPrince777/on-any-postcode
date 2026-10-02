from flask import Flask

from mission_control import entertainment_catalogue, media_assets, product_core_views

ASSET_ID = "7fa79d7e-3ed1-4efc-a1b6-f751ebd5ca20"


def test_media_video_validation_accepts_mp4_and_webm_and_rejects_mismatch():
    media_assets._validate_magic(b"\x00\x00\x00\x18ftyp" + b"x" * 32, "video/mp4")
    media_assets._validate_magic(b"\x1aE\xdf\xa3" + b"x" * 32, "video/webm")
    try:
        media_assets._validate_magic(b"not-a-video", "video/mp4")
    except ValueError as exc:
        assert str(exc) == "video_content_mismatch"
    else:
        raise AssertionError("mismatched video bytes must fail closed")


def test_media_asset_contract_is_first_party_bounded_and_stoppable():
    assert media_assets.MAX_VIDEO_BYTES == 64 * 1024 * 1024
    assert media_assets.MAX_OWNER_STORAGE_BYTES == 1024 * 1024 * 1024
    joined = "\n".join(media_assets.SCHEMA_STATEMENTS)
    assert media_assets.MEDIA_ASSET_MIGRATION_VERSION == "0014_oap_media_assets"
    assert "oap_media_assets" in joined
    assert "owner_identity_id UUID NOT NULL" in joined
    assert "media BYTEA NOT NULL" in joined
    assert "stopped BOOLEAN NOT NULL DEFAULT FALSE" in joined


def test_universal_player_accepts_typed_media_identity_but_stays_fail_closed():
    media_id = f"oap:media:{ASSET_ID}"
    player = entertainment_catalogue.universal_player_contract({
        "content_id": media_id,
        "publication_state": "PUBLISHED",
        "rights_review_state": "VERIFIED",
    })
    assert player["content_id"] == media_id
    assert player["owner"] == "OAP Player"
    assert player["playback_enabled"] is False
    assert player["stream_url"] is None
    assert player["rights"]["allowed"] is False

    for namespace in ("tune", "media", "tv", "live", "records"):
        content_id = f"oap:{namespace}:{ASSET_ID}"
        assert entertainment_catalogue.canonical_content_id(content_id) == content_id
    assert entertainment_catalogue.canonical_content_id(
        f"oap:external:{ASSET_ID}"
    ) is None
    assert entertainment_catalogue.canonical_content_id("https://example.test/video") is None


def test_media_asset_routes_are_authenticated_product_routes():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    rules = {rule.rule: set(rule.methods) for rule in app.url_map.iter_rules()}

    assert rules["/mission/organs/media/assets/upload"] >= {"POST"}
    assert rules["/mission/organs/media/assets"] >= {"GET"}
    assert rules["/mission/organs/media/assets/<asset_id>/video"] >= {"GET"}
    assert rules["/mission/organs/media/assets/<asset_id>/stop"] >= {"POST"}


def test_media_projection_keeps_public_playback_fail_closed(monkeypatch):
    monkeypatch.setattr(
        product_core_views.product_core_services,
        "tune_dashboard",
        lambda identity: {"organ": "OAP Music", "releases": [], "playlists": []},
    )
    result = product_core_views._media_projection("owner")
    assert result["video_asset_contract_ready"] is True
    assert result["public_video_playback_enabled"] is False
    assert result["entertainment"]["playback_enabled"] is False
