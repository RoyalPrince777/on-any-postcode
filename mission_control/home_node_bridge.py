"""First-party outbound Home Node inference bridge for Personal SMI.

The Home Node never exposes Ollama publicly. Instead it authenticates to OAP over
HTTPS, polls for bounded inference work, executes locally, and returns the result.
Jobs are deliberately ephemeral and held only in process memory; no prompt or
result is persisted by this bridge. HRM remains the canonical memory organ.
"""
from __future__ import annotations

import hmac
import os
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any

_MAX_PENDING = 8
_JOB_TTL_SECONDS = 45.0
_RESULT_WAIT_SECONDS = 20.0


def _shared_secret() -> str:
    return os.environ.get("OAP_HOME_NODE_BRIDGE_SECRET", "").strip()


def configured() -> bool:
    return len(_shared_secret()) >= 32


def authorised(token: str | None) -> bool:
    secret = _shared_secret()
    candidate = str(token or "")
    return len(secret) >= 32 and hmac.compare_digest(candidate, secret)


@dataclass
class _Job:
    job_id: str
    payload: dict[str, Any]
    created_at: float = field(default_factory=time.monotonic)
    claimed: bool = False
    result: str | None = None
    error: str | None = None
    event: threading.Event = field(default_factory=threading.Event)


_LOCK = threading.Lock()
_PENDING: deque[str] = deque()
_JOBS: dict[str, _Job] = {}
_LAST_WORKER_SEEN = 0.0


def _prune_locked(now: float) -> None:
    expired = [
        job_id
        for job_id, job in _JOBS.items()
        if now - job.created_at > _JOB_TTL_SECONDS
    ]
    for job_id in expired:
        job = _JOBS.pop(job_id, None)
        if job is not None and not job.event.is_set():
            job.error = "home_node_job_expired"
            job.event.set()
    if expired:
        alive = set(_JOBS)
        _PENDING.clear()
        _PENDING.extend(job_id for job_id in alive if not _JOBS[job_id].claimed)


def submit_inference(payload: dict[str, Any], *, timeout: float = _RESULT_WAIT_SECONDS) -> str:
    """Queue one bounded inference job and synchronously wait for the Home Node."""
    if not configured():
        raise RuntimeError("home_node_bridge_not_configured")
    if not isinstance(payload, dict) or not payload.get("messages"):
        raise ValueError("invalid_home_node_payload")

    now = time.monotonic()
    with _LOCK:
        _prune_locked(now)
        if len(_PENDING) >= _MAX_PENDING:
            raise RuntimeError("home_node_bridge_busy")
        job = _Job(job_id=str(uuid.uuid4()), payload=payload)
        _JOBS[job.job_id] = job
        _PENDING.append(job.job_id)

    if not job.event.wait(max(0.1, min(float(timeout), _RESULT_WAIT_SECONDS))):
        with _LOCK:
            _JOBS.pop(job.job_id, None)
            try:
                _PENDING.remove(job.job_id)
            except ValueError:
                pass
        raise RuntimeError("home_node_bridge_timeout")

    with _LOCK:
        _JOBS.pop(job.job_id, None)
    if job.error:
        raise RuntimeError(job.error)
    text = str(job.result or "").strip()
    if not text:
        raise RuntimeError("home_node_bridge_empty")
    return text[:12000]


def claim_next() -> dict[str, Any] | None:
    """Claim one job for an authenticated outbound Home Node worker."""
    global _LAST_WORKER_SEEN
    now = time.monotonic()
    with _LOCK:
        _LAST_WORKER_SEEN = now
        _prune_locked(now)
        while _PENDING:
            job_id = _PENDING.popleft()
            job = _JOBS.get(job_id)
            if job is None or job.claimed:
                continue
            job.claimed = True
            return {
                "job_id": job.job_id,
                "payload": job.payload,
                "expires_in_seconds": max(0, int(_JOB_TTL_SECONDS - (now - job.created_at))),
            }
    return None


def complete(job_id: str, *, result: str | None = None, error: str | None = None) -> bool:
    """Complete an existing claimed job exactly once."""
    with _LOCK:
        job = _JOBS.get(str(job_id))
        if job is None or job.event.is_set() or not job.claimed:
            return False
        if error:
            job.error = str(error)[:160]
        else:
            text = str(result or "").strip()
            if not text:
                job.error = "home_node_bridge_empty"
            else:
                job.result = text[:12000]
        job.event.set()
        return True


def status() -> dict[str, Any]:
    now = time.monotonic()
    with _LOCK:
        _prune_locked(now)
        worker_recent = bool(_LAST_WORKER_SEEN and now - _LAST_WORKER_SEEN <= 30.0)
        return {
            "configured": configured(),
            "worker_recently_seen": worker_recent,
            "pending_jobs": len(_PENDING),
            "active_jobs": len(_JOBS),
            "public_ollama_required": False,
            "transport": "outbound_https_poll",
        }
