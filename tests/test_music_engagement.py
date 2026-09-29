from mission_control import music_engagement


def test_qualified_engagement_rules():
    assert music_engagement.qualifies(event_type="START", playback_seconds=0) is False
    assert music_engagement.qualifies(event_type="HEARTBEAT", playback_seconds=30) is True
    assert music_engagement.qualifies(
        event_type="HEARTBEAT", playback_seconds=12, duration_seconds=20
    ) is True
    assert music_engagement.qualifies(event_type="COMPLETE", playback_seconds=1) is True


def test_listener_key_is_pseudonymous_and_stable():
    first = music_engagement.listener_key("11111111-1111-4111-8111-111111111111")
    second = music_engagement.listener_key("11111111-1111-4111-8111-111111111111")
    assert first == second
    assert first != "11111111-1111-4111-8111-111111111111"
    assert len(first) == 64


def test_engagement_schema_is_cross_surface_and_privacy_bounded():
    schema = "\n".join(music_engagement.SCHEMA_STATEMENTS)
    assert music_engagement.MUSIC_ENGAGEMENT_MIGRATION_VERSION == "0020_oap_music_engagement"
    assert "OAP_MUSIC" in schema
    assert "OAP_TV" in schema
    assert "listener_key CHAR(64)" in schema
    assert "content_group_id" in schema
    assert "qualified BOOLEAN" in schema
