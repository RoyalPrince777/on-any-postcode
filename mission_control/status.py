"""Read-only status projections for the Mission Control gateway.

This module deliberately exposes two separate projections:

* ``get_public_gateway_status`` returns only coarse, redacted information.
* ``get_authorized_mission_status`` remains fail-closed until authenticated
  identity and permission services are integrated.

No function in this module creates a database, applies a migration, writes an
audit event, changes operational state or probes a non-loopback network host.
"""

from __future__ import annotations

import socket
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from oap.guardian.engine import GuardianEngine

from . import config, provider_fabric
from .agents import get_public_family_status
from .database import db_status

_PUBLIC_ACTION_LABELS = {
    "SYSTEM_LOG_ONLY": "System log recorded",
    "MISSION_REVIEWED": "Mission review recorded",
    "SMI_REVIEWED": "Intelligence review recorded",
    "HUMAN_APPROVED": "Human approval recorded",
    "HUMAN_REJECTED": "Human rejection recorded",
    "KERNEL_EXECUTED": "Approved Builder outcome recorded",
    "WORLD_STATE_UPDATED": "Approved world-state update recorded",
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


def _guardian_component() -> dict[str, str]:
    """Report the actual constitutional Guardian gate, not a fixed label."""

    try:
        guardian = GuardianEngine().status()
        ready = bool(guardian.get("ready"))
    except Exception:  # noqa: BLE001 - status must fail closed and stay redacted.
        ready = False
    return _component(
        "Guardian",
        "Constitutional gate ready" if ready else "Unavailable",
        "healthy" if ready else "degraded",
    )


def _provider_component() -> tuple[dict[str, str], dict[str, Any]]:
    """Build a coarse provider status from configuration and observed evidence."""

    try:
        provider = provider_fabric.get_coarse_provider_status()
    except Exception:  # noqa: BLE001 - do not leak provider details from status.
        provider = {
            "architecture_passed": False,
            "slots": 0,
            "wired": 0,
            "configured": 0,
            "runtime_verified": 0,
            "consequential_execution_enabled": False,
            "human_authority_required": True,
        }
    architecture_ready = bool(provider.get("architecture_passed"))
    configured = int(provider.get("configured") or 0)
    runtime_verified = int(provider.get("runtime_verified") or 0)
    value = f"{configured} configured · {runtime_verified} runtime verified"
    return (
        _component(
            "Provider Fabric",
            value if architecture_ready else "Architecture unavailable",
            "healthy" if architecture_ready else "degraded",
        ),
        provider,
    )


def _public_timeline(db_path: str, initialized: bool) -> list[dict[str, str]]:
    """Return at most five allowlisted events without identities or targets."""

    if not initialized:
        return []

    try:
        connection = _readonly_connect(db_path)
        try:
            rows = connection.execute(
                "SELECT action, timestamp FROM audit_events "
                f"WHERE action IN ({', '.join('?' for _ in _PUBLIC_ACTION_LABELS)}) "
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


def _approval_summary(db_path: str, initialized: bool) -> dict[str, Any]:
    """Return coarse counts from the action-bound approval ledger."""

    if not initialized:
        return {
            "initialized": False,
            "message": "Mission Control database not initialized",
            "counts": {},
        }

    try:
        connection = _readonly_connect(db_path)
        try:
            receipt_table = connection.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type = 'table' AND name = 'smi_approval_receipts'"
            ).fetchone()
            memory_table = connection.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type = 'table' AND name = 'smi_memory_records'"
            ).fetchone()
            if receipt_table is None or memory_table is None:
                return {
                    "initialized": False,
                    "message": "Approval records not initialized",
                    "counts": {},
                }
            row = connection.execute(
                "SELECT "
                "SUM(CASE WHEN r.decision = 'APPROVED' THEN 1 ELSE 0 END) "
                "AS approved, "
                "SUM(CASE WHEN r.decision = 'REJECTED' THEN 1 ELSE 0 END) "
                "AS rejected, "
                "SUM(CASE WHEN r.receipt_id IS NULL AND m.output_state IN "
                "('RECOMMENDATION_READY', 'REVIEW_REQUIRED') THEN 1 ELSE 0 END) "
                "AS pending "
                "FROM smi_memory_records AS m "
                "LEFT JOIN smi_approval_receipts AS r "
                "ON r.request_id = m.request_id"
            ).fetchone()
        finally:
            connection.close()
    except (OSError, sqlite3.Error):
        return {
            "initialized": False,
            "message": "Approval records unavailable",
            "counts": {},
        }
    return {
        "initialized": True,
        "message": "Read-only approval records available",
        "counts": {
            "pending": int(row["pending"] or 0),
            "approved": int(row["approved"] or 0),
            "rejected": int(row["rejected"] or 0),
        },
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
    if database.get("backend") == "postgresql":
        approval_summary = {
            "initialized": initialized,
            "message": (
                "Read-only approval records available"
                if initialized
                else "Mission Control database not initialized"
            ),
            "counts": {},
        }
    else:
        approval_summary = _approval_summary(
            database["db_path"],
            bool(database.get("brain_runtime_initialized")),
        )

    provider_component, provider_summary = _provider_component()
    local_model_component = (
        _component(
            "Local Ollama",
            "Available" if ollama_available else "Unavailable",
            "healthy" if ollama_available else "degraded",
        )
        if config.OAP_LOCAL_MODE
        else _component(
            "Local Ollama",
            "Optional local model inactive",
            "healthy",
        )
    )

    components = [
        _component(
            "Local Mode",
            "Enabled" if config.OAP_LOCAL_MODE else "Disabled by configuration",
            "healthy",
        ),
        database_component,
        audit_component,
        _guardian_component(),
        provider_component,
        local_model_component,
        _component(
            "Approval Queue",
            "Ready" if approval_summary["initialized"] else "Not initialized",
            "healthy" if approval_summary["initialized"] else "degraded",
        ),
    ]

    agents = get_public_family_status()

    return {
        "mode": "Local Mode" if config.OAP_LOCAL_MODE else "Configured Mode",
        "components": components,
        "agents": agents,
        "provider_summary": provider_summary,
        "approval_summary": approval_summary,
        "timeline": (
            []
            if database.get("backend") == "postgresql"
            else _public_timeline(database["db_path"], initialized)
        ),
        "status_truth": {
            "fixed_live_labels": False,
            "external_network_probe_on_status": False,
            "guardian_source": "constitutional_engine",
            "provider_source": "configuration_and_observed_delivery",
        },
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
