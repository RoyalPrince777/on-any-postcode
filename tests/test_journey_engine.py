from __future__ import annotations

import pytest

from mission_control import journey_engine


def test_journey_engine_keeps_transport_domains_separate():
    state = journey_engine.status()
    assert state["ride_modes"] == ["car", "e-bike"]
    assert state["network_transport_modes"] == ["bus", "rail", "metro", "tram", "ferry", "coach"]
    assert state["map_modes"] == ["walk", "bicycle"]
    assert state["truth_states"] == ["SCHEDULED", "PREDICTED", "OBSERVED"]
    assert state["gateway_levels"] == [
        "DATA_AVAILABLE",
        "PLANNING_AVAILABLE",
        "ACTION_AVAILABLE",
        "ACTION_AUTHORISED",
    ]
    assert state["execution_authorised"] is False
    assert state["payment_authorised"] is False


def test_scheduled_observation_is_not_silently_live():
    observation = journey_engine.transport_observation(
        truth_state="scheduled",
        source="operator timetable",
        observed_at="2026-10-04T05:00:00+01:00",
        freshness="fresh",
        confidence=100,
    )
    assert observation["truth_state"] == "SCHEDULED"
    assert observation["live_claim_allowed"] is False


def test_stale_observed_state_cannot_claim_live():
    observation = journey_engine.transport_observation(
        truth_state="OBSERVED",
        source="vehicle telemetry",
        observed_at="2026-10-04T04:00:00+01:00",
        freshness="stale",
        confidence=96,
    )
    assert observation["live_claim_allowed"] is False


def test_multimodal_journey_composes_without_granting_execution():
    walk_obs = journey_engine.transport_observation(
        truth_state="OBSERVED",
        source="OAP route engine",
        observed_at="2026-10-04T05:00:00+01:00",
        freshness="fresh",
        confidence=94,
    )
    bus_obs = journey_engine.transport_observation(
        truth_state="PREDICTED",
        source="operator feed",
        observed_at="2026-10-04T05:01:00+01:00",
        freshness="fresh",
        confidence=88,
    )
    journey = journey_engine.compose_journey(
        origin="A",
        destination="C",
        legs=[
            journey_engine.journey_leg(
                mode="walk", origin="A", destination="B",
                observation=walk_obs, duration_minutes=6,
            ),
            journey_engine.journey_leg(
                mode="bus", origin="B", destination="C",
                observation=bus_obs, duration_minutes=20,
                accessibility="step-free boarding",
            ),
        ],
    )
    assert [leg["mode"] for leg in journey["legs"]] == ["walk", "bus"]
    assert journey["duration_minutes"] == 26
    assert journey["confidence"] == 88
    assert journey["execution_authorised"] is False
    assert journey["payment_authorised"] is False
    assert journey["human_authority_final"] is True


@pytest.mark.parametrize("mode", ["transit", "plane", "scooter"])
def test_unsupported_or_legacy_public_modes_fail_closed(mode):
    observation = journey_engine.transport_observation(
        truth_state="SCHEDULED",
        source="test",
        observed_at="2026-10-04T05:00:00+01:00",
        freshness="fresh",
        confidence=90,
    )
    with pytest.raises(ValueError, match="transport_mode_invalid"):
        journey_engine.journey_leg(
            mode=mode,
            origin="A",
            destination="B",
            observation=observation,
        )
