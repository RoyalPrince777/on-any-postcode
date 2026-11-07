"""Explicit bounded public seed crawl. Never runs on Flask startup.

Usage:
  python scripts/koradaso_crawl_seeds.py --source reviewed-urls.txt --db index.sqlite3 --execute

Only reviewed HTTPS seeds; at most 10 URLs per invocation; one request at a
time; robots.txt must explicitly be retrievable. No automatic link traversal.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mission_control.koradaso_crawler import CrawlerRejected, crawl_seed  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded first-party KORADASO crawler")
    parser.add_argument("--source", required=True, type=Path, help="Reviewed UTF-8 HTTPS URLs, one per line")
    parser.add_argument("--db", required=True, type=Path, help="Local first-party SQLite index")
    parser.add_argument("--execute", action="store_true", help="Explicit consent to network fetching")
    args = parser.parse_args()
    if not args.execute:
        parser.error("pass --execute to allow bounded network fetching")
    if not args.source.is_file() or args.source.resolve() == args.db.resolve():
        parser.error("source must be a separate existing seed file")
    urls = [line.strip() for line in args.source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not urls or len(urls) > 10:
        parser.error("supply 1 to 10 reviewed public HTTPS seed URLs")
    succeeded = 0
    for position, url in enumerate(urls):
        if position:
            time.sleep(2)
        try:
            result = crawl_seed(url, args.db)
        except CrawlerRejected as error:
            print(f"BLOCKED seed {position + 1}: {error}", file=sys.stderr)
            continue
        succeeded += 1
        print(f"Indexed: {result['url']}")
    print(f"KORADASO: {succeeded}/{len(urls)} public pages indexed")
    return 0 if succeeded == len(urls) else 1


if __name__ == "__main__":
    raise SystemExit(main())
