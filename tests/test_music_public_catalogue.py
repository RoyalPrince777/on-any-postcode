from mission_control import music_public_catalogue


def test_listener_contract_is_canonical_first_party():
    result = music_public_catalogue.listener_contract()
    assert result["platform"] == "OAP Music"
    assert result["ownership"] == "first_party"
    assert result["canonical_release_store"] == "oap_music_releases"
    assert result["canonical_track_store"] == "oap_music_tracks"
    assert result["canonical_playlist_store"] == "oap_music_playlists"
    assert result["external_catalogue_dependency"] is False
    assert result["external_player_dependency"] is False
    assert result["playback_enabled"] is False


def test_catalogue_reads_only_published_verified_oap_rows(monkeypatch):
    events = []

    class Result:
        def fetchall(self):
            return [
                (
                    "11111111-1111-1111-1111-111111111111",
                    "Release One",
                    "single",
                    "22222222-2222-2222-2222-222222222222",
                    "Track One",
                    1,
                    123000,
                    False,
                )
            ]

    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, sql, params):
            events.append((sql, params))
            return Result()

    monkeypatch.setattr(
        music_public_catalogue.postgres_db,
        "connect",
        lambda **kwargs: Connection(),
    )
    result = music_public_catalogue.catalogue(query="Track")
    sql, params = events[0]
    assert "r.state='PUBLISHED'" in sql
    assert "r.rights_status='VERIFIED'" in sql
    assert params[0] == "%track%"
    assert result["ownership"] == "first_party"
    assert result["item_count"] == 1
    assert result["items"][0]["track_title"] == "Track One"
    assert result["items"][0]["playback_enabled"] is False
    assert result["items"][0]["stream_url"] is None
    assert result["external_catalogue_dependency"] is False
