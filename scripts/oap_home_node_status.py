#!/usr/bin/env python3
"""Cross-platform read-only OAP Home Node status."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from mission_control.organism_runtime import runtime_status

STATE_DIR = Path(os.environ.get("OAP_HOME_STATE", Path.home() / ".local" / "state" / "oap-home-node"))
STATE_FILE = STATE_DIR / "workers.json"


def _alive(pid: object) -> bool:
    try:
        if isinstance(pid, bool) or not isinstance(pid, (int, str)):
            return False
        if isinstance(pid, str) and not pid.isdecimal():
            return False
        value = int(pid)
        if value <= 0:
            return False
        os.kill(value, 0)
        return True
    except (TypeError, ValueError, OSError):
        return False


state = {}
try:
    loaded = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    if isinstance(loaded, dict):
        state = loaded
except (OSError, ValueError):
    pass

def _recent_state(updated_at: object, *, now: float | None = None) -> bool:
    """Reject missing, stale, future, or malformed supervisor heartbeats."""
    if isinstance(updated_at, bool) or not isinstance(updated_at, (int, float)):
        return False
    current = time.time() if now is None else now
    return 0 <= current - updated_at <= 15


snapshot = {
    "home_node_process": "running" if _alive(state.get("supervisor_pid")) else "stopped",
    "organism_worker": "running" if _alive(state.get("organism_pid")) else "stopped",
    "inference_worker": "running" if _alive(state.get("inference_pid")) else "stopped",
    "bridge_secret_configured": len(os.environ.get("OAP_HOME_NODE_BRIDGE_SECRET", "")) >= 32,
    "platform": state.get("platform"),
    "revision": state.get("revision"),
    "supervisor_heartbeat_recent": _recent_state(state.get("updated_at")),
    "organism_runtime": runtime_status(),
}
snapshot["device_ready"] = bool(
    snapshot["home_node_process"] == "running"
    and snapshot["organism_worker"] == "running"
    and snapshot["inference_worker"] == "running"
    and snapshot["supervisor_heartbeat_recent"]
    and snapshot["bridge_secret_configured"]
    and snapshot["organism_runtime"].get("ready")
)
print(json.dumps(snapshot, indent=2, sort_keys=True))
