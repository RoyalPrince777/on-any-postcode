from __future__ import annotations

import argparse
import json

from mission_control import distribution_market_links as links


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Governed Distribution Booking canonical-link migration"
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    if not args.apply:
        result = links.schema_status()
    else:
        result = links.init_link_schema(
            assume_yes=args.yes,
            dry_run=False,
        )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("schema_ready") is True or not args.apply else 1


if __name__ == "__main__":
    raise SystemExit(main())
