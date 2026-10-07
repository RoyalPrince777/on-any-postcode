"""Human-only review boundary for Koradaso claims."""
from __future__ import annotations
from uuid import UUID, uuid4

from . import postgres_db
from .koradaso_evidence import VALID_STATUS, _audit

REVIEW_PERMISSION = "KORADASO_REVIEW_CLAIMS"

class KoradasoReviewDenied(PermissionError):
    pass

def _uuid(value: object) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_review_identity_or_claim") from exc

def _can_review(connection, reviewer: UUID) -> bool:
    return bool(connection.execute(
        """SELECT 1 FROM oap_identity_roles ir
           JOIN oap_role_permissions rp ON rp.role_id=ir.role_id
           JOIN oap_identities i ON i.identity_id=ir.identity_id
           WHERE ir.identity_id=%s AND rp.permission_id=%s
             AND i.status='ACTIVE' LIMIT 1""",
        (reviewer, REVIEW_PERMISSION),
    ).fetchone())

def review_claim(*, reviewer_id: object, claim_id: object,
                 to_status: str, reason: str) -> dict[str, object]:
    reviewer, claim = _uuid(reviewer_id), _uuid(claim_id)
    target_status = str(to_status).upper()
    if target_status not in VALID_STATUS:
        raise ValueError("invalid_claim_status")
    reason_value = str(reason or "").strip()
    if not reason_value:
        raise ValueError("review_reason_required")

    with postgres_db.connect() as connection:
        if not _can_review(connection, reviewer):
            raise KoradasoReviewDenied("koradaso_claim_review_permission_required")
        row = connection.execute(
            "SELECT status FROM koradaso_claims WHERE claim_id=%s FOR UPDATE",
            (claim,),
        ).fetchone()
        if not row:
            raise ValueError("claim_not_found")
        from_status = str(row[0])
        if from_status == target_status:
            raise ValueError("claim_status_unchanged")

        review_id = uuid4()
        connection.execute(
            """INSERT INTO koradaso_claim_reviews
               (review_id,claim_id,reviewer_id,from_status,to_status,reason)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (review_id, claim, reviewer, from_status, target_status, reason_value),
        )
        connection.execute(
            "UPDATE koradaso_claims SET status=%s WHERE claim_id=%s",
            (target_status, claim),
        )
        _audit(connection, actor=reviewer, action="KORADASO_CLAIM_REVIEWED",
               target=str(claim),
               metadata={"claim_id": str(claim), "review_id": str(review_id),
                         "from_status": from_status, "to_status": target_status})
        connection.commit()
    return {"claim_id": str(claim), "review_id": str(review_id),
            "from_status": from_status, "to_status": target_status,
            "human_reviewed": True, "royal_status_granted": False}
