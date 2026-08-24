"""Bounded agentless Datadog metric delivery for Render deployments."""

from __future__ import annotations

import json
import os
import queue
import threading
import time
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

_ALLOWED_SITES = frozenset({"datadoghq.eu", "datadoghq.com"})
_METRICS: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=1000)
_THREAD: threading.Thread | None = None
_THREAD_LOCK = threading.Lock()
_STATE_LOCK = threading.Lock()
_LAST_SUCCESS: float | None = None
_LAST_ERROR: str | None = None


def enabled() -> bool:
    return os.environ.get("OAP_DATADOG_ENABLED", "false").strip().lower() == "true"


def site() -> str:
    value = os.environ.get("DD_SITE", "datadoghq.eu").strip().casefold()
    return value if value in _ALLOWED_SITES else ""


def configured() -> bool:
    return bool(enabled() and site() and os.environ.get("DD_API_KEY", "").strip())


def _worker() -> None:
    global _LAST_ERROR, _LAST_SUCCESS
    while True:
        item = _METRICS.get()
        batch = [item]
        deadline = time.monotonic() + 1.0
        while len(batch) < 100 and time.monotonic() < deadline:
            try:
                batch.append(_METRICS.get(timeout=0.05))
            except queue.Empty:
                break
        payload = {"series": batch}
        request = urlrequest.Request(
            f"https://api.{site()}/api/v2/series",
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "DD-API-KEY": os.environ.get("DD_API_KEY", "").strip(),
                "User-Agent": "ON-ANY-POSTCODE-Telemetry/1.0",
            },
            method="POST",
        )
        try:
            with urlrequest.urlopen(request, timeout=5) as response:
                if not 200 <= int(response.status) < 300:
                    raise RuntimeError("datadog_metric_rejected")
            with _STATE_LOCK:
                _LAST_SUCCESS = time.time()
                _LAST_ERROR = None
        except (OSError, TimeoutError, RuntimeError, urlerror.URLError) as exc:
            with _STATE_LOCK:
                _LAST_ERROR = type(exc).__name__
        finally:
            for _ in batch:
                _METRICS.task_done()


def _ensure_worker() -> None:
    global _THREAD
    if _THREAD and _THREAD.is_alive():
        return
    with _THREAD_LOCK:
        if _THREAD and _THREAD.is_alive():
            return
        _THREAD = threading.Thread(
            target=_worker,
            name="oap-datadog-metrics",
            daemon=True,
        )
        _THREAD.start()


def metric(
    name: str,
    value: float,
    *,
    tags: tuple[str, ...] = (),
    metric_type: int = 3,
) -> bool:
    """Queue one gauge without blocking the request path."""

    if not configured():
        return False
    _ensure_worker()
    item = {
        "metric": f"oap.{name}",
        "type": metric_type if metric_type in {1, 2, 3} else 3,
        "points": [{"timestamp": int(time.time()), "value": float(value)}],
        "resources": [
            {
                "name": os.environ.get("DD_SERVICE", "on-any-postcode")[:200],
                "type": "service",
            }
        ],
        "tags": [
            f"env:{os.environ.get('DD_ENV', 'production')[:100]}",
            *[str(tag)[:200] for tag in tags[:20]],
        ],
    }
    try:
        _METRICS.put_nowait(item)
    except queue.Full:
        return False
    return True


def record_http_request(*, path: str, status_code: int, duration_ms: float) -> None:
    """Emit request count, latency and error gauges with bounded tags."""

    route_tag = "route:" + (path[:120] if path.startswith("/") else "unknown")
    status_tag = f"status:{int(status_code)}"
    metric("http.request", 1, tags=(route_tag, status_tag), metric_type=1)
    metric("http.duration_ms", duration_ms, tags=(route_tag, status_tag))
    if status_code >= 500:
        metric("http.error", 1, tags=(route_tag, status_tag), metric_type=1)


def status() -> dict[str, object]:
    with _STATE_LOCK:
        last_success = _LAST_SUCCESS
        last_error = _LAST_ERROR
    return {
        "enabled": enabled(),
        "site_valid": bool(site()),
        "api_key_configured": bool(os.environ.get("DD_API_KEY", "").strip()),
        "configured": configured(),
        "delivery_verified": last_success is not None and last_error is None,
        "last_success_epoch": int(last_success) if last_success else None,
        "last_error": last_error,
        "queued": _METRICS.qsize(),
        "ready": bool(configured() and last_success is not None and last_error is None),
    }
