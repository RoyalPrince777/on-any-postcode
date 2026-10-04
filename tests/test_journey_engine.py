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


def _sample_journey():
    walk_obs = journey_engine.transport_observation(
        truth_state="OBSERVED",
        source="OAP route engine",
        observed_at="2026-10-04T05:00:00+01:00",
        freshness="fresh",
        confidence=95,
    )
    rail_obs = journey_engine.transport_observation(
        truth_state="PREDICTED",
        source="operator feed",
        observed_at="2026-10-04T05:01:00+01:00",
        freshness="fresh",
        confidence=89,
    )
    return journey_engine.compose_journey(
        origin="A",
        destination="C",
        legs=[
            journey_engine.journey_leg(
                mode="walk", origin="A", destination="B",
                observation=walk_obs, duration_minutes=5,
            ),
            journey_engine.journey_leg(
                mode="rail", origin="B", destination="C",
                observation=rail_obs, duration_minutes=22,
            ),
        ],
    )


def test_observed_fresh_disruption_propagates_only_to_matching_modes():
    journey = _sample_journey()
    event = journey_engine.disruption_event(
        event_type="line suspended",
        affected_modes=["rail"],
        observation=journey_engine.transport_observation(
            truth_state="OBSERVED",
            source="operator incident feed",
            observed_at="2026-10-04T05:02:00+01:00",
            freshness="fresh",
            confidence=97,
        ),
        severity=90,
        evidence_ids=["ev-rail-001"],
    )
    assessment = journey_engine.assess_disruptions(journey=journey, events=[event])
    assert assessment["impact_state"] == "IMPACT_CONFIRMED"
    assert assessment["affected_leg_ids"] == [journey["legs"][1]["leg_id"]]
    assert assessment["evidence_ids"] == ["ev-rail-001"]
    assert assessment["execution_authorised"] is False


def test_stale_disruption_degrades_to_unknown_not_confirmed():
    journey = _sample_journey()
    event = journey_engine.disruption_event(
        event_type="possible suspension",
        affected_modes=["rail"],
        observation=journey_engine.transport_observation(
            truth_state="OBSERVED",
            source="operator incident feed",
            observed_at="2026-10-04T03:00:00+01:00",
            freshness="stale",
            confidence=99,
        ),
        severity=80,
    )
    assessment = journey_engine.assess_disruptions(journey=journey, events=[event])
    assert assessment["impact_state"] == "UNKNOWN"


def test_recovery_plan_uses_supplied_alternative_without_auto_execution():
    journey = _sample_journey()
    event = journey_engine.disruption_event(
        event_type="rail blocked",
        affected_modes=["rail"],
        observation=journey_engine.transport_observation(
            truth_state="OBSERVED",
            source="operator incident feed",
            observed_at="2026-10-04T05:02:00+01:00",
            freshness="fresh",
            confidence=96,
        ),
        severity=95,
    )
    assessment = journey_engine.assess_disruptions(journey=journey, events=[event])
    alternative = journey_engine.compose_journey(
        origin="A",
        destination="C",
        legs=[
            journey_engine.journey_leg(
                mode="bus",
                origin="A",
                destination="C",
                observation=journey_engine.transport_observation(
                    truth_state="PREDICTED",
                    source="operator feed",
                    observed_at="2026-10-04T05:03:00+01:00",
                    freshness="fresh",
                    confidence=84,
                ),
                duration_minutes=34,
            )
        ],
    )
    recovery = journey_engine.recovery_plan(
        journey=journey,
        assessment=assessment,
        alternatives=[alternative],
    )
    assert recovery["recovery_state"] == "ALTERNATIVE_AVAILABLE"
    assert recovery["alternative_journey_ids"] == [alternative["journey_id"]]
    assert recovery["automatic_execution"] is False
    assert recovery["payment_action_authorised"] is False


def test_command_center_projection_preserves_evidence_and_authority_boundary():
    journey = _sample_journey()
    event = journey_engine.disruption_event(
        event_type="rail blocked",
        affected_modes=["rail"],
        observation=journey_engine.transport_observation(
            truth_state="PREDICTED",
            source="operator feed",
            observed_at="2026-10-04T05:02:00+01:00",
            freshness="fresh",
            confidence=82,
        ),
        severity=70,
        evidence_ids=["ev-rail-002"],
    )
    assessment = journey_engine.assess_disruptions(journey=journey, events=[event])
    recovery = journey_engine.recovery_plan(
        journey=journey,
        assessment=assessment,
    )
    state = journey_engine.command_center_state(
        journey=journey,
        assessment=assessment,
        recovery=recovery,
    )
    assert state["impact_state"] == "PREDICTED_IMPACT"
    assert state["recovery_state"] == "REPLAN_REQUIRED"
    assert state["evidence_ids"] == ["ev-rail-002"]
    assert "alternatives" in state["actions"]
    assert state["execution_authorised"] is False
    assert state["payment_authorised"] is False


def test_dependency_propagation_is_explicit_and_loop_safe():
    journey = _sample_journey()
    rail_leg = journey["legs"][1]["leg_id"]
    walk_leg = journey["legs"][0]["leg_id"]
    event = journey_engine.disruption_event(
        event_type="rail blocked",
        affected_modes=["rail"],
        observation=journey_engine.transport_observation(
            truth_state="OBSERVED",
            source="operator incident feed",
            observed_at="2026-10-04T05:02:00+01:00",
            freshness="fresh",
            confidence=98,
        ),
        severity=95,
        evidence_ids=["ev-rail-003"],
    )
    assessment = journey_engine.assess_disruptions(
        journey=journey,
        events=[event],
        dependencies=[
            {
                "from_leg_id": rail_leg,
                "to_leg_id": walk_leg,
                "type": "feeds",
                "evidence_id": "dep-001",
            },
            {
                "from_leg_id": walk_leg,
                "to_leg_id": rail_leg,
                "type": "connected_to",
                "evidence_id": "dep-002",
            },
        ],
    )
    assert set(assessment["affected_leg_ids"]) == {walk_leg, rail_leg}
    impact = assessment["impacts"][0]
    assert impact["direct_leg_ids"] == [rail_leg]
    assert impact["dependency_propagated_leg_ids"] == [walk_leg]
    assert "dep-001" in assessment["evidence_ids"]
    assert assessment["execution_authorised"] is False


def test_dependency_without_evidence_or_declared_edge_does_not_spread_impact():
    journey = _sample_journey()
    event = journey_engine.disruption_event(
        event_type="rail blocked",
        affected_modes=["rail"],
        observation=journey_engine.transport_observation(
            truth_state="OBSERVED",
            source="operator incident feed",
            observed_at="2026-10-04T05:02:00+01:00",
            freshness="fresh",
            confidence=98,
        ),
        severity=95,
    )
    assessment = journey_engine.assess_disruptions(journey=journey, events=[event])
    assert assessment["affected_leg_ids"] == [journey["legs"][1]["leg_id"]]
