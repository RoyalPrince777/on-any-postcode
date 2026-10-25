#!/usr/bin/env python3
"""Explicit, loopback-only OAP Home V2 web launcher.

Separate from Home Node SMI workers. Never enables Flask debug/reloader or LAN
binding. No network or process is started by importing this module.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    # Refuse unexpected host configuration rather than silently exposing Flask.
    if os.environ.get("OAP_HOME_V2_HOST", "127.0.0.1") != "127.0.0.1":
        raise SystemExit("Home V2 refused: loopback-only host required")
    # Direct `python scripts/...py` execution puts scripts/ on sys.path, not
    # the repository root. Keep both direct and `python -m` launch supported.
    repo_root = str(Path(__file__).resolve().parents[1])
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from app import app
    app.run(host="127.0.0.1", port=5050, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
