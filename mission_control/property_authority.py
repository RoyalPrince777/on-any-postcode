"""Read-only Property authority check in OAP's existing PostgreSQL database.

Evidence issuance, document verification, review and migration are separate gated
work. A reference alone, an ACTIVE flag alone, or merchant certification alone
never confers property advertising rights.
"""
from __future__ import annotations

import hashlib
import json
from uuid import UUID

from . import authority, postgres_db


def verified_advertising_authority(record: dict, evidence_ref: str) -> bool:
    """Require a scoped, independently reviewed, unexpired, non-revoked grant.

    Checks are re-run by the Property lifecycle at approval, publication and
    projection. No network calls or writes; a missing migration denies access.
    """
    try:
        evidence_id = str(UUID(str(evidence_ref)))
        publisher = str(UUID(str(record["publisher_id"])))
        advertiser = str(UUID(str(record["advertiser_id"])))
        property_ref = record["property_ref"]
        country = record["country"]
        if not isinstance(property_ref, str) or not property_ref.strip():
            return False
        if not isinstance(country, str) or not country.strip():
            return False
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT reviewed_by FROM oap_property_advertising_authority
                   WHERE evidence_id=%s AND publisher_id=%s AND advertiser_id=%s
                     AND property_ref=%s AND country=%s AND activity='ADVERTISE'
                     AND status='ACTIVE' AND revoked_at IS NULL
                     AND valid_from<=CURRENT_TIMESTAMP
                     AND valid_until>CURRENT_TIMESTAMP
                     AND reviewed_by<>publisher_id
                     AND reviewed_at IS NOT NULL
                     AND evidence_sha256 ~ '^[0-9a-f]{64}$'
                     AND length(trim(grantor_reference))>0
                   LIMIT 1""",
                (evidence_id, publisher, advertiser, property_ref, country),
            ).fetchone()
            if row is None:
                return False
            # Reviewer must STILL hold canonical active level-zero authority.
            authority.require_human_authority(connection, str(UUID(str(row[0]))))
        return True
    except Exception:  # noqa: BLE001 - invalid/missing/revoked grants deny.
        return False


def revoke_advertising_authority(*, evidence_ref: object, revoked_by: object,
                                 reason: object) -> dict[str, object]:
    """Privately revoke an existing grant and atomically append canonical PG audit.

    No issuing or activation endpoint. Revocation is terminal in migration 0009.
    The caller must supply an authenticated actor, not an identity from request data.
    """
    evidence = str(UUID(str(evidence_ref)))
    reviewer = str(UUID(str(revoked_by)))
    if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 240:
        raise ValueError("invalid_revocation_reason")
    reason_value = reason.strip()
    try:
        with postgres_db.connect() as connection:
            authority.require_human_authority(connection, reviewer)
            result = connection.execute(
                """UPDATE oap_property_advertising_authority
                   SET status='REVOKED', revoked_at=CURRENT_TIMESTAMP
                   WHERE evidence_id=%s AND status IN ('ACTIVE','REVIEW_REQUIRED')
                   RETURNING publisher_id,advertiser_id,property_ref,country""",
                (evidence,),
            ).fetchone()
            if result is None:
                raise ValueError("property_grant_not_revocable")
            # Match existing PostgreSQL audit chain, lock and digest semantics.
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
            previous = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            previous_hash = str(previous[0]) if previous else "GENESIS"
            metadata = {
                "evidence_id": evidence,
                "publisher_id": str(result[0]),
                "advertiser_id": str(result[1]),
                "property_ref": str(result[2]),
                "country": str(result[3]),
                "after_status": "REVOKED",
                "payment_capture_performed": False,
                "public_publishing_performed": False,
            }
            canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
            current_hash = hashlib.sha256(
                (previous_hash + canonical).encode("utf-8")
            ).hexdigest()
            connection.execute(
                """INSERT INTO audit_events(
                    prev_hash,curr_hash,actor_id,actor_type,authority_level,
                    action,target,reason,correlation_id,metadata
                   ) VALUES (%s,%s,%s,'HUMAN_AUTHORITY',0,
                             'PROPERTY_GRANT_REVOKED',%s,%s,%s,%s::jsonb)""",
                (previous_hash, current_hash, reviewer,
                 f"property_grant:{evidence}", reason_value, evidence, canonical),
            )
            connection.commit()
        return {
            "evidence_id": evidence,
            "state": "REVOKED",
            "audit_hash": current_hash,
            "payment_capture_performed": False,
            "public_publishing_performed": False,
        }
    except (ValueError, PermissionError):
        raise
    except Exception as exc:
        raise RuntimeError("property_revocation_unavailable") from exc
