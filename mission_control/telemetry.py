"""Bounded first-party request observability with optional Datadog delivery."""

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
_REQUEST_COUNT = 0
_ERROR_COUNT = 0
_HEALTH_SUCCESS_COUNT = 0
_LAST_REQUEST_EPOCH: float | None = None
_LAST_HEALTH_SUCCESS_EPOCH: float | None = None
_LAST_DURATION_MS: float | None = None
_MAX_DURATION_MS = 0.0
_LOCAL_FRESH_SECONDS = 300


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
    """Queue one external gauge without blocking the request path."""

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
    """Record first-party request evidence and optionally emit external metrics."""

    global _ERROR_COUNT
    global _HEALTH_SUCCESS_COUNT
    global _LAST_DURATION_MS
    global _LAST_HEALTH_SUCCESS_EPOCH
    global _LAST_REQUEST_EPOCH
    global _MAX_DURATION_MS
    global _REQUEST_COUNT

    now = time.time()
    duration_value = max(0.0, float(duration_ms))
    normalized_path = path if path.startswith("/") else "unknown"
    with _STATE_LOCK:
        _REQUEST_COUNT += 1
        _LAST_REQUEST_EPOCH = now
        _LAST_DURATION_MS = duration_value
        _MAX_DURATION_MS = max(_MAX_DURATION_MS, duration_value)
        if int(status_code) >= 500:
            _ERROR_COUNT += 1
        if normalized_path == "/healthz" and 200 <= int(status_code) < 300:
            _HEALTH_SUCCESS_COUNT += 1
            _LAST_HEALTH_SUCCESS_EPOCH = now

    route_tag = "route:" + normalized_path[:120]
    status_tag = f"status:{int(status_code)}"
    metric("http.request", 1, tags=(route_tag, status_tag), metric_type=1)
    metric("http.duration_ms", duration_value, tags=(route_tag, status_tag))
    if status_code >= 500:
        metric("http.error", 1, tags=(route_tag, status_tag), metric_type=1)


def status() -> dict[str, object]:
    """Return non-sensitive local observability plus optional external delivery state."""

    now = time.time()
    with _STATE_LOCK:
        last_success = _LAST_SUCCESS
        last_error = _LAST_ERROR
        request_count = _REQUEST_COUNT
        error_count = _ERROR_COUNT
        health_success_count = _HEALTH_SUCCESS_COUNT
        last_request_epoch = _LAST_REQUEST_EPOCH
        last_health_success_epoch = _LAST_HEALTH_SUCCESS_EPOCH
        last_duration_ms = _LAST_DURATION_MS
        max_duration_ms = _MAX_DURATION_MS
    request_fresh = bool(
        last_request_epoch is not None
        and 0 <= now - last_request_epoch <= _LOCAL_FRESH_SECONDS
    )
    health_fresh = bool(
        last_health_success_epoch is not None
        and 0 <= now - last_health_success_epoch <= _LOCAL_FRESH_SECONDS
    )
    local_ready = bool(request_count > 0 and health_success_count > 0 and request_fresh and health_fresh)
    external_ready = bool(configured() and last_success is not None and last_error is None)
    return {
        "enabled": enabled(),
        "site_valid": bool(site()),
        "api_key_configured": bool(os.environ.get("DD_API_KEY", "").strip()),
        "configured": configured(),
        "delivery_verified": last_success is not None and last_error is None,
        "last_success_epoch": int(last_success) if last_success else None,
        "last_error": last_error,
        "queued": _METRICS.qsize(),
        "ready": external_ready,
        "local_request_count": request_count,
        "local_error_count": error_count,
        "local_health_success_count": health_success_count,
        "local_last_request_epoch": int(last_request_epoch) if last_request_epoch else None,
        "local_last_health_success_epoch": (
            int(last_health_success_epoch) if last_health_success_epoch else None
        ),
        "local_last_duration_ms": last_duration_ms,
        "local_max_duration_ms": max_duration_ms,
        "local_fresh_seconds": _LOCAL_FRESH_SECONDS,
        "local_observability_ready": local_ready,
        "observability_ready": bool(local_ready or external_ready),
    }
