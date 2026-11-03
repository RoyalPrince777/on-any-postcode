"""Bagheera contract regressions: no synthetic runtime claims."""
import pytest

from oap.smi.bagheera_companion import (
    bagheera_companion,
    bagheera_renderer_state,
    review_bagheera_action,
)


def test_default_is_lightweight_and_sensors_off():
    profile = bagheera_companion()
    assert profile.presentation == "avatar_2d"
    assert not profile.voice_enabled
    assert not profile.camera_enabled
    assert not profile.microphone_enabled
    assert not profile.runtime_verified
    assert profile.founder_final and profile.advisory_only


def test_hybrid_voice_needs_both_permissions():
    assert not bagheera_companion(
        presentation="hybrid_3d", voice_consent=True
    ).voice_enabled
    live_request = bagheera_companion(
        presentation="hybrid_3d", voice_consent=True,
        microphone_consent=True
    )
    assert live_request.voice_enabled
    assert not live_request.runtime_verified


@pytest.mark.parametrize("value", ["unknown", "4d", ""])
def test_invalid_presentation_fails_closed(value):
    with pytest.raises(ValueError):
        bagheera_companion(presentation=value)


def test_no_self_authorized_action():
    for permission, founder, evidence in (
        (False, True, True), (True, False, True),
        (True, True, False), (True, True, True)
    ):
        verdict = review_bagheera_action(
            requested_permission=permission,
            founder_approved=founder,
            evidence_present=evidence,
        )
        assert verdict["execute"] is False
        assert verdict["founder_final"] is True
        assert (verdict["recommendation"] == "reviewable") == (
            permission and founder and evidence
        )


@pytest.mark.parametrize("movement,state", [
    ("idle", "ready"), ("listen", "listening"),
    ("consider", "thinking"), ("speak", "speaking"),
    ("alert", "paused"),
])
def test_existing_renderer_state_mapping(movement, state):
    profile = bagheera_companion(movement=movement)
    proposal = bagheera_renderer_state(profile, session_approved=True)
    assert proposal["state"] == state
    assert proposal["renderer_owner"] == "smi_source_pixel_motion"
    assert proposal["dispatch"] is False
    assert proposal["runtime_verified"] is False
    assert proposal["asset_authorized"] is False


def test_no_session_visibility_and_reduced_motion_fail_safe():
    profile = bagheera_companion(movement="speak")
    assert bagheera_renderer_state(profile)["state"] == "paused"
    assert bagheera_renderer_state(
        profile, session_approved=True, visible=False
    )["state"] == "paused"
    assert bagheera_renderer_state(
        profile, session_approved=True, reduce_motion=True
    )["state"] == "paused"
