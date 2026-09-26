"""First-party OAP Records archive for canonical OAP Music releases.

Records preserves owner-scoped release provenance, credits and handoff receipts.
It never grants copyright, starts playback, distributes externally or replaces
OAP Music as the canonical release owner.
"""
from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from . import entertainment_catalogue, postgres_db

RECORDS_MIGRATION_VERSION = "0009_oap_records_archive"
CREDIT_ROLES = frozenset({
    "artist", "writer", "producer", "engineer", "featured_artist", "other"
})
RECEIPT_KINDS = frozenset({"PRIVATE_HANDOFF", "INTERNAL_ARCHIVE", "RECOVERY_READBACK"})
MAX_TEXT = 240

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_records_masters (
        master_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id)
            ON DELETE CASCADE,
        track_id UUID REFERENCES oap_music_tracks(track_id) ON DELETE RESTRICT,
        evidence_receipt_id UUID REFERENCES oap_music_evidence_receipts(receipt_id)
            ON DELETE RESTRICT,
        version_label TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(owner_identity_id,release_id,track_id,version_label)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_records_master_owner_release
        ON oap_records_masters(owner_identity_id,release_id,created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_records_credits (
        credit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id)
            ON DELETE CASCADE,
        role TEXT NOT NULL CHECK (role IN
            ('artist','writer','producer','engineer','featured_artist','other')),
        display_name TEXT NOT NULL,
        evidence_receipt_id UUID REFERENCES oap_music_evidence_receipts(receipt_id)
            ON DELETE RESTRICT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_records_receipts (
        records_receipt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id)
            ON DELETE CASCADE,
        receipt_kind TEXT NOT NULL CHECK (receipt_kind IN
            ('PRIVATE_HANDOFF','INTERNAL_ARCHIVE','RECOVERY_READBACK')),
        destination TEXT NOT NULL,
        reference TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_records_receipt_owner_release
        ON oap_records_receipts(owner_identity_id,release_id,created_at DESC)""",
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
    if not cleaned or len(cleaned) > MAX_TEXT:
        raise ValueError(f"invalid_{name}")
    return cleaned


def records_contract() -> dict[str, object]:
    return {
        "organ": "OAP Records",
        "canonical_release_owner": "OAP Music",
        "capabilities": (
            "masters",
            "credits",
            "archive_receipts",
            "recovery_readback_receipts",
        ),
        "player": entertainment_catalogue.universal_player_contract(),
        "playback_enabled": False,
        "external_distribution_enabled": False,
        "rights_verified_by_records": False,
        "human_authority_final": True,
    }


def archive_gate(music_evidence_gate: object) -> dict[str, object]:
    gate = music_evidence_gate if isinstance(music_evidence_gate, Mapping) else {}
    private_ready = gate.get("private_handoff_ready") is True
    return {
        "private_archive_ready": private_ready,
        "public_archive_ready": False,
        "playback_enabled": False,
        "external_distribution_enabled": False,
        "human_authority_final": True,
    }


class RecordsStore:
    """Owner-scoped Records persistence bound to canonical Music releases."""

    def ensure_schema(self) -> None:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()

    def create_master(
        self, *, owner_identity_id: object, release_id: object, track_id: object,
        version_label: object, evidence_receipt_id: object = None,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        track = _uuid(track_id, "track_id")
        label = _text(version_label, "version_label")
        receipt = (
            _uuid(evidence_receipt_id, "evidence_receipt_id")
            if evidence_receipt_id is not None else None
        )
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_music_tracks t
                   JOIN oap_music_releases r ON r.release_id=t.release_id
                   WHERE t.track_id=%s AND r.release_id=%s
                     AND r.owner_identity_id=%s FOR UPDATE OF r""",
                (track, release, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("records_release_or_track_not_owned")
            if receipt is not None:
                evidence = connection.execute(
                    """SELECT 1 FROM oap_music_evidence_receipts
                       WHERE receipt_id=%s AND release_id=%s
                         AND owner_identity_id=%s""",
                    (receipt, release, owner),
                ).fetchone()
                if evidence is None:
                    raise PermissionError("records_evidence_not_owned")
            row = connection.execute(
                """INSERT INTO oap_records_masters(
                   owner_identity_id,release_id,track_id,evidence_receipt_id,version_label)
                   VALUES (%s,%s,%s,%s,%s)
                   RETURNING master_id""",
                (owner, release, track, receipt, label),
            ).fetchone()
            connection.commit()
        return {
            "master_id": str(row[0]),
            "release_id": release,
            "track_id": track,
            "version_label": label,
            "archived": True,
            "playback_enabled": False,
        }

    def add_credit(
        self, *, owner_identity_id: object, release_id: object, role: object,
        display_name: object, evidence_receipt_id: object = None,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        if not isinstance(role, str) or role not in CREDIT_ROLES:
            raise ValueError("invalid_credit_role")
        name = _text(display_name, "display_name")
        receipt = (
            _uuid(evidence_receipt_id, "evidence_receipt_id")
            if evidence_receipt_id is not None else None
        )
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_music_releases
                   WHERE release_id=%s AND owner_identity_id=%s FOR UPDATE""",
                (release, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("records_release_not_owned")
            if receipt is not None:
                evidence = connection.execute(
                    """SELECT 1 FROM oap_music_evidence_receipts
                       WHERE receipt_id=%s AND release_id=%s
                         AND owner_identity_id=%s""",
                    (receipt, release, owner),
                ).fetchone()
                if evidence is None:
                    raise PermissionError("records_evidence_not_owned")
            row = connection.execute(
                """INSERT INTO oap_records_credits(
                   owner_identity_id,release_id,role,display_name,evidence_receipt_id)
                   VALUES (%s,%s,%s,%s,%s)
                   RETURNING credit_id""",
                (owner, release, role, name, receipt),
            ).fetchone()
            connection.commit()
        return {
            "credit_id": str(row[0]),
            "release_id": release,
            "role": role,
            "display_name": name,
        }

    def append_receipt(
        self, *, owner_identity_id: object, release_id: object,
        receipt_kind: object, destination: object, reference: object,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        if not isinstance(receipt_kind, str) or receipt_kind not in RECEIPT_KINDS:
            raise ValueError("invalid_records_receipt_kind")
        dest = _text(destination, "destination")
        ref = _text(reference, "reference")
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_music_releases
                   WHERE release_id=%s AND owner_identity_id=%s FOR UPDATE""",
                (release, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("records_release_not_owned")
            row = connection.execute(
                """INSERT INTO oap_records_receipts(
                   owner_identity_id,release_id,receipt_kind,destination,reference)
                   VALUES (%s,%s,%s,%s,%s)
                   RETURNING records_receipt_id""",
                (owner, release, receipt_kind, dest, ref),
            ).fetchone()
            connection.commit()
        return {
            "records_receipt_id": str(row[0]),
            "release_id": release,
            "receipt_kind": receipt_kind,
            "destination": dest,
            "reference": ref,
            "proves_external_distribution": False,
        }

    def dashboard(self, *, owner_identity_id: object) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        with postgres_db.connect(readonly=True) as connection:
            masters = connection.execute(
                """SELECT master_id,release_id,track_id,version_label,evidence_receipt_id
                   FROM oap_records_masters
                   WHERE owner_identity_id=%s
                   ORDER BY created_at DESC LIMIT 200""",
                (owner,),
            ).fetchall()
            credits = connection.execute(
                """SELECT credit_id,release_id,role,display_name,evidence_receipt_id
                   FROM oap_records_credits
                   WHERE owner_identity_id=%s
                   ORDER BY created_at DESC LIMIT 500""",
                (owner,),
            ).fetchall()
            receipts = connection.execute(
                """SELECT records_receipt_id,release_id,receipt_kind,destination,reference
                   FROM oap_records_receipts
                   WHERE owner_identity_id=%s
                   ORDER BY created_at DESC LIMIT 500""",
                (owner,),
            ).fetchall()
        return {
            "organ": "OAP Records",
            "masters": [
                {
                    "master_id": str(r[0]), "release_id": str(r[1]),
                    "track_id": str(r[2]), "version_label": str(r[3]),
                    "evidence_receipt_id": str(r[4]) if r[4] else None,
                }
                for r in masters
            ],
            "credits": [
                {
                    "credit_id": str(r[0]), "release_id": str(r[1]),
                    "role": str(r[2]), "display_name": str(r[3]),
                    "evidence_receipt_id": str(r[4]) if r[4] else None,
                }
                for r in credits
            ],
            "receipts": [
                {
                    "records_receipt_id": str(r[0]), "release_id": str(r[1]),
                    "receipt_kind": str(r[2]), "destination": str(r[3]),
                    "reference": str(r[4]),
                    "proves_external_distribution": False,
                }
                for r in receipts
            ],
            "playback_enabled": False,
            "external_distribution_enabled": False,
            "player": entertainment_catalogue.universal_player_contract(),
            "human_authority_final": True,
        }
