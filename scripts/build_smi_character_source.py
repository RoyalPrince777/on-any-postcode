"""Offline CLI: extract approved SMI character layers from reviewed masks.

Example:
  python scripts/build_smi_character_source.py \
    --masks /private/smi-reviewed-masks \
    --output /private/smi-packages/source-v1

Requires the EXACT repository image and seven manual full-canvas L-mode
mask PNGs. Never publishes, generates a substitute or enables animation.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oap.smi.character_source_package import (  # noqa: E402
    SourcePackageError,
    build_source_package,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--masks", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build_source_package(
            ROOT / "static/oap/smi_live_chat_dashboard.jpg",
            args.masks,
            args.output,
        )
    except (OSError, SourcePackageError) as error:
        # Private paths and source bytes must never appear in logs.
        reason = str(error) if isinstance(error, SourcePackageError) else "private_io_failed"
        print("SMI_SOURCE_PACKAGE_BLOCKED: " + reason, file=sys.stderr)
        return 1
    print(
        "SMI_SOURCE_PACKAGE_CREATED: "
        + str(result["layers"])
        + " source-derived layers; motion disabled; human review required"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
