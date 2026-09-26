"""Durable, owner-scoped evidence and civilization intelligence for OAP Music.

This module does not verify copyright, provenance, licences, territories or
distribution authority by itself. It stores independently obtained evidence,
binds it to an existing OAP Music release, maintains an append-only hash chain,
and computes a fail-closed private distribution gate.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any
from uuid import UUID, uuid4

from . import postgres_db

MUSIC_EVIDENCE_MIGRATION_VERSION = "0007_oap_music_evidence_chain"

EVIDENCE_KINDS = frozenset({
    "source_page",
    "recording_rights",
    "composition_rights",
    "asset_provenance",
    "territory_permission",
    "attribution",
    "human_approval",
    "recovery_readback",
})
CIVILIZATION_LEVELS = (
    "postcode", "area", "borough_region", "country", "language",
    "culture", "genre", "movement", "era", "civilization",
)
MAX_TEXT = 240
GENESIS_HASH = "0" * 64

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_evidence_receipts (
        receipt_id UUID PRIMARY KEY,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id) ON DELETE CASCADE,
        evidence_kind TEXT NOT NULL CHECK (evidence_kind IN
          ('source_page','recording_rights','composition_rights','asset_provenance',
           'territory_permission','attribution','human_approval','recovery_readback')),
        evidence_sha256 TEXT NOT NULL CHECK (length(evidence_sha256)=64),
        source_reference TEXT,
        authority_reference TEXT,
        territory TEXT,
        previous_receipt_hash TEXT NOT NULL CHECK (length(previous_receipt_hash)=64),
        receipt_hash TEXT NOT NULL UNIQUE CHECK (length(receipt_hash)=64),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_evidence_owner_release_created
       ON oap_music_evidence_receipts(owner_identity_id,release_id,created_at,receipt_id)""",
    """CREATE TABLE IF NOT EXISTS oap_music_civilization_links (
        link_id UUID PRIMARY KEY,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id) ON DELETE CASCADE,
        level TEXT NOT NULL CHECK (level IN
          ('postcode','area','borough_region','country','language','culture',
           'genre','movement','era','civilization')),
        value TEXT NOT NULL,
        evidence_receipt_id UUID NOT NULL REFERENCES oap_music_evidence_receipts(receipt_id)
            ON DELETE RESTRICT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(release_id,level,value,evidence_receipt_id)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_civilization_release_level
       ON oap_music_civilization_links(release_id,level,created_at)""",
)

