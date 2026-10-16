"""Fingerprint the exact reviewed claim state for release consent.

Call only while holding the claim row FOR UPDATE in the caller's transaction.
"""
from __future__ import annotations

import hashlib
import json


def claim_fingerprint(connection, claim_id: object) -> str:
    row = connection.execute(
        """SELECT subject_kind,subject_ref,predicate,object_value,status,
                  confidence,privacy_scope,created_by
           FROM koradaso_claims WHERE claim_id=%s""",
        (claim_id,),
    ).fetchone()
    if not row:
        raise ValueError("claim_not_found")
    reviews = connection.execute(
        """SELECT review_id,from_status,to_status,reason,reviewer_id
           FROM koradaso_claim_reviews WHERE claim_id=%s
           ORDER BY created_at,review_id""",
        (claim_id,),
    ).fetchall()
    if not reviews:
        raise ValueError("human_review_required_before_release")
    evidence = connection.execute(
        """SELECT ce.evidence_id,ce.relation,ev.original_hash,
                  ev.privacy_scope
           FROM koradaso_claim_evidence ce
           JOIN koradaso_evidence ev ON ev.evidence_id=ce.evidence_id
           WHERE ce.claim_id=%s ORDER BY ce.evidence_id""",
        (claim_id,),
    ).fetchall()
    versions = connection.execute(
        """SELECT v.evidence_id,v.version_number,v.content_hash,v.change_kind
           FROM koradaso_evidence_versions v
           JOIN koradaso_claim_evidence ce ON ce.evidence_id=v.evidence_id
           WHERE ce.claim_id=%s ORDER BY v.evidence_id,v.version_number""",
        (claim_id,),
    ).fetchall()
    payload = {
        "claim": [str(v) for v in row],
        "reviews": [[str(v) for v in item] for item in reviews],
        "evidence": [[str(v) for v in item] for item in evidence],
        "versions": [[str(v) for v in item] for item in versions],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
