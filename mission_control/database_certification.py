"""Bounded, secret-free PostgreSQL certification snapshot for SMI.

This module deliberately exposes no URL, host, username, password, database name,
or credential material. It reuses the read-only PostgreSQL readiness probe.
"""

from __future__ import annotations

from typing import Any

from . import postgres_db


def certification_snapshot() -> dict[str, Any]:
    status = postgres_db.postgres_status()
    return {
        "event": "oap_smi_database_certification",
        "backend": status.get("backend"),
        "source": status.get("source"),
        "configured": bool(status.get("configured")),
        "reachable": bool(status.get("reachable")),
        "initialized": bool(status.get("initialized")),
        "pending_migration_count": len(status.get("pending") or ()),
        "checksum_mismatch_count": len(status.get("checksum_mismatches") or ()),
        "error": status.get("error"),
        "secret_exposed": False,
    }
