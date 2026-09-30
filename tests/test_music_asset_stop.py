import pytest

from mission_control import music_assets

OWNER = "11111111-1111-4111-8111-111111111111"
ASSET = "22222222-2222-4222-8222-222222222222"
RELEASE = "33333333-3333-4333-8333-333333333333"
TRACK = "44444444-4444-4444-8444-444444444444"


def test_stopped_music_asset_fails_closed_before_byte_delivery(monkeypatch):
    class Result:
        def fetchone(self):
            return (b"ID3demo", "audio/mpeg", "0" * 64, "demo.mp3", True)

    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, _sql, _params=()):
            return Result()

    monkeypatch.setattr(
        music_assets.postgres_db,
        "connect",
        lambda **_kwargs: Connection(),
    )
    with pytest.raises(music_assets.MusicAssetStopped, match="music_asset_stopped"):
        music_assets.MusicAssetStore().read(
            owner_identity_id=OWNER,
            asset_id=ASSET,
        )


def test_stop_is_owner_scoped_and_disables_delivery(monkeypatch):
    calls = []

    class Result:
        def fetchone(self):
            return (RELEASE, TRACK, _Instant())

    class _Instant:
        def isoformat(self):
            return "2026-09-29T13:00:00+00:00"

    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, sql, params=()):
            calls.append((sql, params))
            return Result()
        def commit(self):
            calls.append(("commit", ()))

    monkeypatch.setattr(
        music_assets.postgres_db,
        "connect",
        lambda **_kwargs: Connection(),
    )
    result = music_assets.MusicAssetStore().stop(
        owner_identity_id=OWNER,
        asset_id=ASSET,
    )
    update_sql, params = calls[0]
    assert "WHERE asset_id=%s AND owner_identity_id=%s" in update_sql
    assert params == (ASSET, OWNER)
    assert result["stopped"] is True
    assert result["audio_delivery_enabled"] is False
    assert result["public_playback_enabled"] is False


def test_stop_columns_are_governed_by_music_rights_migration():
    from mission_control import music_rights_store

    schema = "\n".join(music_rights_store.SCHEMA_STATEMENTS)
    assert "ADD COLUMN IF NOT EXISTS stopped BOOLEAN" in schema
    assert "ADD COLUMN IF NOT EXISTS stopped_at TIMESTAMPTZ" in schema
