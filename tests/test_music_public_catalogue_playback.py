from mission_control import music_public_catalogue


def test_catalogue_exposes_stream_only_for_active_global_entitlement(monkeypatch):
    class Result:
        def fetchall(self):
            return [(
                "11111111-1111-4111-8111-111111111111",
                "Release",
                "single",
                "22222222-2222-4222-8222-222222222222",
                "Track",
                1,
                180000,
                False,
                "33333333-3333-4333-8333-333333333333",
                False,
                "44444444-4444-4444-8444-444444444444",
            )]

    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, sql, params=()):
            assert "oap_music_entitlements" in sql
            assert "e.territory='*'" in sql
            assert "e.channel='OAP Music'" in sql
            return Result()

    monkeypatch.setattr(
        music_public_catalogue.postgres_db,
        "connect",
        lambda **_kwargs: Connection(),
    )
    result = music_public_catalogue.catalogue()
    assert result["playback_enabled"] is True
    assert result["playable_item_count"] == 1
    item = result["items"][0]
    assert item["playback_enabled"] is True
    assert item["stream_url"].endswith(
        "/33333333-3333-4333-8333-333333333333/stream"
    )
    assert item["playback_gate_revalidated_on_request"] is True


def test_catalogue_keeps_stopped_asset_locked(monkeypatch):
    class Result:
        def fetchall(self):
            return [(
                "11111111-1111-4111-8111-111111111111",
                "Release",
                "single",
                "22222222-2222-4222-8222-222222222222",
                "Track",
                1,
                180000,
                False,
                "33333333-3333-4333-8333-333333333333",
                True,
                "44444444-4444-4444-8444-444444444444",
            )]

    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, _sql, _params=()):
            return Result()

    monkeypatch.setattr(
        music_public_catalogue.postgres_db,
        "connect",
        lambda **_kwargs: Connection(),
    )
    result = music_public_catalogue.catalogue()
    assert result["playback_enabled"] is False
    assert result["playable_item_count"] == 0
    assert result["items"][0]["stream_url"] is None
