"""Founder-private OAP Music company and rights registry.

Records evidence references only, not legal verification or distribution authority.
No request-time schema creation, public API, or stored contract document bytes.
"""
from __future__ import annotations

import hashlib
import re
from uuid import UUID

from . import postgres_db

MIGRATION_VERSION = "0015_music_company_rights_registry"
KINDS = frozenset({"company", "record_label", "isrc_prefix", "release_barcode",
                   "artist_contract", "rights_membership"})
STATES = frozenset({"PENDING", "EVIDENCE_REQUIRED", "VERIFIED", "REJECTED", "REVOKED"})
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_company_rights_registry (
        registry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        kind TEXT NOT NULL CHECK (kind IN
          ('company','record_label','isrc_prefix','release_barcode','artist_contract','rights_membership')),
        reference TEXT NOT NULL,
        display_name TEXT NOT NULL,
        evidence_sha256 CHAR(64),
        evidence_reference TEXT,
        state TEXT NOT NULL DEFAULT 'PENDING' CHECK (state IN
          ('PENDING','EVIDENCE_REQUIRED','VERIFIED','REJECTED','REVOKED')),
        reviewer_identity_id UUID REFERENCES users(id) ON DELETE RESTRICT,
        reviewed_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(owner_identity_id,kind,reference),
        CHECK (state <> 'VERIFIED' OR
            (evidence_sha256 IS NOT NULL AND evidence_reference IS NOT NULL
             AND reviewer_identity_id IS NOT NULL AND reviewed_at IS NOT NULL))
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_registry_owner_kind
       ON oap_music_company_rights_registry(owner_identity_id,kind,state)""",
)
_SHA = re.compile(r"^[0-9a-f]{64}$")


def _uuid(value):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("invalid_identity") from exc


def _text(value, field, limit=240):
    if not isinstance(value, str):
        raise ValueError("invalid_" + field)
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > limit:
        raise ValueError("invalid_" + field)
    return cleaned


def validate_record(*, kind, reference, display_name, evidence_sha256=None,
                    evidence_reference=None):
    if kind not in KINDS:
        raise ValueError("invalid_registry_kind")
    ref = _text(reference, "reference", 120)
    name = _text(display_name, "display_name", 180)
    digest = None
    evidence = None
    if evidence_sha256 is not None or evidence_reference is not None:
        if not isinstance(evidence_sha256, str) or not _SHA.fullmatch(evidence_sha256):
            raise ValueError("invalid_evidence_sha256")
        evidence = _text(evidence_reference, "evidence_reference")
        digest = evidence_sha256
    return kind, ref, name, digest, evidence


class MusicCompanyRightsRegistry:
    """Private, owner-scoped records; only separately authenticated callers may use this store."""

    def add_pending(self, *, owner_identity_id, kind, reference, display_name,
                    evidence_sha256=None, evidence_reference=None):
        owner = _uuid(owner_identity_id)
        kind, ref, name, digest, evidence = validate_record(
            kind=kind, reference=reference, display_name=display_name,
            evidence_sha256=evidence_sha256, evidence_reference=evidence_reference)
        with postgres_db.connect() as conn:
            row = conn.execute(
                """INSERT INTO oap_music_company_rights_registry
                   (owner_identity_id,kind,reference,display_name,evidence_sha256,evidence_reference)
                   VALUES (%s,%s,%s,%s,%s,%s) RETURNING registry_id""",
                (owner, kind, ref, name, digest, evidence),
            ).fetchone()
            conn.commit()
        return {"registry_id": str(row[0]), "state": "PENDING",
                "authority_verified": False, "public_distribution_enabled": False}

    def list_private(self, *, owner_identity_id):
        owner = _uuid(owner_identity_id)
        with postgres_db.connect(readonly=True) as conn:
            rows = conn.execute(
                """SELECT registry_id,kind,reference,display_name,state,created_at
                   FROM oap_music_company_rights_registry
                   WHERE owner_identity_id=%s ORDER BY created_at,registry_id""",
                (owner,),
            ).fetchall()
        return [{"registry_id": str(r[0]), "kind": r[1], "reference": r[2],
                 "display_name": r[3], "state": r[4], "created_at": str(r[5])}
                for r in rows]

    def review(self, *, owner_identity_id, registry_id, reviewer_identity_id,
               decision):
        owner = _uuid(owner_identity_id)
        record_id = _uuid(registry_id)
        reviewer = _uuid(reviewer_identity_id)
        if decision not in {"VERIFIED", "REJECTED", "EVIDENCE_REQUIRED", "REVOKED"}:
            raise ValueError("invalid_review_decision")
        with postgres_db.connect() as conn:
            row = conn.execute(
                """UPDATE oap_music_company_rights_registry
                   SET state=%s,reviewer_identity_id=%s,reviewed_at=CURRENT_TIMESTAMP,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE registry_id=%s AND owner_identity_id=%s
                     AND state <> 'REVOKED'
                     AND (%s <> 'VERIFIED' OR
                          (evidence_sha256 IS NOT NULL AND evidence_reference IS NOT NULL))
                   RETURNING registry_id""",
                (decision, reviewer, record_id, owner, decision),
            ).fetchone()
            if row is None:
                raise PermissionError("registry_not_owned_or_evidence_missing")
            conn.commit()
        return {"registry_id": str(row[0]), "state": decision,
                "authority_verified": False, "public_distribution_enabled": False}
