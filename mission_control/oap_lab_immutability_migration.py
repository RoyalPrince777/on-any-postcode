"""Explicit LAB notebook immutability migration.

This module only defines and applies the minimal database protection for
OAP-LAB notebook rows. Nothing runs at import time. Application requires
explicit Human Authority approval and remains independently reversible.
"""
from __future__ import annotations

from . import postgres_db, workspaces

APPLY_SQL = """
CREATE OR REPLACE FUNCTION oap_lab_workspace_immutable_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF (
            (OLD.workspace_id = 'governance' AND OLD.title LIKE 'OAP-LAB:%')
            OR
            (NEW.workspace_id = 'governance' AND NEW.title LIKE 'OAP-LAB:%')
        ) THEN
            RAISE EXCEPTION 'OAP LAB notebook records are immutable';
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.workspace_id = 'governance' AND OLD.title LIKE 'OAP-LAB:%' THEN
            RAISE EXCEPTION 'OAP LAB notebook records are immutable';
        END IF;
        RETURN OLD;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$;

DROP TRIGGER IF EXISTS oap_lab_workspace_immutable ON oap_workspace_records;

CREATE TRIGGER oap_lab_workspace_immutable
BEFORE UPDATE OR DELETE ON oap_workspace_records
FOR EACH ROW
EXECUTE FUNCTION oap_lab_workspace_immutable_guard();
""".strip()

ROLLBACK_SQL = """
DROP TRIGGER IF EXISTS oap_lab_workspace_immutable ON oap_workspace_records;
DROP FUNCTION IF EXISTS oap_lab_workspace_immutable_guard();
""".strip()


class LabImmutabilityMigrationBlocked(RuntimeError):
    """The explicit LAB immutability database change cannot safely proceed."""


def apply(*, assume_yes: bool = False) -> dict[str, object]:
    """Apply the exact protection after explicit Human Authority approval."""
    if not assume_yes:
        raise LabImmutabilityMigrationBlocked(
            "explicit_human_approval_required"
        )
    if not bool(postgres_db._lab_database_url()):
        raise LabImmutabilityMigrationBlocked("database_unconfigured")

    before = workspaces.lab_immutability_status()
    if before.get("database_enforced"):
        return {
            "applied": False,
            "already_enforced": True,
            "verified": True,
            "rollback_sql": ROLLBACK_SQL,
        }

    try:
        with postgres_db.lab_connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680261,))
            connection.execute(APPLY_SQL)
            connection.commit()
    except Exception as exc:
        raise LabImmutabilityMigrationBlocked(
            "lab_immutability_apply_failed"
        ) from exc

    after = workspaces.lab_immutability_status()
    if not after.get("database_enforced"):
        raise LabImmutabilityMigrationBlocked(
            "lab_immutability_post_apply_proof_failed"
        )
    return {
        "applied": True,
        "already_enforced": False,
        "verified": True,
        "rollback_sql": ROLLBACK_SQL,
    }


def rollback(*, assume_yes: bool = False) -> dict[str, object]:
    """Remove only the LAB-specific trigger/function after explicit approval."""
    if not assume_yes:
        raise LabImmutabilityMigrationBlocked(
            "explicit_human_approval_required"
        )
    if not bool(postgres_db._lab_database_url()):
        raise LabImmutabilityMigrationBlocked("database_unconfigured")
    try:
        with postgres_db.lab_connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680261,))
            connection.execute(ROLLBACK_SQL)
            connection.commit()
    except Exception as exc:
        raise LabImmutabilityMigrationBlocked(
            "lab_immutability_rollback_failed"
        ) from exc
    return {
        "rolled_back": True,
        "verified": not bool(
            workspaces.lab_immutability_status().get(
                "protective_trigger_present"
            )
        ),
    }
