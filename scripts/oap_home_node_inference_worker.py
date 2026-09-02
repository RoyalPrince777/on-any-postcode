#!/usr/bin/env python3
"""Outbound-only OAP Home Node inference worker.

Runs on the Founder-controlled Home Node. It polls the OAP private bridge over
HTTPS, sends each job to local Ollama, then returns only the bounded result.
No inbound port is opened and no third-party AI router is used.
"""
from __future__ import annotations

import json
import os
import sys
import time
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

BASE_URL = os.environ.get("OAP_HOME_NODE_BRIDGE_URL", "https://oap-smi.onrender.com/mission").strip().rstrip("/")
TOKEN = os.environ.get("OAP_HOME_NODE_BRIDGE_SECRET", "").strip()
OLLAMA_URL = os.environ.get("OAP_HOME_NODE_OLLAMA_URL", "http://127.0.0.1:11434/api/chat").strip()
POLL_SECONDS = max(0.5, min(float(os.environ.get("OAP_HOME_NODE_POLL_SECONDS", "1.5")), 30.0))


def _headers() -> dict[str, str]:
    if len(TOKEN) < 32:
        raise RuntimeError("OAP_HOME_NODE_BRIDGE_SECRET must contain at least 32 characters")
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-OAP-Home-Node-Token": TOKEN,
        "User-Agent": "OAP-Home-Node/1",
    }


def _request(url: str, *, method: str = "GET", payload: dict | None = None, timeout: float = 30.0):
    data = None if payload is None else json.dumps(payload).encode()
    req = urlrequest.Request(url, data=data, headers=_headers(), method=method)
    try:
        with urlrequest.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            if not raw:
                return {}, int(response.status)
            return json.loads(raw), int(response.status)
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        body = json.loads(raw) if raw else {}
        return body, int(exc.code)


def _run_local(payload: dict) -> str:
    req = urlrequest.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlrequest.urlopen(req, timeout=120.0) as response:
        body = json.loads(response.read().decode("utf-8", errors="replace"))
    text = str((body.get("message") or {}).get("content", "")).strip() or str(body.get("response", "")).strip()
    if not text:
        raise RuntimeError("local_inference_empty")
    return text[:12000]


def run() -> int:
    _headers()
    print("OAP Home Node inference worker active", flush=True)
    while True:
        try:
            job, status = _request(f"{BASE_URL}/home-node/jobs/next", timeout=20.0)
            if status == 204 or job.get("status") == "idle":
                time.sleep(POLL_SECONDS)
                continue
            if status != 200 or job.get("status") != "job":
                time.sleep(min(POLL_SECONDS * 2, 10.0))
                continue
            job_id = str(job.get("job_id", ""))
            payload = job.get("payload")
            if not job_id or not isinstance(payload, dict):
                continue
            try:
                result = _run_local(payload)
                completion = {"result": result}
            except Exception as exc:  # worker reports bounded failure; server decides fallback policy
                completion = {"error": type(exc).__name__[:80]}
            _request(
                f"{BASE_URL}/home-node/jobs/{job_id}/complete",
                method="POST",
                payload=completion,
                timeout=30.0,
            )
        except (URLError, TimeoutError, OSError, json.JSONDecodeError):
            time.sleep(min(POLL_SECONDS * 2, 10.0))


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except KeyboardInterrupt:
        raise SystemExit(0)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
