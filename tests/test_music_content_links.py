from mission_control import music_content_links


class _Result:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self, scripted):
        self.scripted = list(scripted)
        self.calls = []
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        row = self.scripted.pop(0) if self.scripted else None
        return _Result(row)

    def commit(self):
        self.committed = True


def test_content_link_schema_uses_one_track_content_group():
    schema = "\n".join(music_content_links.SCHEMA_STATEMENTS)
    assert music_content_links.MUSIC_CONTENT_LINK_MIGRATION_VERSION == "0019_oap_music_content_links"
    assert "track_id UUID NOT NULL UNIQUE" in schema
    assert "oap_music_track_content" in schema
    assert "oap_music_video_links" in schema
    assert "content_group_id" in schema


def test_save_lyrics_and_credits_stays_track_owned(monkeypatch):
    connection = _Connection([
        (1,),
        None,
        None,
        None,
    ])
    monkeypatch.setattr(music_content_links.postgres_db, "connect", lambda **kwargs: connection)
    result = music_content_links.save_track_content(
        owner_identity_id="11111111-1111-4111-8111-111111111111",
        track_id="22222222-2222-4222-8222-222222222222",
        lyrics="Born local, built global.",
        credits=[{"name": "Artist One", "role": "Writer"}],
    )
    assert result["lyrics_present"] is True
    assert result["credit_count"] == 1
    assert result["video_bytes_duplicated"] is False
    sql = "\n".join(call[0] for call in connection.calls)
    assert "JOIN oap_music_releases" in sql
    assert "INSERT INTO oap_music_track_content" in sql
    assert connection.committed is True


def test_video_link_reuses_shared_content_identity_without_fake_views(monkeypatch):
    group_id = "33333333-3333-4333-8333-333333333333"
    link_id = "44444444-4444-4444-8444-444444444444"
    connection = _Connection([
        (1,),
        (group_id,),
        (link_id,),
    ])
    monkeypatch.setattr(music_content_links.postgres_db, "connect", lambda **kwargs: connection)
    result = music_content_links.add_video_link(
        owner_identity_id="11111111-1111-4111-8111-111111111111",
        track_id="22222222-2222-4222-8222-222222222222",
        video_kind="OFFICIAL_VIDEO",
        oap_tv_path="/tv-media",
    )
    assert result["content_group_id"] == group_id
    assert result["oap_tv_path"] == "/tv-media"
    assert result["video_bytes_duplicated"] is False
    assert result["shared_engagement_identity"] is True
    assert result["view_count"] is None
    assert result["qualified_engagement_measurement_proven"] is False


def test_unified_engagement_contract_forbids_blind_view_addition():
    contract = music_content_links.engagement_contract(
        content_group_id="33333333-3333-4333-8333-333333333333"
    )
    assert contract["surfaces"] == ("OAP Music", "OAP TV")
    assert contract["music_views"] is None
    assert contract["tv_views"] is None
    assert contract["combined_reach"] is None
    assert contract["raw_counts_must_not_be_blindly_added"] is True
    assert contract["cross_surface_dedupe_ready"] is False
