"""Evidence-bound acceptance receipts for the final OAP Music Civilization gates.

The software records externally obtained acceptance evidence for Golden Track,
Player, Radio, Live, Recovery and Distribution. Presence of a receipt is not
itself a copyright/licence decision: each receipt must bind to an owned release,
the evidence bytes supplied, and a named human approval reference.
"""
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from uuid import UUID

from . import postgres_db

ACCEPTANCE_MIGRATION_VERSION = "0012_oap_music_acceptance_receipts"
ACCEPTANCE_KINDS = frozenset({
    "GOLDEN_TRACK",
    "PLAYER",
    "RADIO",
    "LIVE",
    "RECOVERY",
    "DISTRIBUTION",
})
MAX_REF = 240

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_acceptance_receipts (
        acceptance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id)
            ON DELETE CASCADE,
        acceptance_kind TEXT NOT NULL CHECK (acceptance_kind IN
            ('GOLDEN_TRACK','PLAYER','RADIO','LIVE','RECOVERY','DISTRIBUTION')),
        evidence_sha256 TEXT NOT NULL CHECK (length(evidence_sha256)=64),
        evidence_reference TEXT NOT NULL,
        human_approval_reference TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(owner_identity_id,release_id,acceptance_kind,evidence_sha256)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_acceptance_owner_release
        ON oap_music_acceptance_receipts(
            owner_identity_id,release_id,created_at DESC
        )""",
)


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _text(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"invalid_{name}")
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > MAX_REF:
        raise ValueError(f"invalid_{name}")
    return cleaned


def software_completion_gate(receipts: object) -> dict[str, object]:
    """Report only receipt coverage; never convert it into public execution."""
    rows = receipts if isinstance(receipts, list) else []
    present = {
        row.get("acceptance_kind")
        for row in rows
        if isinstance(row, Mapping) and row.get("acceptance_kind") in ACCEPTANCE_KINDS
    }
    missing = sorted(ACCEPTANCE_KINDS - present)
    return {
        "acceptance_receipt_coverage_complete": not missing,
        "present_acceptance_kinds": sorted(present),
        "missing_acceptance_kinds": missing,
        "public_playback_enabled": False,
        "public_radio_enabled": False,
        "public_live_enabled": False,
        "external_distribution_enabled": False,
        "rights_verified_by_software": False,
        "human_authority_final": True,
    }


class MusicAcceptanceStore:
    """Immutable owner-scoped acceptance evidence store."""

    def ensure_schema(self) -> None:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()

    def append(
        self, *, owner_identity_id: object, release_id: object,
        acceptance_kind: object, evidence_bytes: object,
        evidence_reference: object, human_approval_reference: object,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        if not isinstance(acceptance_kind, str) or acceptance_kind not in ACCEPTANCE_KINDS:
            raise ValueError("invalid_acceptance_kind")
        if not isinstance(evidence_bytes, bytes) or not evidence_bytes:
            raise ValueError("invalid_acceptance_evidence")
        if len(evidence_bytes) > 8_388_608:
            raise ValueError("acceptance_evidence_too_large")
        evidence_ref = _text(evidence_reference, "evidence_reference")
        approval_ref = _text(
            human_approval_reference,
            "human_approval_reference",
        )
        digest = hashlib.sha256(evidence_bytes).hexdigest()
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_music_releases
                   WHERE release_id=%s AND owner_identity_id=%s FOR UPDATE""",
                (release, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("acceptance_release_not_owned")
            row = connection.execute(
                """INSERT INTO oap_music_acceptance_receipts(
                   owner_identity_id,release_id,acceptance_kind,evidence_sha256,
                   evidence_reference,human_approval_reference)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (
                     owner_identity_id,release_id,acceptance_kind,evidence_sha256
                   ) DO UPDATE SET evidence_reference=EXCLUDED.evidence_reference,
                     human_approval_reference=EXCLUDED.human_approval_reference
                   RETURNING acceptance_id""",
                (owner, release, acceptance_kind, digest, evidence_ref, approval_ref),
            ).fetchone()
            connection.commit()
        return {
            "acceptance_id": str(row[0]),
            "release_id": release,
            "acceptance_kind": acceptance_kind,
            "evidence_sha256": digest,
            "public_execution_enabled": False,
            "rights_verified_by_software": False,
        }

    def read(
        self, *, owner_identity_id: object, release_id: object
    ) -> list[dict[str, object]]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        with postgres_db.connect(readonly=True) as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_music_releases
                   WHERE release_id=%s AND owner_identity_id=%s""",
                (release, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("acceptance_release_not_owned")
            rows = connection.execute(
                """SELECT acceptance_id,acceptance_kind,evidence_sha256,
                          evidence_reference,human_approval_reference,created_at
                   FROM oap_music_acceptance_receipts
                   WHERE owner_identity_id=%s AND release_id=%s
                   ORDER BY created_at,acceptance_id""",
                (owner, release),
            ).fetchall()
        return [
            {
                "acceptance_id": str(r[0]),
                "acceptance_kind": str(r[1]),
                "evidence_sha256": str(r[2]),
                "evidence_reference": str(r[3]),
                "human_approval_reference": str(r[4]),
                "created_at": r[5].isoformat(),
            }
            for r in rows
        ]
