#!/usr/bin/env python3
"""Explicit, loopback-only OAP Home V2 web launcher.

Separate from Home Node SMI workers. Never enables Flask debug/reloader or LAN
binding. No network or process is started by importing this module.
"""
from __future__ import annotations

import os


def main() -> None:
    # Refuse unexpected host configuration rather than silently exposing Flask.
    if os.environ.get("OAP_HOME_V2_HOST", "127.0.0.1") != "127.0.0.1":
        raise SystemExit("Home V2 refused: loopback-only host required")
    from app import app
    app.run(host="127.0.0.1", port=5050, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
