#!/usr/bin/env python3
"""Cross-platform OAP Home Node supervisor.

Runs the bounded organism worker and outbound-only inference worker together on
Founder-controlled Android/Termux, Linux, macOS, or Windows hosts.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = Path(os.environ.get("OAP_HOME_STATE", Path.home() / ".local" / "state" / "oap-home-node"))
STATE_FILE = STATE_DIR / "workers.json"
REVISION = os.environ.get("OAP_ENV_REVISION", "device-local")[:120]
STOP = False


def _required() -> None:
    db = (
        os.environ.get("OAP_NEON_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or os.environ.get("OAP_DB_SECRET_B64")
        or os.environ.get("OAP_NEON_DATABASE_URL_B64")
    )
    secret = os.environ.get("OAP_HOME_NODE_BRIDGE_SECRET", "")
    if not db:
        raise RuntimeError("Home Node refused: database credential is not configured")
    if len(secret) < 32:
        raise RuntimeError("Home Node refused: bridge secret must contain at least 32 characters")


def _write_state(organism: subprocess.Popen | None, inference: subprocess.Popen | None) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "supervisor_pid": os.getpid(),
        "organism_pid": organism.pid if organism and organism.poll() is None else None,
        "inference_pid": inference.pid if inference and inference.poll() is None else None,
        "revision": REVISION,
        "platform": sys.platform,
        "updated_at": time.time(),
    }
    STATE_FILE.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _spawn_organism() -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-m", "mission_control.organism_worker"], cwd=ROOT)


def _spawn_inference() -> subprocess.Popen:
    return subprocess.Popen([sys.executable, str(ROOT / "scripts" / "oap_home_node_inference_worker.py")], cwd=ROOT)


def _stop(signum: int, frame: object) -> None:
    del signum, frame
    global STOP
    STOP = True


def run() -> int:
    _required()
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    organism = _spawn_organism()
    inference = _spawn_inference()
    _write_state(organism, inference)
    print(json.dumps({"event": "home_node_started", "platform": sys.platform, "revision": REVISION}), flush=True)
    try:
        while not STOP:
            if organism.poll() is not None:
                time.sleep(3)
                organism = _spawn_organism()
            if inference.poll() is not None:
                time.sleep(3)
                inference = _spawn_inference()
            _write_state(organism, inference)
            time.sleep(2)
    finally:
        for child in (organism, inference):
            if child.poll() is None:
                child.terminate()
        for child in (organism, inference):
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
        _write_state(None, None)
        print(json.dumps({"event": "home_node_stopped", "platform": sys.platform}), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
