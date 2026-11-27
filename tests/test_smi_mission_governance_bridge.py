"""Fail-closed regression checks for the advisory mission governance bridge."""
from oap.smi.mission_governance_bridge import review_mission_candidates


class _Registry:
    def passport(self, agent_id):
        return None


def test_unknown_protocol_rejected_without_registry_lookup():
    result = review_mission_candidates("mission", "unknown", _Registry())
    assert result["status"] == "REJECTED_INVALID_RECOMMENDATION"
    assert result["all_eligible"] is False
    assert result["grants_permissions"] is False
    assert result["agent_execution_verified"] is False


def test_unresolved_passports_fail_closed():
    result = review_mission_candidates("mission", "recovery", _Registry())
    assert result["status"] == "REJECTED_INELIGIBLE_CANDIDATES"
    assert result["all_eligible"] is False
    assert result["candidates"]["Fox"]["reason"] == "PASSPORT_ID_UNRESOLVED"
    assert result["guardian_review_verified"] is False
    assert result["hrm_audit_verified"] is False
    assert result["founder_final_required"] is True


def test_invalid_depth_rejected():
    result = review_mission_candidates("mission", "recovery", _Registry(), depth="INVALID")
    assert result["status"] == "REJECTED_INVALID_RECOMMENDATION"
    assert result["candidates"] == {}
