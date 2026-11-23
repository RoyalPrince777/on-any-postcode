"""Owner-initiated KORADASO public web crawling; never run at Flask startup."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mission_control.koradaso_public_crawler import (  # noqa: E402
    CrawlDenied,
    crawl_public_seed,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded first-party KORADASO crawler")
    parser.add_argument("--seed", required=True, help="Owner-approved HTTPS public URL")
    parser.add_argument("--db", required=True, type=Path, help="OAP-owned SQLite index")
    parser.add_argument("--max-pages", type=int, default=3, choices=range(1, 6),
                        metavar="{1..5}")
    args = parser.parse_args()
    try:
        result = crawl_public_seed(args.seed, args.db, max_pages=args.max_pages)
    except CrawlDenied as exc:
        print(json.dumps({"indexed": 0, "error": str(exc), "blocked": True}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
