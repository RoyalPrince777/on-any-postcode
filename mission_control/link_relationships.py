"""Protected OAP Link relationships and Purpose Links.

Schema changes remain explicit. Importing this module never mutates production.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from . import linkup_safety, postgres_db

SCHEMA_VERSION = "link_relationships_v1"
SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS link_relationships (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        requester_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending','accepted','declined','revoked','expired')),
        link_kind TEXT NOT NULL DEFAULT 'permanent'
            CHECK (link_kind IN ('permanent','purpose')),
        purpose_text TEXT,
        expires_at TIMESTAMPTZ,
        accepted_at TIMESTAMPTZ,
        resolved_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (requester_id <> recipient_id),
        CHECK (link_kind <> 'purpose' OR (purpose_text IS NOT NULL AND btrim(purpose_text) <> '')),
        CHECK (link_kind <> 'permanent' OR expires_at IS NULL))""",
    """CREATE UNIQUE INDEX IF NOT EXISTS uq_link_relationships_active_pair
        ON link_relationships (LEAST(requester_id, recipient_id), GREATEST(requester_id, recipient_id))
        WHERE status IN ('pending','accepted')""",
    "CREATE INDEX IF NOT EXISTS idx_link_relationships_recipient_status ON link_relationships(recipient_id,status,created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_link_relationships_requester_status ON link_relationships(requester_id,status,created_at DESC)",
    """CREATE INDEX IF NOT EXISTS idx_link_relationships_expiry
        ON link_relationships(expires_at)
        WHERE status='accepted' AND link_kind='purpose'""",
)


class LinkRelationshipsUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _kind(value: object) -> str:
    kind = str(value or "permanent").strip().casefold()
    if kind not in {"permanent", "purpose"}:
        raise ValueError("invalid_link_kind")
    return kind


def _expiry(value: object, kind: str) -> datetime | None:
    if kind == "permanent":
        return None
    if not value:
        raise ValueError("purpose_expiry_required")
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_purpose_expiry") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    if parsed <= datetime.now(timezone.utc):
        raise ValueError("purpose_expiry_must_be_future")
    return parsed


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes and not dry_run:
        raise PermissionError("explicit_confirmation_required")
    if dry_run:
        return {"version": SCHEMA_VERSION, "statements": list(SCHEMA_SQL), "applied": False}
    try:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_SQL:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise LinkRelationshipsUnavailable("link_relationships_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def status() -> dict[str, Any]:
    result = {"configured": postgres_db.configured(), "ready": False}
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='link_relationships'"
            ).fetchone()
        result["ready"] = row is not None
    except Exception:  # noqa: BLE001
        return result
    return result


def accepted_between(first_id: object, second_id: object) -> bool:
    """Return whether two identities currently share an accepted Link."""
    first = _uuid(first_id, "invalid_identity")
    second = _uuid(second_id, "invalid_identity")
    if first == second:
        return False
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM link_relationships
                   WHERE LEAST(requester_id,recipient_id)=LEAST(%s::uuid,%s::uuid)
                     AND GREATEST(requester_id,recipient_id)=GREATEST(%s::uuid,%s::uuid)
                     AND status='accepted'
                     AND (link_kind='permanent' OR expires_at>CURRENT_TIMESTAMP)
                   LIMIT 1""",
                (first, second, first, second),
            ).fetchone()
    except Exception as exc:
        raise LinkRelationshipsUnavailable("link_relationship_check_failed") from exc
    return row is not None


def request_link(requester_id: object, recipient_id: object, *, link_kind: object = "permanent", purpose_text: object = "", expires_at: object = None) -> str:
    requester = _uuid(requester_id, "invalid_requester")
    recipient = _uuid(recipient_id, "invalid_recipient")
    if requester == recipient:
        raise ValueError("cannot_link_self")
    if linkup_safety.blocked_between(requester, recipient):
        raise ValueError("link_blocked")
    kind = _kind(link_kind)
    purpose = " ".join(str(purpose_text or "").split())[:240]
    if kind == "purpose" and not purpose:
        raise ValueError("purpose_required")
    expiry = _expiry(expires_at, kind)
    try:
        with postgres_db.connect() as connection:
            member = connection.execute(
                "SELECT 1 FROM users WHERE id=%s AND status='active'", (recipient,)
            ).fetchone()
            if member is None:
                raise ValueError("member_unavailable")
            existing = connection.execute(
                """SELECT 1 FROM link_relationships
                   WHERE LEAST(requester_id,recipient_id)=LEAST(%s::uuid,%s::uuid)
                     AND GREATEST(requester_id,recipient_id)=GREATEST(%s::uuid,%s::uuid)
                     AND status IN ('pending','accepted') LIMIT 1""",
                (requester, recipient, requester, recipient),
            ).fetchone()
            if existing:
                raise ValueError("active_link_exists")
            row = connection.execute(
                """INSERT INTO link_relationships(requester_id,recipient_id,link_kind,purpose_text,expires_at)
                   VALUES (%s,%s,%s,%s,%s) RETURNING id""",
                (requester, recipient, kind, purpose or None, expiry),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkRelationshipsUnavailable("link_request_failed") from exc
    return str(row[0])


def respond(recipient_id: object, relationship_id: object, decision: object) -> bool:
    recipient = _uuid(recipient_id, "invalid_recipient")
    relationship = _uuid(relationship_id, "invalid_relationship")
    choice = str(decision or "").strip().casefold()
    if choice not in {"accepted", "declined"}:
        raise ValueError("invalid_link_decision")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE link_relationships
                   SET status=%s,
                       accepted_at=CASE WHEN %s='accepted' THEN CURRENT_TIMESTAMP ELSE accepted_at END,
                       resolved_at=CURRENT_TIMESTAMP,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE id=%s AND recipient_id=%s AND status='pending'
                   RETURNING id""",
                (choice, choice, relationship, recipient),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise LinkRelationshipsUnavailable("link_response_failed") from exc
    return row is not None


def revoke(identity_id: object, relationship_id: object) -> bool:
    identity = _uuid(identity_id, "invalid_identity")
    relationship = _uuid(relationship_id, "invalid_relationship")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE link_relationships
                   SET status='revoked',resolved_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP
                   WHERE id=%s AND status='accepted' AND (requester_id=%s OR recipient_id=%s)
                   RETURNING id""",
                (relationship, identity, identity),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise LinkRelationshipsUnavailable("link_revoke_failed") from exc
    return row is not None


def list_for_identity(identity_id: object) -> list[dict[str, Any]]:
    identity = _uuid(identity_id, "invalid_identity")
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT id,requester_id,recipient_id,status,link_kind,purpose_text,expires_at,created_at,
                          CASE WHEN status='accepted' AND link_kind='purpose' AND expires_at<=CURRENT_TIMESTAMP
                               THEN 'expired' ELSE status END AS effective_status
                   FROM link_relationships
                   WHERE requester_id=%s OR recipient_id=%s
                   ORDER BY created_at DESC LIMIT 100""",
                (identity, identity),
            ).fetchall()
    except Exception as exc:
        raise LinkRelationshipsUnavailable("link_list_failed") from exc
    return [
        {
            "relationship_id": str(row[0]),
            "requester_id": str(row[1]),
            "recipient_id": str(row[2]),
            "status": str(row[8]),
            "link_kind": str(row[4]),
            "purpose_text": row[5],
            "expires_at": row[6].isoformat() if row[6] else None,
            "created_at": row[7].isoformat(),
        }
        for row in rows
    ]
