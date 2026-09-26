from mission_control import music_civilization


def test_civilization_contract_uses_one_player_and_no_duplicate_engine():
    result = music_civilization.contracts()
    assert result["one_player"] is True
    assert result["duplicate_media_engine_created"] is False
    assert result["public_execution_enabled"] is False


def test_readiness_requires_music_and_recovery_and_respects_stop():
    blocked = music_civilization.readiness(
        music_gate={"private_handoff_ready": True},
        recovery_state={"readback_verified": False},
        radio_state={"stopped": False},
        live_state={"stopped": False},
    )
    assert blocked["records_private_archive_ready"] is False
    assert blocked["radio_private_rotation_ready"] is False
    assert blocked["live_private_handoff_ready"] is False

    ready = music_civilization.readiness(
        music_gate={"private_handoff_ready": True},
        recovery_state={"readback_verified": True},
        radio_state={"stopped": False},
        live_state={"stopped": False},
    )
    assert ready["records_private_archive_ready"] is True
    assert ready["radio_private_rotation_ready"] is True
    assert ready["live_private_handoff_ready"] is True
    assert ready["public_playback_enabled"] is False
    assert ready["external_distribution_enabled"] is False


def test_stop_overrides_private_radio_and_live_readiness():
    result = music_civilization.readiness(
        music_gate={"private_handoff_ready": True},
        recovery_state={"readback_verified": True},
        radio_state={"stopped": True},
        live_state={"stopped": True},
    )
    assert result["records_private_archive_ready"] is True
    assert result["radio_private_rotation_ready"] is False
    assert result["live_private_handoff_ready"] is False
