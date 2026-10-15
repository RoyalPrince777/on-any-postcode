#!/usr/bin/env python3
"""Fail-closed, offline validation of OAP Host candidate evidence receipts.

This checks receipt structure and expiry, NOT whether a remote host is healthy.
It cannot authorise cutover, and must never be represented as live host proof.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

MANDATORY = frozenset({"identity", "network", "runtime", "data", "trust", "dependencies", "recovery", "cutover"})
MAX_AGE = dt.timedelta(minutes=30)


def assess(document: object, *, now: dt.datetime | None = None) -> dict[str, object]:
    now = now or dt.datetime.now(dt.timezone.utc)
    errors: list[str] = []
    if not isinstance(document, dict):
        return {"ready": False, "structure_valid": False, "live_verified": False, "cutover_authorised": False, "errors": ["receipt document must be an object"]}
    receipts = document.get("receipts")
    if not isinstance(receipts, list):
        return {"ready": False, "structure_valid": False, "live_verified": False, "cutover_authorised": False, "errors": ["receipts must be a list"]}
    seen: set[str] = set()
    common_incident: str | None = None
    common_host: str | None = None
    for i, receipt in enumerate(receipts):
        if not isinstance(receipt, dict):
            errors.append(f"receipt {i}: not an object")
            continue
        check = receipt.get("check_id")
        if not isinstance(check, str) or check not in MANDATORY:
            errors.append(f"receipt {i}: unknown check_id")
            continue
        if check in seen:
            errors.append(f"receipt {i}: duplicate check_id {check}")
        seen.add(check)
        for key in ("incident_id", "host_id", "evidence_ref", "operator"):
            value = receipt.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"receipt {i}: missing {key}")
        incident = receipt.get("incident_id")
        host = receipt.get("host_id")
        if common_incident is None:
            common_incident = incident
        elif incident != common_incident:
            errors.append(f"receipt {i}: mixed incident_id")
        if common_host is None:
            common_host = host
        elif host != common_host:
            errors.append(f"receipt {i}: mixed host_id")
        if receipt.get("result") != "PASS":
            errors.append(f"receipt {i}: not PASS")
        try:
            raw = receipt["observed_at"]
            if not isinstance(raw, str):
                raise ValueError("not a timestamp")
            timestamp = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if timestamp.tzinfo is None or not dt.timedelta(0) <= now - timestamp <= MAX_AGE:
                raise ValueError("stale, future or timezone-naive")
        except (KeyError, TypeError, ValueError):
            errors.append(f"receipt {i}: invalid or stale observed_at")
    missing = MANDATORY - seen
    if missing:
        errors.append("missing checks: " + ", ".join(sorted(missing)))
    # Offline validation cannot prove the authenticity of external evidence or
    # approve a production cutover, regardless of the receipt contents.
    return {"ready": False, "structure_valid": not errors, "live_verified": False,
            "cutover_authorised": False, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipts", type=Path)
    args = parser.parse_args()
    result = assess(json.loads(args.receipts.read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["structure_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
