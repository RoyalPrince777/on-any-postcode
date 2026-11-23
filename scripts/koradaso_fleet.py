"""Explicit local operator CLI for the existing KORADASO crawler queue.

No daemon, web trigger, Flask startup hook, or implicit cron installation.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mission_control.koradaso_crawl_fleet import (  # noqa: E402
    approve_seed, fleet_status, revoke_seed, run_due_once,
)


def main() -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description="KORADASO governed crawl fleet (source gate)")
    parser.add_argument("--state", type=Path, required=True, help="Private queue SQLite path")
    parser.add_argument("--index", type=Path, required=True, help="Existing public index SQLite path")
    sub = parser.add_subparsers(dest="action", required=True)
    approve = sub.add_parser("approve", help="Locally authorise one public HTTPS seed")
    approve.add_argument("--seed", required=True)
    approve.add_argument("--interval-hours", type=int, default=24)
    revoke = sub.add_parser("revoke", help="Disable future claims for a seed")
    revoke.add_argument("--seed", required=True)
    sub.add_parser("run-once", help="Claim and crawl at most one approved due seed")
    sub.add_parser("status", help="Read queue status; never crawls")
    args = parser.parse_args()
    try:
        if args.action == "approve":
            approve_seed(args.state, args.seed, interval_hours=args.interval_hours)
            result = {"status": "approved", "seed": args.seed}
        elif args.action == "revoke":
            revoke_seed(args.state, args.seed)
            result = {"status": "revoked", "seed": args.seed}
        elif args.action == "status":
            result = {"seeds": fleet_status(args.state)}
        else:
            result = run_due_once(args.state, args.index)
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") not in ("crawl_errors", "CrawlDenied", "OSError", "ValueError") else 1


if __name__ == "__main__":
    raise SystemExit(main())
