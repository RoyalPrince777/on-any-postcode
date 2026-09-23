"""Read-only OAP Mail database preflight; never a migration authorisation.

The executing service can report its own redacted database selection and
schema readiness. Service-to-project identity and recoverability require
independent operator evidence: a database name is not proof of either.
"""
from __future__ import annotations

from . import mail_migration, postgres_db

_ALLOWED_AUTHORITIES = frozenset({"primary", "fallback"})
_ALLOWED_SOURCES = frozenset({
    "primary_override", "fallback_override", "platform_database_url",
    "legacy_oap_secret", "legacy_neon", "unconfigured",
    "fallback_unconfigured", "invalid_authority",
})


# Operator evidence is external to this application and cannot be inferred
# from a reachable database, a migration record, a branch or a service name.
# This checklist contains categories only: never credentials or backup IDs.
_INDEPENDENT_RELEASE_EVIDENCE = (
    "service_to_database_target_mapping",
    "backup_owner_and_source_target_match",
    "independent_backup_integrity_verification",
    "isolated_restore_completion_and_readback",
    "restore_timestamp_and_operator_attestation",
    "founder_release_approval",
)


def report() -> dict[str, object]:
    """Collect bounded metadata only; never expose URLs, credentials or messages."""
    result: dict[str, object] = {
        "component": "OAP Mail / database preflight",
        "read_only": True,
        "database_authority": "unverified",
        "database_source": "unverified",
        "database_configured": False,
        "database_reachable": False,
        "base_schema_ready": False,
        "mail_schema_ready": False,
        "target_mapping_proven": False,
        "recovery_point_verified": False,
        "independent_release_evidence_required": list(
            _INDEPENDENT_RELEASE_EVIDENCE
        ),
        "independent_release_evidence_verified": False,
        "live_migration_authorized": False,
        "release_ready": False,
        "error": None,
    }
    try:
        authority = postgres_db.database_authority()
        source = postgres_db.database_source()
        if authority not in _ALLOWED_AUTHORITIES or source not in _ALLOWED_SOURCES:
            result["error"] = "database_selection_unavailable"
            return result
        result["database_authority"] = authority
        result["database_source"] = source
        result["database_configured"] = postgres_db.configured()
        if not result["database_configured"]:
            result["error"] = "database_selection_unavailable"
            return result
        base = postgres_db.postgres_status()
        if base.get("source") not in {None, source}:
            result["error"] = "database_source_changed_during_preflight"
            return result
        if base.get("checksum_mismatches"):
            result["error"] = "base_migration_checksum_mismatch"
            return result
        result["database_reachable"] = base.get("reachable") is True
        result["base_schema_ready"] = base.get("initialized") is True
        if not result["database_reachable"] or not result["base_schema_ready"]:
            result["error"] = "base_postgres_not_ready"
            return result
        mail = mail_migration.schema_status()
        # Status is advisory only: reject an authority/source switch while
        # collecting the two independent read-only database observations.
        if (
            postgres_db.database_authority() != authority
            or postgres_db.database_source() != source
        ):
            result["error"] = "database_selection_changed_during_preflight"
            return result
        result["mail_schema_ready"] = mail.get("schema_ready") is True
        result["error"] = mail.get("error")
    except Exception:  # noqa: BLE001 - redacted evidence boundary
        result["error"] = "mail_preflight_unavailable"
    return result
