"""Fail-closed, read-only DNS migration inventory checks. No DNS network access or writes."""
from __future__ import annotations

import ipaddress
import json
import sys
from pathlib import Path

REQUIRED_TYPES = {"A", "AAAA", "MX", "TXT"}
PRESERVE_PREFIXES = ("_dmarc", "_domainkey", "autodiscover", "_domainconnect")


def validate(inventory: dict) -> list[str]:
    errors: list[str] = []
    if inventory.get("domain") != "onanypostcode.global":
        errors.append("unexpected domain")
    records = inventory.get("records")
    if not isinstance(records, list) or not records:
        return errors + ["nonempty verified records inventory required"]
    if not inventory.get("source_verified_at") or not inventory.get("source"):
        errors.append("source and verification timestamp required")
    if inventory.get("delegation_approved") is True:
        errors.append("this offline gate cannot authorize delegation")
    seen = set()
    types = set()
    for index, row in enumerate(records):
        if not isinstance(row, dict):
            errors.append(f"record {index} must be object")
            continue
        host, kind, value = row.get("host"), row.get("type"), row.get("value")
        if not all(isinstance(v, str) and v.strip() for v in (host, kind, value)):
            errors.append(f"record {index} incomplete")
            continue
        kind = kind.upper()
        types.add(kind)
        key = (host, kind, value)
        if key in seen:
            errors.append(f"duplicate record {index}")
        seen.add(key)
        if kind in {"A", "AAAA"}:
            try:
                address = ipaddress.ip_address(value)
                if address.version != (4 if kind == "A" else 6):
                    errors.append(f"record {index} address family mismatch")
            except ValueError:
                errors.append(f"record {index} invalid IP address")
    for kind in sorted(REQUIRED_TYPES - types):
        errors.append(f"missing {kind} record inventory")
    hosts = {r.get("host", "").lower() for r in records if isinstance(r, dict)}
    if not any(x == "_dmarc" or x.startswith("_dmarc.") for x in hosts):
        errors.append("DMARC inventory absent")
    if not any("_domainkey" in x for x in hosts):
        errors.append("DKIM inventory absent")
    if not any(x == "autodiscover" or x.startswith("autodiscover.") for x in hosts):
        errors.append("autodiscover inventory absent")
    return errors



def compare_with_verified_baseline(candidate: dict, baseline: dict) -> list[str]:
    """Require exact record-set equality with a separately acquired baseline.

    This compares supplied files only; it cannot authenticate the baseline.
    """
    errors = ["candidate: " + e for e in validate(candidate)]
    errors += ["baseline: " + e for e in validate(baseline)]
    if errors:
        return errors

    def normalized(data):
        return sorted(
            (r["host"].strip().lower().rstrip("."),
             r["type"].strip().upper(),
             r["value"].strip())
            for r in data["records"]
        )
    if normalized(candidate) != normalized(baseline):
        errors.append("candidate records differ from verified baseline; do not delegate")
    return errors


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/oap_dns_inventory_check.py candidate-records.json verified-baseline.json")
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        baseline = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        problems = compare_with_verified_baseline(data, baseline)
    except (OSError, ValueError, TypeError) as exc:
        print(f"FAIL CLOSED: {exc}")
        return 1
    if problems:
        for problem in problems:
            print(f"FAIL CLOSED: {problem}")
        return 1
    print("Supplied inventories match; NOT baseline authenticity, live DNS or delegation approval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
