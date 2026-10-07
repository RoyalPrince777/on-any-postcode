"""Koradaso explicit release-consent boundary.

Consent authorises a specific reviewed claim for public projection. It does not
grant Royal status, ancestry, publication permission, or any SIKA authority.
"""
from __future__ import annotations

from uuid import UUID, uuid4

from . import postgres_db
from .koradaso_evidence import _audit

RELEASE_PERMISSION = "KORADASO_RELEASE_HERITAGE"


class KoradasoReleaseDenied(PermissionError):
    pass


def _uuid(value: object, field: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{field}") from exc


def _can_release(connection, actor: UUID) -> bool:
    return bool(
        connection.execute(
            """SELECT 1 FROM oap_identity_roles ir
               JOIN oap_role_permissions rp ON rp.role_id=ir.role_id
               JOIN oap_identities i ON i.identity_id=ir.identity_id
               WHERE ir.identity_id=%s AND rp.permission_id=%s
                 AND i.status='ACTIVE' LIMIT 1""",
            (actor, RELEASE_PERMISSION),
        ).fetchone()
    )


def grant_release(*, actor_id: object, claim_id: object, reason: str) -> dict[str, object]:
    actor = _uuid(actor_id, "actor_id")
    claim = _uuid(claim_id, "claim_id")
    reason_value = str(reason or "").strip()
    if not reason_value:
        raise ValueError("release_reason_required")

    with postgres_db.connect() as connection:
        if not _can_release(connection, actor):
            raise KoradasoReleaseDenied("koradaso_release_permission_required")
        claim_row = connection.execute(
            "SELECT privacy_scope FROM koradaso_claims WHERE claim_id=%s FOR UPDATE",
            (claim,),
        ).fetchone()
        if not claim_row:
            raise ValueError("claim_not_found")
        reviewed = connection.execute(
            "SELECT 1 FROM koradaso_claim_reviews WHERE claim_id=%s LIMIT 1",
            (claim,),
        ).fetchone()
        if not reviewed:
            raise KoradasoReleaseDenied("human_review_required_before_release")
        active = connection.execute(
            """SELECT release_id FROM koradaso_release_consents
               WHERE claim_id=%s AND revoked_at IS NULL LIMIT 1""",
            (claim,),
        ).fetchone()
        if active:
            raise KoradasoReleaseDenied("active_release_already_exists")

        release_id = uuid4()
        connection.execute(
            """INSERT INTO koradaso_release_consents
               (release_id,claim_id,released_by,reason)
               VALUES (%s,%s,%s,%s)""",
            (release_id, claim, actor, reason_value),
        )
        _audit(
            connection,
            actor=actor,
            action="KORADASO_HERITAGE_RELEASE_GRANTED",
            target=str(release_id),
            metadata={"release_id": str(release_id), "claim_id": str(claim)},
        )
        connection.commit()
    return {
        "release_id": str(release_id),
        "claim_id": str(claim),
        "released": True,
        "royal_status_granted": False,
    }


def revoke_release(*, actor_id: object, release_id: object, reason: str) -> dict[str, object]:
    actor = _uuid(actor_id, "actor_id")
    release = _uuid(release_id, "release_id")
    reason_value = str(reason or "").strip()
    if not reason_value:
        raise ValueError("release_revocation_reason_required")

    with postgres_db.connect() as connection:
        if not _can_release(connection, actor):
            raise KoradasoReleaseDenied("koradaso_release_permission_required")
        row = connection.execute(
            """SELECT claim_id,revoked_at FROM koradaso_release_consents
               WHERE release_id=%s FOR UPDATE""",
            (release,),
        ).fetchone()
        if not row:
            raise ValueError("release_not_found")
        if row[1] is not None:
            raise ValueError("release_already_revoked")
        connection.execute(
            """UPDATE koradaso_release_consents
               SET revoked_at=CURRENT_TIMESTAMP, revoked_by=%s,
                   revocation_reason=%s
               WHERE release_id=%s""",
            (actor, reason_value, release),
        )
        _audit(
            connection,
            actor=actor,
            action="KORADASO_HERITAGE_RELEASE_REVOKED",
            target=str(release),
            metadata={"release_id": str(release), "claim_id": str(row[0])},
        )
        connection.commit()
    return {"release_id": str(release), "revoked": True}
