#!/usr/bin/env python3
"""Cross-platform read-only OAP Home Node status."""
from __future__ import annotations

import json
import os
import socket
from pathlib import Path

from mission_control.organism_runtime import runtime_status, worker_execution_evidence

STATE_DIR = Path(os.environ.get("OAP_HOME_STATE", Path.home() / ".local" / "state" / "oap-home-node"))
STATE_FILE = STATE_DIR / "workers.json"


def _alive(pid: object) -> bool:
    try:
        value = int(pid)
        if value <= 0:
            return False
        os.kill(value, 0)
        return True
    except (TypeError, ValueError, OSError):
        return False


state = {}
try:
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
except (OSError, ValueError):
    pass

snapshot = {
    "home_node_process": "running" if _alive(state.get("supervisor_pid")) else "stopped",
    "organism_worker": "running" if _alive(state.get("organism_pid")) else "stopped",
    "inference_worker": "running" if _alive(state.get("inference_pid")) else "stopped",
    "bridge_secret_configured": len(os.environ.get("OAP_HOME_NODE_BRIDGE_SECRET", "")) >= 32,
    "platform": state.get("platform"),
    "revision": state.get("revision"),
    "organism_runtime": runtime_status(),
}
organism_id = os.environ.get("OAP_WORKER_ID", "").strip()[:120]
if not organism_id and snapshot["organism_worker"] == "running":
    organism_id = f"{socket.gethostname()}:{state.get('organism_pid')}"[:120]
snapshot["organism_execution_evidence"] = worker_execution_evidence(
    organism_id, str(state.get("revision") or "")
)
snapshot["device_ready"] = bool(
    snapshot["home_node_process"] == "running"
    and snapshot["organism_worker"] == "running"
    and snapshot["inference_worker"] == "running"
    and snapshot["bridge_secret_configured"]
    and snapshot["organism_runtime"].get("ready")
    and snapshot["organism_execution_evidence"].get("job_receipt_verified")
)
print(json.dumps(snapshot, indent=2, sort_keys=True))
