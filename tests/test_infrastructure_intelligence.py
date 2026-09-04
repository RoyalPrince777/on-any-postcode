from __future__ import annotations

from mission_control import infrastructure_intelligence, live_signals, technology_intelligence


def test_infrastructure_intelligence_is_first_party_bounded_and_not_a_new_world():
    status = infrastructure_intelligence.infrastructure_intelligence_status()

    assert status["name"] == "Infrastructure Intelligence"
    assert status["parent"] == "Technology Intelligence"
    assert status["architecture_ready"] is True
    assert status["mode"] == "first_party_evidence_review"
    assert status["demo_mode"] is False
    assert status["focus_count"] == 10
    assert status["brain_count"] == 0
    assert status["intelligence_world_count_added"] == 0
    assert status["first_party_policy"]["owner"] == "ON ANY POSTCODE"
    assert status["first_party_policy"]["external_identity_allowed"] is False
    assert status["first_party_policy"]["external_authority_allowed"] is False
    assert status["independent_execute"] is False
    assert status["independent_approval"] is False
    assert status["human_authority_final"] is True


def test_infrastructure_review_uses_canonical_signals_and_fails_unknowns_to_warning():
    projection = {
        "modules": [
            {"id": "maps", "state": "healthy", "status": "Runtime verified", "data": "Observed"},
            {"id": "weather", "state": "degraded", "status": "Configured", "data": "Pending"},
            {"id": "esim", "state": "degraded", "status": "OAP carrier capability required", "data": "Pending"},
            {"id": "connectivity", "state": "degraded", "status": "Not connected", "data": "No evidence"},
        ]
    }

    result = infrastructure_intelligence.review(projection)
    focuses = {item["id"]: item for item in result["focuses"]}

    assert result["signal"]["id"] == "warning"
    assert focuses["maps"]["signal"]["id"] == "healthy"
    assert focuses["network"]["signal"]["id"] == "offline"
    assert focuses["storage"]["signal"]["id"] == "warning"
    assert result["can_execute"] is False
    assert result["can_approve"] is False
    assert result["war_room_feed"]["decision_authority"] is False
    assert live_signals.validate_signal_language()["passed"] is True


def test_technology_intelligence_exposes_infrastructure_child_without_new_brain():
    status = technology_intelligence.technology_intelligence_status()
    section_ids = {item["id"] for item in status["sections"]}
    infrastructure = status["infrastructure"]

    assert status["architecture_passed"] is True
    assert "infrastructure" in section_ids
    assert infrastructure["name"] == "Infrastructure Intelligence"
    assert infrastructure["brain_count"] == 0
    assert infrastructure["intelligence_world_count_added"] == 0
    assert status["infrastructure_execution_authority"] is False
    assert status["infrastructure_operator_claim"] is False
