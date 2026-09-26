"""Read-only runtime binding proof for canonical SMI state ownership.

This probe never creates tables, runs migrations, writes records, spends money,
dispatches work, or changes authority. It proves only redacted runtime bindings
that can be independently read from the selected PostgreSQL target.
"""

from __future__ import annotations

from typing import Any

from oap.smi.state_ownership_registry import owners
from . import postgres_db


_TABLE_BINDINGS: dict[str, tuple[str, ...]] = {
    "identity": ("users",),
    "arena_competition": ("oap_arena_matches",),
    "arena_profile": ("oap_arena_player_profiles",),
    "organiser": ("oap_workspace_records",),
    "studio": ("oap_workspace_records",),
}

_FK_BINDINGS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "arena_profile": (("oap_arena_player_profiles", "identity_id", "users"),),
    "arena_competition": (
        ("oap_arena_matches", "player_a_id", "users"),
        ("oap_arena_matches", "player_b_id", "users"),
    ),
    "organiser": (("oap_workspace_records", "identity_id", "users"),),
    "studio": (("oap_workspace_records", "identity_id", "users"),),
}


def _table_names(connection) -> set[str]:
    rows = connection.execute(
        """SELECT table_name FROM information_schema.tables
           WHERE table_schema='public'"""
    ).fetchall()
    return {str(row[0]) for row in rows}


def _fk_exists(connection, table: str, column: str, referenced_table: str) -> bool:
    row = connection.execute(
        """SELECT 1
           FROM information_schema.table_constraints tc
           JOIN information_schema.key_column_usage kcu
             ON tc.constraint_name=kcu.constraint_name
            AND tc.constraint_schema=kcu.constraint_schema
           JOIN information_schema.constraint_column_usage ccu
             ON ccu.constraint_name=tc.constraint_name
            AND ccu.constraint_schema=tc.constraint_schema
           WHERE tc.constraint_type='FOREIGN KEY'
             AND tc.table_schema='public'
             AND tc.table_name=%s
             AND kcu.column_name=%s
             AND ccu.table_name=%s
           LIMIT 1""",
        (table, column, referenced_table),
    ).fetchone()
    return row is not None


def probe() -> dict[str, Any]:
    fingerprint = postgres_db.database_identity_fingerprint()
    result: dict[str, Any] = {
        "component": "SMI Runtime State Binding Proof",
        "database": {
            "source": fingerprint.get("source"),
            "authority": fingerprint.get("authority"),
            "reachable": bool(fingerprint.get("reachable")),
            "fingerprint_present": bool(fingerprint.get("fingerprint")),
            "secret_exposed": False,
        },
        "domains": {},
        "proven_count": 0,
        "checked_count": 0,
        "all_canonical_domains_proven": False,
        "read_only": True,
        "schema_changed": False,
        "human_authority_final": True,
        "error": None,
    }

    if not fingerprint.get("reachable"):
        result["error"] = "canonical_database_unreachable"
        return result

    try:
        with postgres_db.connect(readonly=True) as connection:
            tables = _table_names(connection)
            for owner in owners():
                domain = owner.domain_id
                required_tables = _TABLE_BINDINGS.get(domain)
                if required_tables is None:
                    result["domains"][domain] = {
                        "owner": owner.owner_component,
                        "state": "UNPROVEN",
                        "reason": "runtime_binding_probe_not_defined",
                    }
                    continue

                result["checked_count"] += 1
                missing_tables = sorted(set(required_tables) - tables)
                fk_checks = _FK_BINDINGS.get(domain, ())
                missing_fks = [
                    {
                        "table": table,
                        "column": column,
                        "references": referenced,
                    }
                    for table, column, referenced in fk_checks
                    if not _fk_exists(connection, table, column, referenced)
                ]
                proven = not missing_tables and not missing_fks
                result["domains"][domain] = {
                    "owner": owner.owner_component,
                    "state": "PROVEN" if proven else "UNPROVEN",
                    "required_tables": required_tables,
                    "missing_tables": tuple(missing_tables),
                    "missing_foreign_keys": tuple(missing_fks),
                }
                if proven:
                    result["proven_count"] += 1
    except (RuntimeError, OSError, postgres_db._driver().Error):
        result["error"] = "runtime_binding_probe_failed"
        return result

    result["all_canonical_domains_proven"] = bool(
        result["proven_count"] == len(owners())
    )
    return result
