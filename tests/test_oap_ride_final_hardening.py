# ruff: noqa: I001
from pathlib import Path

from mission_control import link_incoming, oap_ride_split_snapshot


def test_split_snapshot_migration_dry_run_is_bounded():
    state = oap_ride_split_snapshot.init_schema(assume_yes=True, dry_run=True)
    assert state["migration"] == "0009_oap_ride_split_snapshot"
    assert state["tables"] == 1
    assert len(state["checksum"]) == 64


def test_incoming_requires_movement_sources_for_ride_proposals():
    assert "oap_movement_bookings" in link_incoming.REQUIRED_TABLES
    assert "oap_movement_match_proposals" in link_incoming.REQUIRED_TABLES


def test_incoming_query_contains_first_party_journey_projection():
    source = Path("mission_control/link_incoming.py").read_text(encoding="utf-8")
    assert "'incoming_journey'::text" in source
    assert "'Incoming Journey'::text" in source
    assert "p.worker_identity_id=%s" in source
    assert "p.state='PROPOSED'" in source
