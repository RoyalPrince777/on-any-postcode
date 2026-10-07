"""Koradaso Gate-25 truth foundation.

Creates only first-party domain tables on top of canonical OAP identities and audit.
It grants no Royal status, issues no invitation, publishes no evidence and creates no
SIKA value. Installation is explicit and read-back is non-mutating.
"""
from __future__ import annotations

import hashlib

from . import postgres_db

MIGRATION_VERSION = "koradaso_truth_foundation_v3"

STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS koradaso_people (
        person_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        oap_identity_id UUID REFERENCES oap_identities(identity_id),
        display_name TEXT NOT NULL,
        record_state TEXT NOT NULL DEFAULT 'RECORDED'
            CHECK (record_state IN ('RECORDED','DISPUTED','ARCHIVED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS koradaso_evidence (
        evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        evidence_type TEXT NOT NULL,
        title TEXT NOT NULL,
        source_uri TEXT,
        original_language TEXT,
        original_hash TEXT NOT NULL,
        privacy_scope TEXT NOT NULL
            CHECK (privacy_scope IN ('ME','ROYAL_HOUSE','FAMILY','COMMUNITY','PUBLIC')),
        created_by UUID REFERENCES oap_identities(identity_id),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS koradaso_evidence_versions (
        version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        evidence_id UUID NOT NULL REFERENCES koradaso_evidence(evidence_id) ON DELETE RESTRICT,
        version_number INTEGER NOT NULL CHECK (version_number >= 1),
        content_hash TEXT NOT NULL,
        change_kind TEXT NOT NULL CHECK (change_kind IN ('ORIGINAL','TRANSCRIPTION','TRANSLATION','INTERPRETATION','CORRECTION')),
        language TEXT,
        created_by UUID NOT NULL REFERENCES oap_identities(identity_id),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (evidence_id,version_number))""",
    """CREATE TABLE IF NOT EXISTS koradaso_claims (
        claim_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        subject_kind TEXT NOT NULL,
        subject_ref TEXT NOT NULL,
        predicate TEXT NOT NULL,
        object_value TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'RESEARCHING'
            CHECK (status IN ('DOCUMENTED','SCHOLARLY','FAMILY_CONFIRMED',
                              'ORAL_TRADITION','CONTESTED','RESEARCHING')),
        confidence DOUBLE PRECISION CHECK (confidence >= 0 AND confidence <= 1),
        privacy_scope TEXT NOT NULL
            CHECK (privacy_scope IN ('ME','ROYAL_HOUSE','FAMILY','COMMUNITY','PUBLIC')),
        created_by UUID REFERENCES oap_identities(identity_id),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS koradaso_claim_evidence (
        claim_id UUID NOT NULL REFERENCES koradaso_claims(claim_id) ON DELETE CASCADE,
        evidence_id UUID NOT NULL REFERENCES koradaso_evidence(evidence_id) ON DELETE RESTRICT,
        relation TEXT NOT NULL CHECK (relation IN ('SUPPORTS','CONTRADICTS','CONTEXT')),
        PRIMARY KEY (claim_id,evidence_id))""",
    """CREATE TABLE IF NOT EXISTS koradaso_claim_reviews (
        review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claim_id UUID NOT NULL REFERENCES koradaso_claims(claim_id) ON DELETE RESTRICT,
        reviewer_id UUID NOT NULL REFERENCES oap_identities(identity_id),
        from_status TEXT NOT NULL,
        to_status TEXT NOT NULL,
        reason TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS koradaso_release_consents (
        release_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claim_id UUID NOT NULL REFERENCES koradaso_claims(claim_id) ON DELETE RESTRICT,
        released_by UUID NOT NULL REFERENCES oap_identities(identity_id),
        reason TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        revoked_at TIMESTAMPTZ,
        revoked_by UUID REFERENCES oap_identities(identity_id),
        revocation_reason TEXT)""",
    """CREATE UNIQUE INDEX IF NOT EXISTS ux_koradaso_active_release
        ON koradaso_release_consents(claim_id) WHERE revoked_at IS NULL""",
    """CREATE TABLE IF NOT EXISTS koradaso_publications (
        publication_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claim_id UUID NOT NULL REFERENCES koradaso_claims(claim_id) ON DELETE RESTRICT,
        published_by UUID NOT NULL REFERENCES oap_identities(identity_id),
        public_summary TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        revoked_at TIMESTAMPTZ)""",
    """CREATE TABLE IF NOT EXISTS koradaso_relationships (
        relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        from_person_id UUID NOT NULL REFERENCES koradaso_people(person_id) ON DELETE RESTRICT,
        relationship_type TEXT NOT NULL,
        to_person_id UUID NOT NULL REFERENCES koradaso_people(person_id) ON DELETE RESTRICT,
        valid_from DATE, valid_until DATE,
        claim_id UUID REFERENCES koradaso_claims(claim_id) ON DELETE RESTRICT,
        CHECK (from_person_id <> to_person_id),
        CHECK (valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from))""",
    """CREATE TABLE IF NOT EXISTS koradaso_invites (
        invite_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        invited_by UUID NOT NULL REFERENCES oap_identities(identity_id),
        token_hash TEXT NOT NULL UNIQUE,
        expires_at TIMESTAMPTZ NOT NULL,
        claimed_by UUID REFERENCES oap_identities(identity_id),
        claimed_at TIMESTAMPTZ,
        revoked_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK ((claimed_by IS NULL AND claimed_at IS NULL) OR
               (claimed_by IS NOT NULL AND claimed_at IS NOT NULL)))""",
    "CREATE INDEX IF NOT EXISTS ix_koradaso_claim_subject ON koradaso_claims(subject_kind,subject_ref)",
    "CREATE INDEX IF NOT EXISTS ix_koradaso_relationship_from ON koradaso_relationships(from_person_id,relationship_type)",
    """INSERT INTO oap_permissions(permission_id,description)
        VALUES ('KORADASO_ISSUE_INVITE','Issue or revoke Koradaso Royal House access invitations')
        ON CONFLICT (permission_id) DO NOTHING""",
    """INSERT INTO oap_permissions(permission_id,description)
        VALUES ('KORADASO_RECORD_EVIDENCE','Record Koradaso evidence and proposed claims')
        ON CONFLICT (permission_id) DO NOTHING""",
    """INSERT INTO oap_permissions(permission_id,description)
        VALUES ('KORADASO_REVIEW_CLAIMS','Review Koradaso claims and change evidence status')
        ON CONFLICT (permission_id) DO NOTHING""",
    """INSERT INTO oap_permissions(permission_id,description)
        VALUES ('KORADASO_RELEASE_HERITAGE','Explicitly release reviewed Koradaso heritage for public projection')
        ON CONFLICT (permission_id) DO NOTHING""",
    """INSERT INTO oap_permissions(permission_id,description)
        VALUES ('KORADASO_PUBLISH_HERITAGE','Publish reviewed Koradaso heritage projections')
        ON CONFLICT (permission_id) DO NOTHING""",
    """INSERT INTO oap_permissions(permission_id,description) VALUES
        ('KORADASO_READ_ROYAL_EVIDENCE','Read Koradaso Royal House evidence'),
        ('KORADASO_READ_FAMILY_EVIDENCE','Read Koradaso family evidence'),
        ('KORADASO_READ_COMMUNITY_EVIDENCE','Read Koradaso community evidence')
        ON CONFLICT (permission_id) DO NOTHING""",
)
REQUIRED_TABLES = (
    "koradaso_people", "koradaso_evidence", "koradaso_evidence_versions", "koradaso_claims",
    "koradaso_claim_evidence", "koradaso_claim_reviews", "koradaso_release_consents", "koradaso_publications", "koradaso_relationships", "koradaso_invites",
)
PREREQUISITES = ("oap_identities", "audit_events")
MIGRATION_CHECKSUM = hashlib.sha256("\n".join(STATEMENTS).encode()).hexdigest()


class KoradasoSchemaUnavailable(RuntimeError):
    pass


def _regclass(connection, name: str) -> bool:
    row = connection.execute("SELECT to_regclass(%s)", (f"public.{name}",)).fetchone()
    return bool(row and row[0])


def readback() -> dict[str, object]:
    try:
        with postgres_db.connect(readonly=True) as connection:
            prerequisites = {name: _regclass(connection, name) for name in PREREQUISITES}
            tables = {name: _regclass(connection, name) for name in REQUIRED_TABLES}
    except Exception as exc:
        raise KoradasoSchemaUnavailable("koradaso_schema_readback_failed") from exc
    return {
        "migration": MIGRATION_VERSION,
        "checksum": MIGRATION_CHECKSUM,
        "prerequisites": prerequisites,
        "tables": tables,
        "prerequisites_ready": all(prerequisites.values()),
        "schema_ready": all(tables.values()),
        "royal_status_granted": False,
        "invite_issued": False,
        "evidence_published": False,
        "sika_issued": False,
    }


def install(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("explicit_confirmation_required")
    if dry_run:
        return {
            "migration": MIGRATION_VERSION,
            "checksum": MIGRATION_CHECKSUM,
            "schema_ready": False,
            "dry_run": True,
            "statement_count": len(STATEMENTS),
        }
    try:
        with postgres_db.connect() as connection:
            missing = [name for name in PREREQUISITES if not _regclass(connection, name)]
            if missing:
                raise KoradasoSchemaUnavailable(
                    "koradaso_schema_prerequisites_missing:" + ",".join(missing)
                )
            for statement in STATEMENTS:
                connection.execute(statement)
            connection.commit()
    except KoradasoSchemaUnavailable:
        raise
    except Exception as exc:
        raise KoradasoSchemaUnavailable("koradaso_schema_install_failed") from exc

    proof = readback()
    if proof["schema_ready"] is not True:
        raise KoradasoSchemaUnavailable("koradaso_schema_readback_incomplete")
    return {**proof, "dry_run": False, "statement_count": len(STATEMENTS)}
