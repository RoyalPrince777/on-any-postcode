"""Read-only status projections for the Mission Control gateway.

This module deliberately exposes two separate projections:

* ``get_public_gateway_status`` returns only coarse, redacted information.
* ``get_authorized_mission_status`` remains fail-closed until authenticated
  identity and permission services are integrated.

No function in this module creates a database, applies a migration, writes an
audit event, or changes operational state.
"""

from __future__ import annotations

import socket
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from . import config
from .db import db_status
from .organism import INTELLIGENCE_WORLDS

_PUBLIC_ACTION_LABELS = {
    "SYSTEM_LOG_ONLY": "System log recorded",
    "MISSION_REVIEWED": "Mission review recorded",
    "HUMAN_APPROVED": "Human approval recorded",
    "HUMAN_REJECTED": "Human rejection recorded",
}


def _component(label: str, value: str, state: str) -> dict[str, str]:
    return {"label": label, "value": value, "state": state}


def _readonly_connect(db_path: str) -> sqlite3.Connection:
    """Open an existing SQLite file in query-only mode without creating it."""

    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=1)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA busy_timeout = 250")
    return connection


def _probe_ollama() -> bool:
    """Check only a loopback Ollama endpoint; never contact a remote host."""

    parsed = urlparse(config.OLLAMA_URL)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        return False

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((parsed.hostname, port), timeout=0.15):
            return True
    except OSError:
        return False


def _public_timeline(db_path: str, initialized: bool) -> list[dict[str, str]]:
    """Return at most five allowlisted events without identities or targets."""

    if not initialized:
        return []

    try:
        connection = _readonly_connect(db_path)
        try:
            rows = connection.execute(
                "SELECT action, timestamp FROM audit_events "
                "WHERE action IN (?, ?, ?, ?) "
                "ORDER BY event_seq DESC LIMIT 5",
                tuple(_PUBLIC_ACTION_LABELS),
            ).fetchall()
        finally:
            connection.close()
    except (OSError, sqlite3.Error):
        return []

    return [
        {
            "summary": _PUBLIC_ACTION_LABELS[row["action"]],
            "timestamp": row["timestamp"],
        }
        for row in rows
    ]


def _approval_summary(initialized: bool) -> dict[str, Any]:
    """Return a safe placeholder until the approval migration is available."""

    if not initialized:
        return {
            "initialized": False,
            "message": "Mission Control database not initialized",
            "counts": {},
        }

    # Migration 0003 will define the canonical approval schema. Until then,
    # do not infer Mission Control state from the legacy ``approvals`` table.
    return {
        "initialized": False,
        "message": "Approval queue not initialized",
        "counts": {},
    }


def get_public_gateway_status() -> dict[str, Any]:
    """Build the coarse public status projection without changing state."""

    database = db_status()
    initialized = bool(database.get("initialized"))

    if not database["exists"]:
        database_component = _component("Database", "Not initialized", "degraded")
    elif initialized:
        database_component = _component("Database", "Read-only ready", "healthy")
    elif database.get("error"):
        database_component = _component("Database", "Unavailable", "degraded")
    else:
        database_component = _component(
            "Database", "Legacy data found; Mission Control not initialized", "degraded"
        )

    audit_component = _component(
        "HRM Audit Chain",
        "Ready" if initialized else "Not initialized",
        "healthy" if initialized else "degraded",
    )
    ollama_available = _probe_ollama()
    approval_summary = _approval_summary(initialized)

    components = [
        _component(
            "Local Mode",
            "Enabled" if config.OAP_LOCAL_MODE else "Disabled",
            "healthy" if config.OAP_LOCAL_MODE else "degraded",
        ),
        database_component,
        audit_component,
        _component("Guardian", "Not connected", "degraded"),
        _component(
            "Ollama",
            "Available" if ollama_available else "Degraded",
            "healthy" if ollama_available else "degraded",
        ),
        _component(
            "Approval Queue",
            "Ready" if approval_summary["initialized"] else "Not initialized",
            "healthy" if approval_summary["initialized"] else "degraded",
        ),
    ]

    agents = [
        {
            "name": name,
            "status": "Not connected",
            "assignment": "No assignment",
        }
        for name in INTELLIGENCE_WORLDS
    ]

    return {
        "mode": "Local Mode" if config.OAP_LOCAL_MODE else "Configured Mode",
        "components": components,
        "agents": agents,
        "approval_summary": approval_summary,
        "timeline": _public_timeline(database["db_path"], initialized),
        "human_authority": {
            "status": "Final approval required",
            "message": "Intelligence proposes. Human Authority approves or rejects.",
        },
    }


def get_authorized_mission_status(identity: Any) -> dict[str, Any]:
    """Fail closed until verified Identity and Permission services are wired."""

    del identity
    raise PermissionError(
        "Privileged Mission Control status is unavailable until Identity and "
        "Permission checks are enabled."
    )
