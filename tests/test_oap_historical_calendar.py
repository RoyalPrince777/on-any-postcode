"""Bounded tests for OAP historical calendar labels and evidence boundary."""
from datetime import date

from mission_control.oap_historical_calendar import calendar_labels, validate_evidence_record


def test_approved_augustine_and_yawoada():
    labels = calendar_labels(date(2026, 8, 20))
    assert labels["civil_weekday"] == "Thursday"
    assert labels["akan_weekday"] == "Yawoada"
    assert labels["oap_month"] == "AUGUSTINE"
    assert labels["iso_date"] == "2026-08-20"


def test_other_month_names_not_prematurely_approved():
    assert calendar_labels(date(2026, 10, 11))["oap_month"] == "October"


def test_evidence_requires_provenance_and_classification():
    valid = {"kind": "scientific", "claim": "Test claim", "source": "Test source", "uncertainty": "Test limitation"}
    assert validate_evidence_record(valid)
    assert not validate_evidence_record({**valid, "source": ""})
    assert not validate_evidence_record({**valid, "kind": "verified_adam_and_eve"})
