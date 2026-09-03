from mission_control import link_realtime


def test_realtime_capabilities_use_oap_names_and_fail_closed():
    states = link_realtime.capability_state()
    assert [item["name"] for item in states] == [
        "Voice",
        "Call",
        "Face Up",
        "Media",
        "Files",
        "Around Now",
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


def test_privacy_dial_defaults_are_private_first():
    dial = link_realtime.privacy_dial()
    assert dial["voice"] is True
    assert dial["call"] is False
    assert dial["face_up"] is False
    assert dial["around_now"] is False
    assert dial["share_my_spot"] is False


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
