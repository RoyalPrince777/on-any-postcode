"""Evidence and claim runtime for the Koradaso truth foundation."""
from __future__ import annotations

import hashlib
from uuid import UUID, uuid4

from . import postgres_db

WRITE_PERMISSION = "KORADASO_RECORD_EVIDENCE"
VALID_PRIVACY = frozenset({"ME", "ROYAL_HOUSE", "FAMILY", "COMMUNITY", "PUBLIC"})
VALID_STATUS = frozenset({
    "DOCUMENTED", "SCHOLARLY", "FAMILY_CONFIRMED",
    "ORAL_TRADITION", "CONTESTED", "RESEARCHING",
})
VALID_RELATIONS = frozenset({"SUPPORTS", "CONTRADICTS", "CONTEXT"})


class KoradasoEvidenceDenied(PermissionError):
    pass


def _identity(value: object) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_identity") from exc


def _has_permission(connection, identity: UUID) -> bool:
    return bool(connection.execute(
        """SELECT 1 FROM oap_identity_roles ir
           JOIN oap_role_permissions rp ON rp.role_id=ir.role_id
           JOIN oap_identities i ON i.identity_id=ir.identity_id
           WHERE ir.identity_id=%s AND rp.permission_id=%s
             AND i.status='ACTIVE' LIMIT 1""",
        (identity, WRITE_PERMISSION),
    ).fetchone())


def record_evidence(*, actor_id: object, evidence_type: str, title: str,
                    original_bytes: bytes, original_language: str,
                    privacy_scope: str, source_uri: str | None = None) -> dict[str, object]:
    actor = _identity(actor_id)
    privacy = str(privacy_scope).upper()
    if privacy not in VALID_PRIVACY:
        raise ValueError("invalid_privacy_scope")
    if not original_bytes:
        raise ValueError("original_evidence_required")
    digest = hashlib.sha256(original_bytes).hexdigest()
    evidence_id = uuid4()
    with postgres_db.connect() as connection:
        if not _has_permission(connection, actor):
            raise KoradasoEvidenceDenied("koradaso_evidence_permission_required")
        connection.execute(
            """INSERT INTO koradaso_evidence
               (evidence_id,evidence_type,title,source_uri,original_language,
                original_hash,privacy_scope,created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (evidence_id, evidence_type.strip(), title.strip(), source_uri,
             original_language.strip(), digest, privacy, actor),
        )
        connection.execute(
            """INSERT INTO koradaso_evidence_versions
               (version_id,evidence_id,version_number,content_hash,change_kind,
                language,created_by)
               VALUES (%s,%s,1,%s,'ORIGINAL',%s,%s)""",
            (uuid4(), evidence_id, digest, original_language.strip(), actor),
        )
        connection.commit()
    return {"evidence_id": str(evidence_id), "original_hash": digest,
            "privacy_scope": privacy}


def record_claim(*, actor_id: object, subject_kind: str, subject_ref: str,
                 predicate: str, object_value: str, status: str,
                 confidence: float, privacy_scope: str) -> dict[str, object]:
    actor = _identity(actor_id)
    state, privacy = str(status).upper(), str(privacy_scope).upper()
    if state not in VALID_STATUS:
        raise ValueError("invalid_claim_status")
    if privacy not in VALID_PRIVACY:
        raise ValueError("invalid_privacy_scope")
    if not 0 <= float(confidence) <= 1:
        raise ValueError("invalid_confidence")
    claim_id = uuid4()
    with postgres_db.connect() as connection:
        if not _has_permission(connection, actor):
            raise KoradasoEvidenceDenied("koradaso_evidence_permission_required")
        connection.execute(
            """INSERT INTO koradaso_claims
               (claim_id,subject_kind,subject_ref,predicate,object_value,status,
                confidence,privacy_scope,created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (claim_id, subject_kind.strip(), subject_ref.strip(), predicate.strip(),
             object_value.strip(), state, float(confidence), privacy, actor),
        )
        connection.commit()
    return {"claim_id": str(claim_id), "status": state,
            "privacy_scope": privacy, "human_confirmed": False}


def link_evidence(*, actor_id: object, claim_id: object, evidence_id: object,
                  relation: str) -> None:
    actor = _identity(actor_id)
    try:
        claim, evidence = UUID(str(claim_id)), UUID(str(evidence_id))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_claim_or_evidence") from exc
    relation_value = str(relation).upper()
    if relation_value not in VALID_RELATIONS:
        raise ValueError("invalid_evidence_relation")
    with postgres_db.connect() as connection:
        if not _has_permission(connection, actor):
            raise KoradasoEvidenceDenied("koradaso_evidence_permission_required")
        scopes = connection.execute(
            """SELECT c.privacy_scope,e.privacy_scope
               FROM koradaso_claims c CROSS JOIN koradaso_evidence e
               WHERE c.claim_id=%s AND e.evidence_id=%s FOR UPDATE""",
            (claim, evidence),
        ).fetchone()
        if not scopes:
            raise ValueError("claim_or_evidence_not_found")
        # A public/community claim must never expose a more-private source by implication.
        rank = {"ME": 0, "ROYAL_HOUSE": 1, "FAMILY": 2, "COMMUNITY": 3, "PUBLIC": 4}
        if rank[str(scopes[0])] > rank[str(scopes[1])]:
            raise KoradasoEvidenceDenied("claim_scope_exceeds_evidence_scope")
        connection.execute(
            """INSERT INTO koradaso_claim_evidence(claim_id,evidence_id,relation)
               VALUES (%s,%s,%s)
               ON CONFLICT (claim_id,evidence_id) DO UPDATE SET relation=EXCLUDED.relation""",
            (claim, evidence, relation_value),
        )
        connection.commit()


def append_evidence_version(*, actor_id: object, evidence_id: object,
                            content_bytes: bytes, change_kind: str,
                            language: str | None = None) -> dict[str, object]:
    actor = _identity(actor_id)
    try:
        evidence = UUID(str(evidence_id))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_evidence_id") from exc
    kind = str(change_kind).upper()
    if kind not in {"TRANSCRIPTION", "TRANSLATION", "INTERPRETATION", "CORRECTION"}:
        raise ValueError("invalid_evidence_change_kind")
    if not content_bytes:
        raise ValueError("evidence_version_content_required")
    digest = hashlib.sha256(content_bytes).hexdigest()
    with postgres_db.connect() as connection:
        if not _has_permission(connection, actor):
            raise KoradasoEvidenceDenied("koradaso_evidence_permission_required")
        row = connection.execute(
            """SELECT COALESCE(MAX(v.version_number),0),e.privacy_scope
               FROM koradaso_evidence e
               LEFT JOIN koradaso_evidence_versions v ON v.evidence_id=e.evidence_id
               WHERE e.evidence_id=%s GROUP BY e.privacy_scope FOR UPDATE""",
            (evidence,),
        ).fetchone()
        if not row:
            raise ValueError("evidence_not_found")
        version_number = int(row[0]) + 1
        connection.execute(
            """INSERT INTO koradaso_evidence_versions
               (version_id,evidence_id,version_number,content_hash,change_kind,
                language,created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (uuid4(), evidence, version_number, digest, kind, language, actor),
        )
        connection.commit()
    return {"evidence_id": str(evidence), "version_number": version_number,
            "content_hash": digest, "change_kind": kind}
