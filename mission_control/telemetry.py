"""First-party OAP Data request observability. No external analytics transport.

Only bounded aggregate counts and timing are kept in process memory. No paths,
queries, cookies, identifiers, or request bodies are retained or exported.
"""
from __future__ import annotations
import threading
import time

_STATE_LOCK = threading.Lock()
_REQUEST_COUNT = 0
_ERROR_COUNT = 0
_HEALTH_SUCCESS_COUNT = 0
_LAST_REQUEST_EPOCH: float | None = None
_LAST_HEALTH_SUCCESS_EPOCH: float | None = None
_LAST_DURATION_MS: float | None = None
_MAX_DURATION_MS = 0.0
_LOCAL_FRESH_SECONDS = 300


def enabled() -> bool:
    """Legacy compatibility: external telemetry is permanently disabled."""
    return False


def site() -> str:
    return ""


def configured() -> bool:
    return False


def metric(name: str, value: float, *, tags: tuple[str, ...] = (),
           metric_type: int = 3) -> bool:
    """Legacy API retained for callers; never exports or queues data."""
    return False


def record_http_request(*, path: str, status_code: int, duration_ms: float) -> None:
    """Count requests and errors locally without storing identifiable route paths."""
    global _REQUEST_COUNT, _ERROR_COUNT, _HEALTH_SUCCESS_COUNT
    global _LAST_REQUEST_EPOCH, _LAST_HEALTH_SUCCESS_EPOCH
    global _LAST_DURATION_MS, _MAX_DURATION_MS
    now = time.time()
    duration = max(0.0, float(duration_ms))
    with _STATE_LOCK:
        _REQUEST_COUNT += 1
        _LAST_REQUEST_EPOCH = now
        _LAST_DURATION_MS = duration
        _MAX_DURATION_MS = max(_MAX_DURATION_MS, duration)
        if int(status_code) >= 500:
            _ERROR_COUNT += 1
        if path == "/healthz" and 200 <= int(status_code) < 300:
            _HEALTH_SUCCESS_COUNT += 1
            _LAST_HEALTH_SUCCESS_EPOCH = now


def status() -> dict[str, object]:
    """Compatibility status projection consumed by the existing SMI proof gate."""
    now = time.time()
    with _STATE_LOCK:
        request_count = _REQUEST_COUNT
        error_count = _ERROR_COUNT
        health_success_count = _HEALTH_SUCCESS_COUNT
        last_request_epoch = _LAST_REQUEST_EPOCH
        last_health_success_epoch = _LAST_HEALTH_SUCCESS_EPOCH
        last_duration_ms = _LAST_DURATION_MS
        max_duration_ms = _MAX_DURATION_MS
    request_fresh = (last_request_epoch is not None
                     and 0 <= now - last_request_epoch <= _LOCAL_FRESH_SECONDS)
    health_fresh = (last_health_success_epoch is not None
                    and 0 <= now - last_health_success_epoch <= _LOCAL_FRESH_SECONDS)
    local_ready = bool(request_count and health_success_count and request_fresh and health_fresh)
    return {
        "enabled": False, "site_valid": False, "api_key_configured": False,
        "configured": False, "delivery_verified": False,
        "last_success_epoch": None, "last_error": None, "queued": 0,
        "ready": False,
        "local_request_count": request_count,
        "local_error_count": error_count,
        "local_health_success_count": health_success_count,
        "local_last_request_epoch": int(last_request_epoch) if last_request_epoch else None,
        "local_last_health_success_epoch": int(last_health_success_epoch) if last_health_success_epoch else None,
        "local_last_duration_ms": last_duration_ms,
        "local_max_duration_ms": max_duration_ms,
        "local_fresh_seconds": _LOCAL_FRESH_SECONDS,
        "local_observability_ready": local_ready,
        "observability_ready": local_ready,
    }
