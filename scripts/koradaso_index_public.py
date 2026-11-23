"""Import reviewed public HTTPS page metadata into the local KORADASO index.

Input: JSON Lines records, each with url/title/description.
No fetching, crawling, private-page indexing, network calls or auto-discovery.
Run manually by the index owner; not part of Flask startup.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mission_control.koradaso_web_index import ingest_public_page  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Curated KORADASO public web index importer")
    parser.add_argument("--source", required=True, type=Path, help="Reviewed JSONL of public page metadata")
    parser.add_argument("--db", required=True, type=Path, help="First-party local SQLite index")
    args = parser.parse_args()

    if not args.source.is_file() or args.source.resolve() == args.db.resolve():
        parser.error("source must be a separate existing JSONL file")

    rows = []
    with args.source.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if number > 1000:
                parser.error("maximum 1000 curated records per import")
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ValueError("expected object")
                item = {
                    "url": payload["url"],
                    "title": payload["title"],
                    "description": payload.get("description", ""),
                }
                from mission_control.koradaso_web_index import _safe_public_url
                if not _safe_public_url(item["url"]) or not isinstance(item["title"], str):
                    raise ValueError("unsafe URL or title")
                if not item["title"].strip() or len(item["title"]) > 200:
                    raise ValueError("title length")
                if not isinstance(item["description"], str) or len(item["description"]) > 1200:
                    raise ValueError("description length")
                rows.append(item)
            except (KeyError, ValueError, TypeError, json.JSONDecodeError) as error:
                parser.error(f"invalid record on line {number}: {error}")

    for item in rows:
        ingest_public_page(args.db, **item)
    print(f"KORADASO indexed {len(rows)} curated public-page records locally.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
