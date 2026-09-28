from __future__ import annotations

from scripts.validate_truth_ledger import derive_status, validate_ledger


def _feature() -> dict:
    return {
        "feature_id": "example",
        "scope": "bounded example",
        "commit_sha": "a" * 40,
        "image_digest": "sha256:" + "b" * 64,
        "runtime_service": "existing-service",
        "route": "/example",
        "required_gates": [
            "exact_head_ci",
            "deploy_receipt",
            "health_readback",
            "route_acceptance",
            "rollback_or_recovery",
        ],
    }


def _events() -> list[dict]:
    base = {
        "feature_id": "example",
        "commit_sha": "a" * 40,
        "result": "pass",
        "location": "evidence://example",
        "producer": "ci",
        "authority": "automated",
        "created_at": "2026-09-28T00:00:00Z",
        "supersedes": None,
        "expires_when": "code_or_runtime_changes",
    }
    return [
        {**base, "evidence_id": f"ev-{kind}", "type": kind}
        for kind in (
            "exact_head_ci",
            "deploy_receipt",
            "health_readback",
            "route_acceptance",
            "rollback_or_recovery",
        )
    ]


def test_green_is_derived_only_from_complete_evidence():
    status, missing = derive_status(_feature(), _events())
    assert status == "GREEN"
    assert missing == []


def test_missing_route_acceptance_derives_purple():
    events = [e for e in _events() if e["type"] != "route_acceptance"]
    status, missing = derive_status(_feature(), events)
    assert status == "PURPLE"
    assert missing == ["route_acceptance"]


def test_manual_status_is_forbidden():
    feature = _feature()
    feature["status"] = "GREEN"
    data = {
        "schema_version": 2,
        "mode": "truth",
        "derivation": {"status_is_computed": True, "append_only_evidence": True},
        "features": [feature],
        "evidence_events": _events(),
    }
    assert "example:manual_status_forbidden" in validate_ledger(data)


def test_duplicate_evidence_id_is_rejected():
    events = _events()
    events.append(dict(events[0]))
    data = {
        "schema_version": 2,
        "mode": "truth",
        "derivation": {"status_is_computed": True, "append_only_evidence": True},
        "features": [_feature()],
        "evidence_events": events,
    }
    assert any("duplicate_evidence_id" in e for e in validate_ledger(data))


def test_wrong_commit_evidence_cannot_turn_feature_green():
    events = _events()
    events[0]["commit_sha"] = "c" * 40
    status, missing = derive_status(_feature(), events)
    assert status == "PURPLE"
    assert "exact_head_ci" in missing
