"""Evidence-gated ISAC master status: no synthetic operational green."""
from datetime import datetime, timezone
from mission_control.isac_master_command import master_isac_status


def test_no_sources_are_not_connected():
    status = master_isac_status({})
    assert status["monitor"]["radio"] == "NOT_CONNECTED"
    assert status["monitor"]["surveillance"]["status"] == "NOT_CONNECTED"
    assert status["incoming"]["world_crisis"]["status"] == "NOT_CONNECTED"
    assert status["intelligence"]["human_rights"]["status"] == "NOT_CONNECTED"
    assert status["continuous_monitoring_verified"] is False
    assert status["gorilla"]["physical_actions_authorized"] is False


def test_radio_needs_both_connection_and_hardware_proof():
    assert master_isac_status({"live_radio_connected": True})["monitor"]["radio"] == "NOT_CONNECTED"
    assert master_isac_status({"hardware_green": True})["monitor"]["radio"] == "NOT_CONNECTED"
    assert master_isac_status({"hardware_green": True, "live_radio_connected": True})["monitor"]["radio"] == "CONNECTED"


def test_external_source_needs_evidence_and_freshness_receipt():
    source = {"verified": True, "operational": True}
    status = master_isac_status({}, crisis_feed=source)
    assert status["incoming"]["world_crisis"]["status"] == "NOT_CONNECTED"
    source["checked_at"] = datetime.now(timezone.utc).isoformat()
    status = master_isac_status({}, crisis_feed=source)
    assert status["incoming"]["world_crisis"]["status"] == "CONNECTED"
    assert status["intelligence"]["event_truth_not_implied_by_source_verification"]


def test_interrupted_source_does_not_claim_live():
    source = {"verified": True, "operational": False, "checked_at": datetime.now(timezone.utc).isoformat()}
    status = master_isac_status({}, surveillance=source)
    assert status["monitor"]["surveillance"]["status"] == "INTERRUPTED"


def test_stale_source_never_claims_connected():
    source = {"verified": True, "operational": True, "checked_at": "2020-01-01T00:00:00Z"}
    assert master_isac_status({}, crisis_feed=source)["incoming"]["world_crisis"]["status"] == "STALE"
