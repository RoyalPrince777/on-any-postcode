"""Privacy-minimised youth contact guard for Link Up.

Stores only a governed age class (minor/adult), never date of birth.
Unknown identities are never guessed. Cross-age contact is blocked only when
both classifications are proven and conflict.
"""
from __future__ import annotations

import uuid
from typing import Any

from . import authority, postgres_db

SCHEMA_VERSION = "link_youth_guard_v1"
ALLOWED_BANDS = {"minor", "adult"}
SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS link_age_classifications (
        identity_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        age_band TEXT NOT NULL CHECK (age_band IN ('minor','adult')),
        source TEXT NOT NULL CHECK (source IN ('verified_record','human_authority')),
        confirmed_by UUID NOT NULL REFERENCES oap_identities(identity_id),
        confirmed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS idx_link_age_band
       ON link_age_classifications(age_band,updated_at DESC)""",
)

class LinkYouthSafetyUnavailable(RuntimeError):
    pass

def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc

def _band(value: object) -> str:
    band = str(value or "").strip().casefold()
    if band not in ALLOWED_BANDS:
        raise ValueError("invalid_age_band")
    return band

def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes and not dry_run:
        raise PermissionError("explicit_confirmation_required")
    if dry_run:
        return {"version": SCHEMA_VERSION, "statements": list(SCHEMA_SQL), "applied": False}
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext('oap_link_youth_guard_v1'))"
            )
            for statement in SCHEMA_SQL:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise LinkYouthSafetyUnavailable("link_youth_guard_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}

def status() -> dict[str, Any]:
    result = {
        "configured": postgres_db.configured(),
        "ready": False,
        "stores_date_of_birth": False,
        "unknown_is_guessed": False,
        "cross_age_policy": "block_only_when_both_proven",
    }
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            table = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='link_age_classifications'"""
            ).fetchone()
        result["ready"] = table is not None
    except Exception:
        return result
    return result

def set_age_band(
    target_identity_id: object,
    *,
    age_band: object,
    confirmed_by_identity_id: object,
    source: object = "human_authority",
    human_authority_approved: bool,
) -> dict[str, object]:
    if human_authority_approved is not True:
        raise PermissionError("human_authority_approval_required")
    target = _uuid(target_identity_id, "invalid_target_identity")
    confirmer = _uuid(confirmed_by_identity_id, "invalid_confirmer_identity")
    band = _band(age_band)
    source_value = str(source or "").strip().casefold()
    if source_value not in {"verified_record", "human_authority"}:
        raise ValueError("invalid_age_source")
    try:
        with postgres_db.connect() as connection:
            authority.require_human_authority(connection, confirmer)
            active = connection.execute(
                "SELECT 1 FROM users WHERE id=%s AND status='active'",
                (target,),
            ).fetchone()
            if active is None:
                raise ValueError("member_unavailable")
            connection.execute(
                """INSERT INTO link_age_classifications(
                       identity_id,age_band,source,confirmed_by
                   ) VALUES (%s,%s,%s,%s)
                   ON CONFLICT (identity_id) DO UPDATE SET
                     age_band=EXCLUDED.age_band,
                     source=EXCLUDED.source,
                     confirmed_by=EXCLUDED.confirmed_by,
                     updated_at=CURRENT_TIMESTAMP""",
                (target, band, source_value, confirmer),
            )
            connection.commit()
    except (ValueError, PermissionError, authority.HumanAuthorityRequired):
        raise
    except Exception as exc:
        raise LinkYouthSafetyUnavailable("link_age_classification_write_failed") from exc
    return {
        "identity_id": target,
        "age_band": band,
        "source": source_value,
        "human_authority_final": True,
    }

def age_band(identity_id: object) -> str | None:
    identity = _uuid(identity_id, "invalid_identity")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT age_band FROM link_age_classifications
                   WHERE identity_id=%s LIMIT 1""",
                (identity,),
            ).fetchone()
    except Exception as exc:
        raise LinkYouthSafetyUnavailable("link_age_classification_read_failed") from exc
    return str(row[0]) if row else None

def contact_policy(first_id: object, second_id: object) -> dict[str, object]:
    first = _uuid(first_id, "invalid_identity")
    second = _uuid(second_id, "invalid_identity")
    if first == second:
        return {"allowed": False, "reason": "same_identity"}
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT identity_id,age_band FROM link_age_classifications
                   WHERE identity_id IN (%s,%s)""",
                (first, second),
            ).fetchall()
    except Exception as exc:
        raise LinkYouthSafetyUnavailable("link_youth_policy_read_failed") from exc
    bands = {str(row[0]): str(row[1]) for row in rows}
    first_band = bands.get(first)
    second_band = bands.get(second)
    if first_band is None or second_band is None:
        return {
            "allowed": True,
            "reason": "age_proof_unresolved",
            "resolved": False,
            "first_band": first_band,
            "second_band": second_band,
        }
    cross_age = {first_band, second_band} == {"minor", "adult"}
    return {
        "allowed": not cross_age,
        "reason": "youth_contact_restricted" if cross_age else "age_policy_clear",
        "resolved": True,
        "first_band": first_band,
        "second_band": second_band,
    }

def require_contact_allowed(first_id: object, second_id: object) -> dict[str, object]:
    policy = contact_policy(first_id, second_id)
    if policy["allowed"] is not True:
        raise ValueError("youth_contact_restricted")
    return policy
