from __future__ import annotations

from scripts.validate_truth_ledger import validate_ledger, validate_record


def _green_record() -> dict:
    return {
        "feature_id": "example",
        "scope": "bounded example",
        "status": "GREEN",
        "commit_sha": "a" * 40,
        "image_digest": "sha256:" + "b" * 64,
        "runtime_service": "existing-service",
        "route": "/example",
        "evidence": [
            {"type": "exact_head_ci", "result": "pass"},
            {"type": "deploy_receipt", "result": "proven"},
            {"type": "health_readback", "result": "pass"},
            {"type": "route_acceptance", "result": "pass"},
            {"type": "rollback_or_recovery", "result": "pass"},
        ],
        "missing_gates": [],
    }


def test_green_requires_complete_evidence_chain():
    assert validate_record(_green_record()) == []


def test_green_fails_closed_when_route_acceptance_is_missing():
    record = _green_record()
    record["evidence"] = [
        item for item in record["evidence"] if item["type"] != "route_acceptance"
    ]
    errors = validate_record(record)
    assert any("green_missing_evidence:route_acceptance" in error for error in errors)


def test_green_fails_closed_with_any_missing_gate():
    record = _green_record()
    record["missing_gates"] = ["browser_acceptance"]
    assert "example:green_with_missing_gates" in validate_record(record)


def test_ledger_rejects_duplicate_feature_ids():
    first = _green_record()
    second = _green_record()
    data = {
        "schema_version": 1,
        "mode": "truth",
        "records": [first, second],
    }
    assert "example:duplicate_feature_id" in validate_ledger(data)
