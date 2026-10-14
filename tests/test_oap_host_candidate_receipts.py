from __future__ import annotations

import datetime as dt

from scripts.oap_host_candidate_receipts import MANDATORY, assess

NOW = dt.datetime(2026, 10, 14, 15, 0, tzinfo=dt.UTC)


def valid_receipts():
    return {"receipts": [
        {"incident_id": "inc-1", "host_id": "candidate-1", "check_id": check,
         "observed_at": NOW.isoformat(), "result": "PASS",
         "evidence_ref": "evidence/" + check, "operator": "authorised-operator"}
        for check in sorted(MANDATORY)
    ]}


def test_all_receipts_cannot_authorise_cutover_without_live_proof():
    result = assess(valid_receipts(), now=NOW)
    assert result["structure_valid"] is True
    assert result["ready"] is False
    assert result["live_verified"] is False
    assert result["cutover_authorised"] is False


def test_missing_receipt_is_blocked():
    doc = valid_receipts()
    doc["receipts"].pop()
    result = assess(doc, now=NOW)
    assert result["structure_valid"] is False
    assert "missing checks:" in " ".join(result["errors"])


def test_duplicate_receipt_is_blocked():
    doc = valid_receipts()
    doc["receipts"].append(doc["receipts"][0].copy())
    assert assess(doc, now=NOW)["structure_valid"] is False


def test_stale_receipt_is_blocked():
    doc = valid_receipts()
    doc["receipts"][0]["observed_at"] = (NOW - dt.timedelta(hours=2)).isoformat()
    assert assess(doc, now=NOW)["structure_valid"] is False


def test_mixed_host_is_blocked():
    doc = valid_receipts()
    doc["receipts"][0]["host_id"] = "other-host"
    assert assess(doc, now=NOW)["structure_valid"] is False


def test_failed_dependency_is_blocked():
    doc = valid_receipts()
    next(r for r in doc["receipts"] if r["check_id"] == "dependencies")["result"] = "FAIL"
    assert assess(doc, now=NOW)["structure_valid"] is False


def test_missing_operator_is_blocked():
    doc = valid_receipts()
    doc["receipts"][0]["operator"] = ""
    assert assess(doc, now=NOW)["structure_valid"] is False


def test_non_object_is_blocked():
    assert assess([], now=NOW)["ready"] is False
    assert assess({"receipts": "yes"}, now=NOW)["structure_valid"] is False
