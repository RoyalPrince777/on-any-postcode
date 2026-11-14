"""Select the production PostgreSQL backend or local SQLite without duplication."""

from __future__ import annotations

import os
import time
from copy import deepcopy
from typing import Any

from . import db as sqlite_db
from . import postgres_db

_DB_STATUS_CACHE_VALUE: dict[str, Any] | None = None
_DB_STATUS_CACHE_EXPIRES_AT = 0.0


def _cache_seconds() -> float:
    """Return a bounded readiness cache duration for all PostgreSQL runtimes."""

    raw = os.environ.get("OAP_DB_STATUS_CACHE_SECONDS", "60").strip()
    try:
        seconds = float(raw)
    except ValueError:
        seconds = 60.0
    return min(max(seconds, 5.0), 300.0)


def _clear_db_status_cache() -> None:
    """Clear the process-local readiness cache (mainly useful for tests)."""

    global _DB_STATUS_CACHE_VALUE, _DB_STATUS_CACHE_EXPIRES_AT
    _DB_STATUS_CACHE_VALUE = None
    _DB_STATUS_CACHE_EXPIRES_AT = 0.0


def _postgres_status() -> dict[str, Any]:
    """Read PostgreSQL status without letting platform probes hammer Neon."""

    global _DB_STATUS_CACHE_VALUE, _DB_STATUS_CACHE_EXPIRES_AT
    now = time.monotonic()
    if _DB_STATUS_CACHE_VALUE is not None and now < _DB_STATUS_CACHE_EXPIRES_AT:
        return deepcopy(_DB_STATUS_CACHE_VALUE)

    status = postgres_db.postgres_status()
    _DB_STATUS_CACHE_VALUE = deepcopy(status)
    hosted = os.environ.get("RENDER", "").lower() == "true"
    duration = _cache_seconds() if hosted else min(_cache_seconds(), 5.0)
    _DB_STATUS_CACHE_EXPIRES_AT = now + duration
    return status


def db_status() -> dict[str, Any]:
    """Return one normalized, redacted database status."""
    if postgres_db.configured():
        status = _postgres_status()
        return {
            **status,
            "db_path": None,
            "exists": bool(status["reachable"]),
            "brain_runtime_initialized": bool(status["initialized"]),
            "applied": [] if status["pending"] else [
                {"version": postgres_db.MIGRATION_VERSION}
            ],
        }
    return {**sqlite_db.db_status(), "backend": "sqlite"}
