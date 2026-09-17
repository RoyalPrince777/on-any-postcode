"""Runtime wiring for governed eSIM persistence.

This module performs only a read-only schema check before attaching persistence.
It never creates tables, migrates data, provisions profiles, or selects a carrier.
"""
from __future__ import annotations

from typing import Any

from . import esim_persistence, esim_provisioning, postgres_db

_REQUIRED_TABLES = ("oap_esim_requests", "oap_esim_events")
_STATE: dict[str, Any] = {
    "persistence_attached": False,
    "database_configured": False,
    "schema_ready": False,
    "reason": "not_checked",
}


def configure() -> dict[str, Any]:
    """Attach the PostgreSQL repository only when its schema already exists."""

    if not postgres_db.configured():
        return _set_state(False, False, False, "database_not_configured")

    try:
        with postgres_db.connect() as connection:
            rows = connection.execute(
                """SELECT to_regclass(%s), to_regclass(%s)""",
                _REQUIRED_TABLES,
            ).fetchone()
    except Exception:  # noqa: BLE001 - expose no connection details.
        return _set_state(False, True, False, "database_unavailable")

    schema_ready = bool(rows and all(rows))
    if not schema_ready:
        esim_provisioning.CORE.repository = None
        return _set_state(False, True, False, "esim_schema_not_initialized")

    esim_provisioning.CORE.repository = esim_persistence.EsimRepository(
        postgres_db.connect
    )
    return _set_state(True, True, True, "ready")


def status() -> dict[str, Any]:
    """Return redacted runtime readiness."""

    return dict(_STATE)


def _set_state(
    attached: bool,
    database_configured: bool,
    schema_ready: bool,
    reason: str,
) -> dict[str, Any]:
    _STATE.update(
        {
            "persistence_attached": attached,
            "database_configured": database_configured,
            "schema_ready": schema_ready,
            "reason": reason,
        }
    )
    return status()
