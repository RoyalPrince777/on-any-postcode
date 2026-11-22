#!/usr/bin/env python3
"""Start one local OAP service: signed-in HQ on 5000, public discovery on 5052."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=("hq", "public"))
    args = parser.parse_args()
    port = 5000 if args.role == "hq" else 5052
    environment = dict(os.environ, OAP_LOCAL_SERVICE_ROLE=args.role, OAP_LOCAL_MODE="true")
    os.chdir(Path(__file__).resolve().parents[1])
    os.execvpe(sys.executable, [
        sys.executable, "-m", "gunicorn", "app:app",
        "--bind", f"127.0.0.1:{port}", "--workers", "1", "--threads", "4",
        "--timeout", "120",
    ], environment)


if __name__ == "__main__":
    main()
