from flask import Flask

from mission_control import music_assets, music_public_views


ASSET = "22222222-2222-4222-8222-222222222222"
OWNER = "11111111-1111-4111-8111-111111111111"


def _app():
    app = Flask(__name__)
    app.register_blueprint(music_public_views.bp)
    return app


def test_public_stream_is_locked_without_current_entitlement(monkeypatch):
    monkeypatch.setattr(
        music_public_views._music_entitlement_store,
        "public_gate",
        lambda **_kwargs: {
            "allowed": False,
            "reason": "public_entitlement_missing",
        },
    )
    response = _app().test_client().get(
        f"/music/api/assets/{ASSET}/stream"
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "public_playback_locked"


def test_public_stream_delivers_real_range_only_after_all_gates(monkeypatch):
    monkeypatch.setattr(
        music_public_views._music_entitlement_store,
        "public_gate",
        lambda **_kwargs: {
            "allowed": True,
            "owner_identity_id": OWNER,
            "rights_decision_hash": "a" * 64,
            "entitlement_id": "33333333-3333-4333-8333-333333333333",
        },
    )
    monkeypatch.setattr(
        music_public_views._music_asset_store,
        "read_public_candidate",
        lambda **_kwargs: (
            OWNER,
            b"0123456789",
            "audio/mpeg",
            "b" * 64,
            "track.mp3",
        ),
    )
    response = _app().test_client().get(
        f"/music/api/assets/{ASSET}/stream",
        headers={"Range": "bytes=2-5"},
    )
    assert response.status_code == 206
    assert response.data == b"2345"
    assert response.headers["Content-Range"] == "bytes 2-5/10"
    assert response.headers["Accept-Ranges"] == "bytes"
    assert response.headers["X-OAP-Rights-Decision"] == "a" * 64


def test_public_stream_returns_gone_after_asset_stop(monkeypatch):
    monkeypatch.setattr(
        music_public_views._music_entitlement_store,
        "public_gate",
        lambda **_kwargs: {
            "allowed": True,
            "owner_identity_id": OWNER,
            "rights_decision_hash": "a" * 64,
            "entitlement_id": "33333333-3333-4333-8333-333333333333",
        },
    )

    def stopped(**_kwargs):
        raise music_assets.MusicAssetStopped("music_asset_stopped")

    monkeypatch.setattr(
        music_public_views._music_asset_store,
        "read_public_candidate",
        stopped,
    )
    response = _app().test_client().get(
        f"/music/api/assets/{ASSET}/stream"
    )
    assert response.status_code == 410
    assert response.get_json()["error"]["code"] == "music_asset_stopped"
