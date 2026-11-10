from mission_control import smi_73_signal_field as field


def test_live_health_projection_keeps_unproven_signals_unknown():
    snapshot = {
        "status": "degraded",
        "checks": {
            "permission": True,
            "audit": True,
            "guardian": True,
            "aegis": True,
            "war_room": True,
            "database": True,
            "schema": True,
            "human_authority": True,
            "nexus": True,
            "agent_registry": True,
        },
        "invariants": {
            "human_authority_final": True,
            "execution_locked": True,
        },
        "inference": {"first_party_inference_ready": False},
        "environment": {"revision_present": True},
        "database_reason": None,
    }
    evidence = field.evidence_from_smi_health(snapshot)
    result = field.evaluate(evidence)
    assert result["green_100"] is False
    assert result["seal_777"] == "not_earned"
    assert result["states"]["security.access"] == "proven"
    assert result["states"]["crown.runtime_proof"] == "blocked"
    assert result["states"]["crown.end_to_end_proof"] == "blocked"
    assert result["states"]["crown.recovery_proof"] == "unknown"


def test_live_health_projection_requires_first_party_inference_for_end_to_end():
    snapshot = {
        "status": "green",
        "checks": {
            "permission": True,
            "audit": True,
            "guardian": True,
            "aegis": True,
            "war_room": True,
            "database": True,
            "schema": True,
            "human_authority": True,
            "nexus": True,
            "agent_registry": True,
        },
        "invariants": {
            "human_authority_final": True,
            "execution_locked": True,
        },
        "inference": {"first_party_inference_ready": True},
        "environment": {"revision_present": True},
        "database_reason": None,
    }
    evidence = field.evidence_from_smi_health(snapshot)
    assert evidence["crown.end_to_end_proof"] is True
