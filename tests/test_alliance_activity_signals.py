"""Bounded tests for 21-check Performance & Activity projection."""
import pytest

from mission_control.alliance_activity_signals import CHECKS_21, project_agent_signals


def test_missing_telemetry_is_not_green():
    result = project_agent_signals("JUNGLE-HATHI-001")
    assert result["signal_count"] == 21
    assert not result["green"]
    assert result["signals"]["monitoring_proof"]["state"] == "unknown"


def test_claim_without_receipt_is_not_proven():
    result = project_agent_signals("fox", {"source_proof": {"state": "proven"}})
    assert result["signals"]["source_proof"]["state"] == "unknown"
    assert not result["green"]


def test_inapplicable_checks_do_not_create_false_green():
    result = project_agent_signals("fox", applicable=set())
    assert not result["green"]
    assert all(v["state"] == "not_applicable" for v in result["signals"].values())


def test_unrecognised_applicability_fails_closed():
    with pytest.raises(ValueError):
        project_agent_signals("fox", applicable={"invented"})


def test_receipts_are_not_automatically_authenticated():
    observations = {k: {"state": "proven", "receipt": "claimed-ref"} for k in CHECKS_21}
    result = project_agent_signals("fox", observations)
    assert result["receipt_authenticity_verified"] is False
    assert result["all_applicable_claimed_proven"] is True
    assert result["green"] is False
    assert result["authority_effect"] == "none"
