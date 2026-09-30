"""Durable, private Awards nomination intake; no auto-migration or vote/winner path."""
from __future__ import annotations

import os
from uuid import UUID

from . import postgres_db
from .awards_eligibility import check_decade_nomination

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_award_nominations (
        nomination_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        award_program TEXT NOT NULL CHECK (award_program = 'BEST_OF_THE_DECADE'),
        first_year SMALLINT NOT NULL,
        last_year SMALLINT NOT NULL CHECK (last_year = first_year + 9),
        nominee_name TEXT NOT NULL CHECK (length(nominee_name) BETWEEN 1 AND 160),
        award_type TEXT NOT NULL CHECK (length(award_type) BETWEEN 1 AND 100),
        achievement_date DATE NOT NULL,
        evidence_reference TEXT NOT NULL CHECK (length(evidence_reference) BETWEEN 1 AND 500),
        status TEXT NOT NULL DEFAULT 'PENDING_REVIEW'
            CHECK (status = 'PENDING_REVIEW'),
        idempotency_key TEXT NOT NULL CHECK (length(idempotency_key) BETWEEN 8 AND 128),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(owner_identity_id,award_program,idempotency_key)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_oap_award_nomination_owner
       ON oap_award_nominations(owner_identity_id,created_at DESC)""",
)


def init_schema(*, assume_yes: bool = False) -> None:
    """Explicit operator-authorized schema initialization only; never on import/boot."""
    if not assume_yes:
        raise PermissionError("explicit_schema_authority_required")
    with postgres_db.connect() as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        conn.commit()


def _bounded(value: object, name: str, limit: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"invalid_{name}")
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > limit:
        raise ValueError(f"invalid_{name}")
    return cleaned


def prepare_nomination(payload: object, *, first_year: int, last_year: int) -> dict[str, object]:
    """Validate admission only; source references are unverified pending review."""
    if not isinstance(payload, dict):
        raise TypeError("json_object_required")
    nominee = _bounded(payload.get("nominee_name"), "nominee_name", 160)
    category = _bounded(payload.get("award_type"), "award_type", 100)
    reference = _bounded(payload.get("evidence_reference"), "evidence_reference", 500)
    key = _bounded(payload.get("idempotency_key"), "idempotency_key", 128)
    if len(key) < 8:
        raise ValueError("invalid_idempotency_key")
    achievement_date = payload.get("achievement_date")
    record = {
        "nominee_name": nominee,
        "award_type": category,
        "evidence_reference": reference,
        "achievement_date": achievement_date,
    }
    eligible, reason = check_decade_nomination(
        record, first_year=first_year, last_year=last_year,
    )
    if not eligible:
        raise ValueError(reason)
    return {**record, "idempotency_key": key}


def configured_decade() -> tuple[int, int]:
    """Founder must explicitly set the decade; no silent 2020s assumption."""
    raw = os.environ.get("OAP_AWARDS_DECADE_FIRST_YEAR", "")
    if not raw.isascii() or len(raw) != 4 or not raw.isdecimal():
        raise RuntimeError("awards_decade_not_approved")
    first = int(raw)
    if not 1 <= first <= 9990:
        raise RuntimeError("awards_decade_not_approved")
    return first, first + 9


def submit_nomination(payload: object, *, owner_identity_id: object) -> dict[str, object]:
    """Durable owner-scoped pending review with atomic retry deduplication."""
    owner = str(UUID(str(owner_identity_id)))
    first, last = configured_decade()
    record = prepare_nomination(payload, first_year=first, last_year=last)
    with postgres_db.connect() as conn:
        row = conn.execute(
            """INSERT INTO oap_award_nominations
                (owner_identity_id,award_program,first_year,last_year,nominee_name,
                 award_type,achievement_date,evidence_reference,idempotency_key)
               VALUES (%s,'BEST_OF_THE_DECADE',%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (owner_identity_id,award_program,idempotency_key)
               DO NOTHING RETURNING nomination_id""",
            (owner, first, last, record["nominee_name"], record["award_type"],
             record["achievement_date"], record["evidence_reference"],
             record["idempotency_key"]),
        ).fetchone()
        if row is None:
            existing = conn.execute(
                """SELECT nomination_id,first_year,last_year,nominee_name,award_type,
                          achievement_date,evidence_reference FROM oap_award_nominations
                   WHERE owner_identity_id=%s AND award_program='BEST_OF_THE_DECADE'
                         AND idempotency_key=%s""",
                (owner, record["idempotency_key"]),
            ).fetchone()
            if existing is None or (
                int(existing[1]) != first or int(existing[2]) != last
                or existing[3] != record["nominee_name"]
                or existing[4] != record["award_type"]
                or str(existing[5]) != record["achievement_date"]
                or existing[6] != record["evidence_reference"]
            ):
                raise ValueError("idempotency_conflict")
            nomination_id = existing[0]
        else:
            nomination_id = row[0]
        conn.commit()
    return {
        "nomination_id": str(nomination_id),
        "award_program": "BEST_OF_THE_DECADE",
        "status": "PENDING_REVIEW",
        "evidence_verified": False,
        "voting_enabled": False,
        "winner_declared": False,
        "human_authority_final": True,
    }
