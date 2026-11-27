#!/usr/bin/env python3
"""Start the original SMI Flask app on private loopback 5000 after local checks.

Default is read-only preflight. Never chooses or promotes a database.
Run from the existing repository with its approved private environment loaded.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
EXPECTED_SOCKET = Path.home() / ".local/state/oap-postgres/socket"

def local_target(config):
    return (
        config.get("dbname") == "smi_local"
        and config.get("host") == str(EXPECTED_SOCKET)
        and str(config.get("port", "5432")) == "5432"
        and not config.get("hostaddr")
        and not config.get("service")
        and not os.getenv("PGHOSTADDR")
        and not os.getenv("PGSERVICE")
    )

def port_available():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 5000))
        return True
    except OSError:
        return False

def preflight():
    from psycopg.conninfo import conninfo_to_dict
    from mission_control import postgres_db, founder_local_auth
    result = {"port": 5000, "bind": "127.0.0.1", "database_selected_local": False,
              "database_ready": False, "founder_auth_bound": False,
              "session_secret_configured": False, "port_available": False,
              "ready_to_attempt_start": False, "public_update": "locked"}
    try:
        config = conninfo_to_dict(postgres_db._database_url())
        result["database_selected_local"] = (
            postgres_db.database_authority() == "primary" and local_target(config)
        )
    except Exception:
        result["reason"] = "database_configuration_invalid"
        return result
    if not result["database_selected_local"]:
        result["reason"] = "existing_authority_not_approved_local_socket"
        return result
    result["database_ready"] = postgres_db.postgres_status().get("initialized") is True
    if result["database_ready"]:
        result["founder_auth_bound"] = founder_local_auth.bound()
    result["session_secret_configured"] = len(os.getenv("OAP_SESSION_SECRET", "").strip()) >= 32
    result["port_available"] = port_available()
    result["ready_to_attempt_start"] = all(result[k] for k in (
        "database_selected_local", "database_ready", "founder_auth_bound",
        "session_secret_configured", "port_available"))
    if not result["ready_to_attempt_start"]:
        result["reason"] = "one_or_more_preflight_checks_failed"
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", action="store_true",
                        help="Explicitly start the existing private local web app")
    args = parser.parse_args()
    try:
        result = preflight()
    except Exception as exc:
        print(json.dumps({"ready_to_attempt_start": False,
                          "reason": type(exc).__name__}))
        return 2
    print(json.dumps(result, indent=2), flush=True)
    if not result["ready_to_attempt_start"]:
        return 2
    if not args.start:
        return 0
    # These flags apply only to this loopback web process, not other services.
    os.environ["OAP_LOCAL_MODE"] = "true"
    os.environ["OAP_HOME_NODE_BRIDGE_ENABLED"] = "0"
    os.environ["OAP_INFERENCE_COMPATIBILITY_FALLBACK"] = "0"
    os.chdir(ROOT)
    from app import app
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
