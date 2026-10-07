"""Governed public projection of reviewed Koradaso heritage claims."""
from __future__ import annotations

from uuid import UUID, uuid4

from . import postgres_db
from .koradaso_evidence import _audit

PUBLISH_PERMISSION = "KORADASO_PUBLISH_HERITAGE"
PUBLISHABLE_STATUS = frozenset({"DOCUMENTED", "SCHOLARLY", "FAMILY_CONFIRMED", "ORAL_TRADITION", "CONTESTED"})

class KoradasoPublicationDenied(PermissionError):
    pass

def _uuid(value: object) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_publication_identity_or_claim") from exc

def _can_publish(connection, actor: UUID) -> bool:
    return bool(connection.execute(
        """SELECT 1 FROM oap_identity_roles ir
           JOIN oap_role_permissions rp ON rp.role_id=ir.role_id
           JOIN oap_identities i ON i.identity_id=ir.identity_id
           WHERE ir.identity_id=%s AND rp.permission_id=%s
             AND i.status='ACTIVE' LIMIT 1""",
        (actor, PUBLISH_PERMISSION),
    ).fetchone())

def publish_claim(*, publisher_id: object, claim_id: object,
                  public_summary: str) -> dict[str, object]:
    publisher, claim = _uuid(publisher_id), _uuid(claim_id)
    summary = str(public_summary or "").strip()
    if not summary:
        raise ValueError("public_summary_required")
    with postgres_db.connect() as connection:
        if not _can_publish(connection, publisher):
            raise KoradasoPublicationDenied("koradaso_publish_permission_required")
        row = connection.execute(
            "SELECT status,privacy_scope FROM koradaso_claims WHERE claim_id=%s FOR UPDATE",
            (claim,),
        ).fetchone()
        if not row:
            raise ValueError("claim_not_found")
        status, privacy_scope = str(row[0]), str(row[1])
        if status not in PUBLISHABLE_STATUS:
            raise KoradasoPublicationDenied("claim_not_human_review_ready")
        reviewed = connection.execute(
            "SELECT 1 FROM koradaso_claim_reviews WHERE claim_id=%s LIMIT 1",
            (claim,),
        ).fetchone()
        if not reviewed:
            raise KoradasoPublicationDenied("human_review_required_before_publication")

        publication_id = uuid4()
        connection.execute(
            """INSERT INTO koradaso_publications
               (publication_id,claim_id,published_by,public_summary)
               VALUES (%s,%s,%s,%s)""",
            (publication_id, claim, publisher, summary),
        )
        _audit(connection, actor=publisher, action="KORADASO_HERITAGE_PUBLISHED",
               target=str(publication_id),
               metadata={"publication_id": str(publication_id),
                         "claim_id": str(claim),
                         "source_privacy_scope": privacy_scope})
        connection.commit()
    return {"publication_id": str(publication_id), "claim_id": str(claim),
            "public_summary": summary, "published": True}

def revoke_publication(*, publisher_id: object, publication_id: object,
                       reason: str) -> dict[str, object]:
    publisher, publication = _uuid(publisher_id), _uuid(publication_id)
    reason_value = str(reason or "").strip()
    if not reason_value:
        raise ValueError("revocation_reason_required")
    with postgres_db.connect() as connection:
        if not _can_publish(connection, publisher):
            raise KoradasoPublicationDenied("koradaso_publish_permission_required")
        row = connection.execute(
            """SELECT claim_id,revoked_at FROM koradaso_publications
               WHERE publication_id=%s FOR UPDATE""",
            (publication,),
        ).fetchone()
        if not row:
            raise ValueError("publication_not_found")
        if row[1] is not None:
            raise ValueError("publication_already_revoked")
        connection.execute(
            "UPDATE koradaso_publications SET revoked_at=CURRENT_TIMESTAMP WHERE publication_id=%s",
            (publication,),
        )
        _audit(connection, actor=publisher, action="KORADASO_HERITAGE_REVOKED",
               target=str(publication),
               metadata={"publication_id": str(publication),
                         "claim_id": str(row[0]), "reason": reason_value})
        connection.commit()
    return {"publication_id": str(publication), "revoked": True}
