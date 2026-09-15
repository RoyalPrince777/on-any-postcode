"""Secret-safe PostgreSQL connection diagnostic for SMI.

Returns only a bounded error category. Never returns connection URLs, hosts,
usernames, passwords, database names, exception strings, or server messages.
"""

from __future__ import annotations

import socket
from typing import Any

from . import postgres_db


def _category(exc: BaseException) -> str:
    # Prefer exception classes/SQLSTATE over rendering exception text, because
    # driver messages may contain host/user/database details.
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(exc, socket.gaierror):
        return "dns_failed"

    sqlstate = getattr(exc, "sqlstate", None)
    if sqlstate == "28P01":
        return "authentication_failed"
    if sqlstate in {"28000"}:
        return "authorization_failed"
    if sqlstate in {"3D000"}:
        return "database_not_found"
    if sqlstate and str(sqlstate).startswith("08"):
        return "connection_failed"

    name = type(exc).__name__.lower()
    if "timeout" in name:
        return "timeout"
    if "ssl" in name or "tls" in name:
        return "tls_failed"
    if "operational" in name or "connection" in name:
        return "connection_failed"
    return "database_unavailable"


def diagnostic_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "event": "oap_smi_database_connection_diagnostic",
        "configured": postgres_db.configured(),
        "source": postgres_db.database_source(),
        "reachable": False,
        "category": None,
        "secret_exposed": False,
    }
    if not snapshot["configured"]:
        snapshot["category"] = "database_url_not_configured"
        return snapshot

    try:
        with postgres_db.connect(readonly=True) as connection:
            connection.execute("SELECT 1").fetchone()
        snapshot["reachable"] = True
        snapshot["category"] = "ok"
    except BaseException as exc:  # category only; never serialize exc
        snapshot["category"] = _category(exc)
    return snapshot
