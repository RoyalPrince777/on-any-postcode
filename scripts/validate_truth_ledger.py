#!/usr/bin/env python3
"""Validate the canonical OAP Truth Ledger v2.

The ledger is append-only for evidence. Status is derived from evidence and cannot
be asserted directly. Unsupported Green claims therefore have no writable field.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "deploy" / "oap-truth-ledger.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PASS_RESULTS = {"pass", "present", "proven"}
GREEN_EVIDENCE = {
    "exact_head_ci",
    "deploy_receipt",
    "health_readback",
    "route_acceptance",
    "rollback_or_recovery",
}


def _valid_sha(value: object) -> bool:
    return isinstance(value, str) and bool(SHA_RE.fullmatch(value))


def derive_status(feature: dict, events: list[dict]) -> tuple[str, list[str]]:
    feature_id = feature["feature_id"]
    commit_sha = feature["commit_sha"]
    applicable = [
        e for e in events
        if e.get("feature_id") == feature_id
        and e.get("commit_sha") == commit_sha
        and e.get("result") in PASS_RESULTS
    ]
    types = {str(e.get("type")) for e in applicable}
    required = set(feature.get("required_gates") or [])
    missing = sorted(required - types)

    if any(e.get("result") == "failed" for e in events if e.get("feature_id") == feature_id):
        return "RED", missing
    if not applicable:
        return "UNKNOWN", missing
    if not missing and GREEN_EVIDENCE.issubset(types) and feature.get("runtime_service"):
        return "GREEN", []
    return "PURPLE", missing


def validate_ledger(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 2:
        errors.append("unsupported_schema_version")
    if data.get("mode") != "truth":
        errors.append("mode_must_be_truth")

    derivation = data.get("derivation") or {}
    if derivation.get("status_is_computed") is not True:
        errors.append("status_must_be_computed")
    if derivation.get("append_only_evidence") is not True:
        errors.append("evidence_must_be_append_only")

    features = data.get("features")
    events = data.get("evidence_events")
    if not isinstance(features, list) or not features:
        errors.append("features_missing_or_empty")
        return errors
    if not isinstance(events, list):
        errors.append("evidence_events_not_list")
        return errors

    feature_ids: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            errors.append("feature_not_object")
            continue
        feature_id = str(feature.get("feature_id") or "")
        if not feature_id:
            errors.append("feature_id_missing")
            continue
        if feature_id in feature_ids:
            errors.append(f"{feature_id}:duplicate_feature_id")
        feature_ids.add(feature_id)
        if "status" in feature:
            errors.append(f"{feature_id}:manual_status_forbidden")
        if not _valid_sha(feature.get("commit_sha")):
            errors.append(f"{feature_id}:invalid_commit_sha")
        digest = feature.get("image_digest")
        if digest is not None and not (
            isinstance(digest, str) and DIGEST_RE.fullmatch(digest)
        ):
            errors.append(f"{feature_id}:invalid_image_digest")
        gates = feature.get("required_gates")
        if not isinstance(gates, list) or not gates:
            errors.append(f"{feature_id}:required_gates_missing")

    evidence_ids: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            errors.append("evidence_event_not_object")
            continue
        evidence_id = str(event.get("evidence_id") or "")
        if not evidence_id:
            errors.append("evidence_id_missing")
        elif evidence_id in evidence_ids:
            errors.append(f"{evidence_id}:duplicate_evidence_id")
        evidence_ids.add(evidence_id)
        if event.get("feature_id") not in feature_ids:
            errors.append(f"{evidence_id or 'event'}:unknown_feature_id")
        if not _valid_sha(event.get("commit_sha")):
            errors.append(f"{evidence_id or 'event'}:invalid_commit_sha")
        for field in ("type", "result", "location", "producer", "authority", "created_at"):
            if not str(event.get(field) or "").strip():
                errors.append(f"{evidence_id or 'event'}:{field}_missing")

    return errors


def snapshot(data: dict) -> dict[str, object]:
    events = data["evidence_events"]
    derived = []
    for feature in data["features"]:
        status, missing = derive_status(feature, events)
        derived.append({
            "feature_id": feature["feature_id"],
            "commit_sha": feature["commit_sha"],
            "status": status,
            "missing_gates": missing,
        })
    return {
        "component": "OAP Truth Ledger",
        "mode": "truth",
        "derived": derived,
    }


def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    errors = validate_ledger(data)
    result = {
        **snapshot(data),
        "valid": not errors,
        "feature_count": len(data.get("features", [])),
        "evidence_event_count": len(data.get("evidence_events", [])),
        "errors": errors,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
