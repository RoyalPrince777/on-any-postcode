"""Regression checks for existing OAP accounting anchors and read-only chain verification."""
from dataclasses import replace

from mission_control import oap_blockchain_accounting_anchor as anchor
from mission_control import sika_anchor_chain_verifier as verifier


def record(name, previous):
    return anchor.anchor(
        anchor_id=name,
        jurisdiction="United Kingdom",
        domain="JOURNAL",
        subject_reference="journal-" + name,
        previous_hash=previous,
        evidence_hash="a" * 64,
    )


def test_valid_two_record_chain_with_trusted_tip():
    first = record("one", verifier.ZERO_HASH)
    second = record("two", first.current_hash)
    result = verifier.verify_chain([first, second], expected_tip=second.current_hash)
    assert result.valid is True
    assert result.checked == 2
    assert result.as_dict()["money_movement"] is False


def test_empty_chain_fails_closed():
    assert verifier.verify_chain([]).reason == "empty_chain"


def test_missing_middle_record_fails_closed():
    first = record("one", verifier.ZERO_HASH)
    second = record("two", first.current_hash)
    third = record("three", second.current_hash)
    assert verifier.verify_chain([first, third]).reason == "chain_link_mismatch"


def test_tampering_with_evidence_fails_closed():
    first = record("one", verifier.ZERO_HASH)
    altered = replace(first, evidence_hash="b" * 64)
    assert verifier.verify_chain([altered]).reason == "anchor_hash_mismatch"


def test_duplicate_anchor_id_fails_closed():
    first = record("one", verifier.ZERO_HASH)
    second = record("one", first.current_hash)
    assert verifier.verify_chain([first, second]).reason == "duplicate_anchor_id"


def test_trusted_tip_mismatch_fails_closed():
    first = record("one", verifier.ZERO_HASH)
    assert verifier.verify_chain([first], expected_tip="f" * 64).reason == "trusted_tip_mismatch"


def test_no_money_or_consensus_claims():
    state = verifier.status()
    assert state["money_movement"] is False
    assert state["consensus_proven"] is False
    assert state["source_of_truth"] == "sika_postgresql_journal"
