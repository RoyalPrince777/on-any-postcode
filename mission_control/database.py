"""Select the production PostgreSQL backend or local SQLite without duplication."""

from __future__ import annotations

from typing import Any

from . import db as sqlite_db
from . import postgres_db


def db_status() -> dict[str, Any]:
    """Return one normalized, redacted database status."""
    if postgres_db.configured():
        status = postgres_db.postgres_status()
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
