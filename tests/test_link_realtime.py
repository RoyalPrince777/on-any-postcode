from mission_control import link_realtime


def test_realtime_capabilities_use_oap_names_and_fail_closed():
    states = link_realtime.capability_state()
    assert [item["name"] for item in states] == [
        "Voice",
        "Call",
        "Face Up",
        "Share",
        "Files",
        "Around Now",
        "Live Spot",
    ]
    assert all(item["ready"] is False for item in states)
    assert all(item["missing"] for item in states)


def test_face_up_requires_camera_microphone_and_transport_gates():
    state = next(
        item for item in link_realtime.capability_state({"signalling": True})
        if item["id"] == "face_up"
    )
    assert state["ready"] is False
    assert "microphone_permission" in state["missing"]
    assert "camera_permission" in state["missing"]
    assert "turn_fallback" in state["missing"]


def test_capability_only_turns_ready_when_all_evidence_is_true():
    voice = next(
        item
        for item in link_realtime.capability_state(
            {
                "microphone_permission": True,
                "media_store": True,
                "guardian_scan": True,
            }
        )
        if item["id"] == "voice"
    )
    assert voice["ready"] is True
    assert voice["missing"] == []


def test_live_spot_requires_explicit_stop_and_private_visibility():
    live_spot = next(
        item
        for item in link_realtime.capability_state(
            {
                "location_permission": True,
                "presence_store": True,
                "expiry": True,
                "per_link_visibility": True,
            }
        )
        if item["id"] == "live_spot"
    )
    assert live_spot["ready"] is False
    assert live_spot["missing"] == ["explicit_live_spot_stop"]


def test_privacy_dial_defaults_are_private_first():
    dial = link_realtime.privacy_dial()
    assert dial["voice"] is True
    assert dial["call"] is False
    assert dial["face_up"] is False
    assert dial["around_now"] is False
    assert dial["share_my_spot"] is False
    assert dial["live_spot"] is False


def test_privacy_dial_only_accepts_known_boolean_overrides():
    dial = link_realtime.privacy_dial(
        {"face_up": True, "around_now": True, "unknown": True, "call": "yes"}
    )
    assert dial["face_up"] is True
    assert dial["around_now"] is True
    assert dial["call"] is False
    assert "unknown" not in dial


def test_realtime_runtime_does_not_require_phone_number_or_call_recording():
    assert link_realtime.RUNTIME_GATES["phone_number_required"] is False
    assert link_realtime.RUNTIME_GATES["record_calls_by_default"] is False
    assert link_realtime.RUNTIME_GATES["public_media_projection"] is False


def test_oap_motion_is_first_party_offline_safe_and_fail_closed():
    assert link_realtime.OAP_MOTION_SYSTEM["name"] == "OAP Motion"
    assert link_realtime.OAP_MOTION_SYSTEM["ownership"] == "first_party"
    assert link_realtime.OAP_MOTION_SYSTEM["external_emoji_provider_required"] is False
    assert link_realtime.OAP_MOTION_SYSTEM["reduced_motion_required"] is True
    assert link_realtime.OAP_MOTION_SYSTEM["offline_safe_required"] is True

    state = link_realtime.motion_state()
    assert state["ready"] is False
    assert state["signals"] == 15
    assert state["missing"] == list(link_realtime.OAP_MOTION_RUNTIME_REQUIREMENTS)


def test_oap_motion_only_certifies_with_all_local_accessibility_evidence():
    state = link_realtime.motion_state(
        {requirement: True for requirement in link_realtime.OAP_MOTION_RUNTIME_REQUIREMENTS}
    )
    assert state["ready"] is True
    assert state["missing"] == []
