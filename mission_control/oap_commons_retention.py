"""Bounded OAP Commons retention operator; no scheduler or live credentials.

Run only on a trusted OAP runtime with its existing PostgreSQL connection.
Enable explicitly via OAP_COMMONS_RETENTION_ENABLED=1 and --apply. Does not
contact members, agents, APIs, providers or the public voting system.
"""
from __future__ import annotations

import argparse
import json
import os

from . import oap_commons, oap_commons_governance, postgres_db

MAX_BATCHES = 20
MAX_BATCH_SIZE = 100


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OAP Commons private retention sweep")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--apply", action="store_true")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--max-batches", type=int, default=10)
    args = parser.parse_args(argv)
    if (not 1 <= args.batch_size <= MAX_BATCH_SIZE
        or not 1 <= args.max_batches <= MAX_BATCHES):
        parser.error("batch size must be 1–100 and maximum batches 1–20")
    if args.apply and os.getenv("OAP_COMMONS_RETENTION_ENABLED") != "1":
        print(json.dumps({
            "status": "DENIED", "reason": "explicit_operator_enablement_required",
            "content_erased": 0,
        }))
        return 2
    if not postgres_db.configured():
        print(json.dumps({
            "status": "UNAVAILABLE", "reason": "canonical_postgresql_not_configured",
            "content_erased": 0,
        }))
        return 3
    try:
        due_before = oap_commons_governance.expired_count()
        if args.dry_run:
            print(json.dumps({
                "status": "DRY_RUN", "expired_count": due_before,
                "retention_days": oap_commons.RETENTION_DAYS,
                "content_erased": 0, "scheduler_installed": False,
            }))
            return 0
        total = 0
        for _ in range(args.max_batches):
            result = oap_commons_governance.erase_expired_system(
                limit=args.batch_size,
            )
            removed = int(result["redacted_count"])
            total += removed
            if removed < args.batch_size:
                break
        remaining = oap_commons_governance.expired_count()
        print(json.dumps({
            "status": "CLEAR" if remaining == 0 else "BACKLOG_REMAINS",
            "expired_before": due_before,
            "redacted_count": total, "expired_remaining": remaining,
            "retention_days": oap_commons.RETENTION_DAYS,
            "audit_actor": "OAP_COMMONS_RETENTION_SERVICE",
            "scheduler_installed": False,
        }))
        return 0 if remaining == 0 else 4
    except oap_commons.CommonsUnavailable:
        print(json.dumps({
            "status": "UNAVAILABLE",
            "reason": "commons_retention_database_or_audit_failure",
            "content_erased": None,
        }))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