SCHEMA_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _text(value: object, name: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise ValueError(f"invalid_{name}")
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > MAX_TEXT:
        raise ValueError(f"invalid_{name}")
    return cleaned


def _sha256(value: object, name: str) -> str:
    if (
        not isinstance(value, str) or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise ValueError(f"invalid_{name}")
    return value


def canonical_receipt_payload(
    *,
    receipt_id: str,
    owner_identity_id: str,
    release_id: str,
    evidence_kind: str,
    evidence_sha256: str,
    source_reference: str | None,
    authority_reference: str | None,
    territory: str | None,
    previous_receipt_hash: str,
) -> bytes:
    payload = {
        "authority_reference": authority_reference,
        "evidence_kind": evidence_kind,
        "evidence_sha256": evidence_sha256,
        "owner_identity_id": owner_identity_id,
        "previous_receipt_hash": previous_receipt_hash,
        "receipt_id": receipt_id,
        "release_id": release_id,
        "source_reference": source_reference,
        "territory": territory,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def build_receipt(
    *,
    owner_identity_id: object,
    release_id: object,
    evidence_kind: object,
    evidence_bytes: object,
    source_reference: object = None,
    authority_reference: object = None,
    territory: object = None,
    previous_receipt_hash: object = GENESIS_HASH,
    receipt_id: object = None,
) -> dict[str, str | None]:
    """Build one immutable receipt from actual bytes; never infer rights."""
    owner = _uuid(owner_identity_id, "owner_identity_id")
    release = _uuid(release_id, "release_id")
    rid = _uuid(receipt_id or str(uuid4()), "receipt_id")
    if not isinstance(evidence_kind, str) or evidence_kind not in EVIDENCE_KINDS:
        raise ValueError("invalid_evidence_kind")
    if not isinstance(evidence_bytes, bytes) or not evidence_bytes or len(evidence_bytes) > 8_388_608:
        raise ValueError("invalid_evidence_bytes")
    source = _text(source_reference, "source_reference", optional=True)
    authority = _text(authority_reference, "authority_reference", optional=True)
    territory_value = _text(territory, "territory", optional=True)
    previous = _sha256(previous_receipt_hash, "previous_receipt_hash")
    evidence_sha = hashlib.sha256(evidence_bytes).hexdigest()
    body = canonical_receipt_payload(
        receipt_id=rid,
        owner_identity_id=owner,
        release_id=release,
        evidence_kind=evidence_kind,
        evidence_sha256=evidence_sha,
        source_reference=source,
        authority_reference=authority,
        territory=territory_value,
        previous_receipt_hash=previous,
    )
    return {
        "receipt_id": rid,
        "owner_identity_id": owner,
        "release_id": release,
        "evidence_kind": evidence_kind,
        "evidence_sha256": evidence_sha,
        "source_reference": source,
        "authority_reference": authority,
        "territory": territory_value,
        "previous_receipt_hash": previous,
        "receipt_hash": hashlib.sha256(body).hexdigest(),
    }


def verify_receipt_chain(receipts: object) -> dict[str, object]:
    rows = receipts if isinstance(receipts, list) else []
    previous = GENESIS_HASH
    verified = True
    checked = 0
    for row in rows:
        if not isinstance(row, Mapping):
            verified = False
            break
        try:
            rid = _uuid(row.get("receipt_id"), "receipt_id")
            owner = _uuid(row.get("owner_identity_id"), "owner_identity_id")
            release = _uuid(row.get("release_id"), "release_id")
            kind = row.get("evidence_kind")
            if not isinstance(kind, str) or kind not in EVIDENCE_KINDS:
                raise ValueError("invalid_evidence_kind")
            evidence_sha = _sha256(row.get("evidence_sha256"), "evidence_sha256")
            prev = _sha256(row.get("previous_receipt_hash"), "previous_receipt_hash")
            claimed = _sha256(row.get("receipt_hash"), "receipt_hash")
            source = _text(row.get("source_reference"), "source_reference", optional=True)
            authority = _text(row.get("authority_reference"), "authority_reference", optional=True)
            territory = _text(row.get("territory"), "territory", optional=True)
        except ValueError:
            verified = False
            break
        if prev != previous:
            verified = False
            break
        actual = hashlib.sha256(canonical_receipt_payload(
            receipt_id=rid, owner_identity_id=owner, release_id=release,
            evidence_kind=kind, evidence_sha256=evidence_sha,
            source_reference=source, authority_reference=authority,
            territory=territory, previous_receipt_hash=prev,
        )).hexdigest()
        if actual != claimed:
            verified = False
            break
        previous = claimed
        checked += 1
    return {
        "chain_verified": verified and checked == len(rows),
        "receipt_count": checked,
        "head_hash": previous if checked else GENESIS_HASH,
        "rights_verified": False,
        "playback_authorised": False,
        "public_catalogue_enabled": False,
    }


def civilization_projection(links: object) -> dict[str, object]:
    """Evidence-backed cultural graph projection; never infer missing heritage."""
    rows = links if isinstance(links, list) else []
    graph: dict[str, list[dict[str, str]]] = {level: [] for level in CIVILIZATION_LEVELS}
    seen: set[tuple[str, str, str]] = set()
    for row in rows[:500]:
        if not isinstance(row, Mapping):
            continue
        level = row.get("level")
        if level not in CIVILIZATION_LEVELS:
            continue
        try:
            value = _text(row.get("value"), "value")
            receipt = _uuid(row.get("evidence_receipt_id"), "evidence_receipt_id")
        except ValueError:
            continue
        key = (level, value.casefold(), receipt)
        if key in seen:
            continue
        seen.add(key)
        graph[level].append({"value": value, "evidence_receipt_id": receipt})
    return {
        "organ": "OAP Music",
        "graph": graph,
        "evidence_backed_only": True,
        "inference_performed": False,
        "public_claims_enabled": False,
    }


def private_distribution_gate(receipts: object, *, recovery_readback_proven: bool = False) -> dict[str, object]:
    """Require the complete evidence set; remain private and fail closed."""
    rows = receipts if isinstance(receipts, list) else []
    chain = verify_receipt_chain(rows)
    kinds = {
        row.get("evidence_kind") for row in rows
        if isinstance(row, Mapping) and row.get("evidence_kind") in EVIDENCE_KINDS
    }
    required = {
        "source_page", "recording_rights", "composition_rights",
        "asset_provenance", "territory_permission", "attribution", "human_approval",
    }
    missing = sorted(required - kinds)
    ready = bool(chain["chain_verified"] and not missing and recovery_readback_proven is True)
    return {
        "private_handoff_ready": ready,
        "chain_verified": chain["chain_verified"],
        "missing_evidence_kinds": missing,
        "recovery_readback_proven": recovery_readback_proven is True,
        "recording_rights_evidence_present": "recording_rights" in kinds,
        "composition_rights_evidence_present": "composition_rights" in kinds,
        "asset_provenance_evidence_present": "asset_provenance" in kinds,
        "territory_permission_evidence_present": "territory_permission" in kinds,
        "human_approval_evidence_present": "human_approval" in kinds,
        "external_distribution_enabled": False,
        "playback_enabled": False,
        "public_catalogue_enabled": False,
        "rights_verified_by_software": False,
        "human_authority_final": True,
    }


class MusicEvidenceStore:
    """Postgres persistence bound to canonical owner-scoped OAP Music releases."""

    def ensure_schema(self) -> None:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.commit()

    def append_receipt(
        self, *, owner_identity_id: object, release_id: object,
        evidence_kind: object, evidence_bytes: object,
        source_reference: object = None, authority_reference: object = None,
        territory: object = None,
    ) -> dict[str, str | None]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_music_releases
                   WHERE release_id=%s AND owner_identity_id=%s FOR UPDATE""",
                (release, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("music_release_not_owned")
            previous_row = connection.execute(
                """SELECT receipt_hash FROM oap_music_evidence_receipts
                   WHERE owner_identity_id=%s AND release_id=%s
                   ORDER BY created_at DESC,receipt_id DESC LIMIT 1 FOR UPDATE""",
                (owner, release),
            ).fetchone()
            previous = str(previous_row[0]) if previous_row else GENESIS_HASH
            receipt = build_receipt(
                owner_identity_id=owner, release_id=release,
                evidence_kind=evidence_kind, evidence_bytes=evidence_bytes,
                source_reference=source_reference,
                authority_reference=authority_reference, territory=territory,
                previous_receipt_hash=previous,
            )
            connection.execute(
                """INSERT INTO oap_music_evidence_receipts(
                   receipt_id,owner_identity_id,release_id,evidence_kind,evidence_sha256,
                   source_reference,authority_reference,territory,previous_receipt_hash,receipt_hash)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    receipt["receipt_id"], owner, release, receipt["evidence_kind"],
                    receipt["evidence_sha256"], receipt["source_reference"],
                    receipt["authority_reference"], receipt["territory"],
                    receipt["previous_receipt_hash"], receipt["receipt_hash"],
                ),
            )
            connection.commit()
        return receipt

    def read_receipts(self, *, owner_identity_id: object, release_id: object) -> list[dict[str, Any]]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        with postgres_db.connect(readonly=True) as connection:
            owned = connection.execute(
                """SELECT 1 FROM oap_music_releases
                   WHERE release_id=%s AND owner_identity_id=%s""",
                (release, owner),
            ).fetchone()
            if owned is None:
                raise PermissionError("music_release_not_owned")
            rows = connection.execute(
                """SELECT receipt_id,owner_identity_id,release_id,evidence_kind,
                          evidence_sha256,source_reference,authority_reference,territory,
                          previous_receipt_hash,receipt_hash
                   FROM oap_music_evidence_receipts
                   WHERE owner_identity_id=%s AND release_id=%s
                   ORDER BY created_at,receipt_id""",
                (owner, release),
            ).fetchall()
        return [
            {
                "receipt_id": str(r[0]), "owner_identity_id": str(r[1]),
                "release_id": str(r[2]), "evidence_kind": str(r[3]),
                "evidence_sha256": str(r[4]), "source_reference": r[5],
                "authority_reference": r[6], "territory": r[7],
                "previous_receipt_hash": str(r[8]), "receipt_hash": str(r[9]),
            }
            for r in rows
        ]

    def add_civilization_link(
        self, *, owner_identity_id: object, release_id: object, level: object,
        value: object, evidence_receipt_id: object,
    ) -> dict[str, str]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        receipt = _uuid(evidence_receipt_id, "evidence_receipt_id")
        if not isinstance(level, str) or level not in CIVILIZATION_LEVELS:
            raise ValueError("invalid_civilization_level")
        text_value = _text(value, "value")
        link_id = str(uuid4())
        with postgres_db.connect() as connection:
            evidence = connection.execute(
                """SELECT 1 FROM oap_music_evidence_receipts
                   WHERE receipt_id=%s AND owner_identity_id=%s AND release_id=%s""",
                (receipt, owner, release),
            ).fetchone()
            if evidence is None:
                raise PermissionError("evidence_receipt_not_owned")
            connection.execute(
                """INSERT INTO oap_music_civilization_links(
                   link_id,owner_identity_id,release_id,level,value,evidence_receipt_id)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (release_id,level,value,evidence_receipt_id) DO NOTHING""",
                (link_id, owner, release, level, text_value, receipt),
            )
            connection.commit()
        return {
            "link_id": link_id, "release_id": release, "level": level,
            "value": text_value, "evidence_receipt_id": receipt,
        }
