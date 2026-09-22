"""Read-only OAP Mail database preflight; never a migration authorisation.

The executing service can report its own redacted database selection and
schema readiness. Service-to-project identity and recoverability require
independent operator evidence: a database name is not proof of either.
"""
from __future__ import annotations

from . import mail_migration, postgres_db


def report() -> dict[str, object]:
    """Collect bounded metadata only; never expose URLs, credentials or messages."""
    result: dict[str, object] = {
        "component": "OAP Mail / database preflight",
        "read_only": True,
        "database_authority": postgres_db.database_authority(),
        "database_source": postgres_db.database_source(),
        "database_configured": False,
        "database_reachable": False,
        "base_schema_ready": False,
        "mail_schema_ready": False,
        "target_mapping_proven": False,
        "recovery_point_verified": False,
        "live_migration_authorized": False,
        "release_ready": False,
        "error": None,
    }
    try:
        result["database_configured"] = postgres_db.configured()
        if result["database_authority"] == "invalid" or not result["database_configured"]:
            result["error"] = "database_selection_unavailable"
            return result
        base = postgres_db.postgres_status()
        result["database_reachable"] = base.get("reachable") is True
        result["base_schema_ready"] = base.get("initialized") is True
        if not result["base_schema_ready"]:
            result["error"] = "base_postgres_not_ready"
            return result
        mail = mail_migration.schema_status()
        result["mail_schema_ready"] = mail.get("schema_ready") is True
        result["error"] = mail.get("error")
    except Exception:  # noqa: BLE001 - redacted evidence boundary
        result["error"] = "mail_preflight_unavailable"
    return result
