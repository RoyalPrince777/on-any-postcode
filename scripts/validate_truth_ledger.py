#!/usr/bin/env python3
"""Validate the canonical OAP Truth Ledger.

Fail closed: malformed records or unsupported Green claims return non-zero.
This validator does not mutate production or external systems.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "deploy" / "oap-truth-ledger.json"
STATUSES = {"GREEN", "PURPLE", "RED", "UNKNOWN"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
GREEN_EVIDENCE = {
    "exact_head_ci",
    "deploy_receipt",
    "health_readback",
    "route_acceptance",
    "rollback_or_recovery",
}


def validate_record(record: dict) -> list[str]:
    errors: list[str] = []
    feature_id = str(record.get("feature_id") or "").strip()
    if not feature_id:
        errors.append("feature_id_missing")

    status = str(record.get("status") or "")
    if status not in STATUSES:
        errors.append(f"{feature_id or 'record'}:invalid_status")

    sha = record.get("commit_sha")
    if sha is not None and not SHA_RE.fullmatch(str(sha)):
        errors.append(f"{feature_id or 'record'}:invalid_commit_sha")

    digest = record.get("image_digest")
    if digest is not None and not DIGEST_RE.fullmatch(str(digest)):
        errors.append(f"{feature_id or 'record'}:invalid_image_digest")

    evidence = record.get("evidence")
    if not isinstance(evidence, list):
        errors.append(f"{feature_id or 'record'}:evidence_not_list")
        evidence = []

    evidence_types = {
        str(item.get("type"))
        for item in evidence
        if isinstance(item, dict) and item.get("result") in {"pass", "present", "proven"}
    }

    missing_gates = record.get("missing_gates")
    if not isinstance(missing_gates, list):
        errors.append(f"{feature_id or 'record'}:missing_gates_not_list")
        missing_gates = []

    if status == "GREEN":
        if missing_gates:
            errors.append(f"{feature_id}:green_with_missing_gates")
        absent = sorted(GREEN_EVIDENCE - evidence_types)
        if absent:
            errors.append(f"{feature_id}:green_missing_evidence:{','.join(absent)}")
        if not record.get("runtime_service"):
            errors.append(f"{feature_id}:green_without_runtime_service")
        if not record.get("commit_sha"):
            errors.append(f"{feature_id}:green_without_commit_sha")

    return errors


def validate_ledger(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("unsupported_schema_version")
    if data.get("mode") != "truth":
        errors.append("mode_must_be_truth")

    records = data.get("records")
    if not isinstance(records, list) or not records:
        return errors + ["records_missing_or_empty"]

    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            errors.append("record_not_object")
            continue
        feature_id = str(record.get("feature_id") or "")
        if feature_id in seen and feature_id:
            errors.append(f"{feature_id}:duplicate_feature_id")
        seen.add(feature_id)
        errors.extend(validate_record(record))
    return errors


def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    errors = validate_ledger(data)
    result = {
        "component": "OAP Truth Ledger",
        "mode": "truth",
        "valid": not errors,
        "record_count": len(data.get("records", [])) if isinstance(data, dict) else 0,
        "errors": errors,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
