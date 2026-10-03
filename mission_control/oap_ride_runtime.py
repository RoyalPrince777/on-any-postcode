"""Durable OAP Ride journey lifecycle on top of OAP Movement.

Owns Journey Code, start/completion receipts and feedback without altering the
existing Movement migration. No vehicle control, dispatch or payment capture.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from . import postgres_db, oap_ride_payment_bridge

RIDE_RUNTIME_MIGRATION = "0001_oap_ride_runtime"
TABLES = frozenset({
    "oap_ride_journey_codes",
    "oap_ride_receipts",
    "oap_ride_feedback",
})
STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_ride_journey_codes (
        booking_id UUID PRIMARY KEY REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        code_hash TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('ISSUED','VERIFIED','EXPIRED','LOCKED')),
        attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0 AND attempts <= 5),
        expires_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_ride_receipts (
        booking_id UUID PRIMARY KEY REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        rider_identity_id UUID NOT NULL,
        driver_identity_id UUID NOT NULL,
        completed_at TIMESTAMPTZ NOT NULL,
        payment_state TEXT NOT NULL,
        amount_minor BIGINT,
        currency TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_ride_feedback (
        feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id UUID NOT NULL REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        author_identity_id UUID NOT NULL,
        rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
        note TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(booking_id, author_identity_id))""",
)
CHECKSUM = hashlib.sha256("\n".join(STATEMENTS).encode()).hexdigest()


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def schema_status() -> dict[str, Any]:
    result = {"migration": RIDE_RUNTIME_MIGRATION, "schema_ready": False, "tables": 0, "error": None}
    try:
        with postgres_db.connect(readonly=True) as connection:
            tables = {str(row[0]) for row in connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            ).fetchall()}
            result["tables"] = len(TABLES & tables)
            if not TABLES <= tables:
                result["error"] = "ride_runtime_schema_pending"
                return result
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (RIDE_RUNTIME_MIGRATION,),
            ).fetchone()
            if row is None or str(row[0]) != CHECKSUM:
                result["error"] = "ride_runtime_migration_not_verified"
                return result
            result["schema_ready"] = True
            return result
    except Exception:
        result["error"] = "ride_runtime_store_unavailable"
        return result


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes:
        raise RuntimeError("explicit_human_approval_required")
    if dry_run:
        return {"dry_run": True, "migration": RIDE_RUNTIME_MIGRATION, "checksum": CHECKSUM, "tables": len(TABLES)}
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800021,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (RIDE_RUNTIME_MIGRATION,),
        ).fetchone()
        if row is not None and str(row[0]) != CHECKSUM:
            raise RuntimeError("ride_runtime_migration_checksum_mismatch")
        if row is None:
            for statement in STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (RIDE_RUNTIME_MIGRATION, CHECKSUM),
            )
        connection.commit()
    return schema_status()


def _participants(connection, booking: str) -> tuple[str, str, str]:
    row = connection.execute(
        """SELECT b.member_identity_id,b.state,p.worker_identity_id
           FROM oap_movement_bookings b
           JOIN oap_movement_match_proposals p ON p.booking_id=b.booking_id AND p.state='ACCEPTED'
           WHERE b.booking_id=%s AND b.service_type='ride'""",
        (booking,),
    ).fetchone()
    if row is None:
        raise PermissionError("accepted_ride_required")
    return str(row[0]), str(row[2]), str(row[1])


def issue_journey_code(*, booking_id: object, rider_identity_id: object) -> dict[str, Any]:
    booking = _uuid(booking_id, "booking_id")
    rider = _uuid(rider_identity_id, "rider_identity_id")
    code = f"{secrets.randbelow(1_000_000):06d}"
    digest = hashlib.sha256(f"{booking}:{code}".encode()).hexdigest()
    expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
    with postgres_db.connect() as connection:
        owner, _, state = _participants(connection, booking)
        if owner != rider:
            raise PermissionError("ride_owner_required")
        if state != "ACCEPTED":
            raise ValueError("ride_not_ready_for_pickup")
        connection.execute(
            """INSERT INTO oap_ride_journey_codes
               (booking_id,code_hash,state,attempts,expires_at)
               VALUES (%s,%s,'ISSUED',0,%s)
               ON CONFLICT (booking_id) DO UPDATE SET
                 code_hash=EXCLUDED.code_hash,state='ISSUED',attempts=0,
                 expires_at=EXCLUDED.expires_at,updated_at=CURRENT_TIMESTAMP""",
            (booking, digest, expiry),
        )
        connection.commit()
    return {"booking_id": booking, "journey_code": code, "expires_at": expiry.isoformat(), "stored_plaintext": False}


def verify_and_start(*, booking_id: object, driver_identity_id: object, journey_code: object) -> dict[str, Any]:
    booking = _uuid(booking_id, "booking_id")
    driver = _uuid(driver_identity_id, "driver_identity_id")
    code = str(journey_code or "").strip()
    if len(code) != 6 or not code.isdigit():
        raise ValueError("invalid_journey_code")
    digest = hashlib.sha256(f"{booking}:{code}".encode()).hexdigest()
    with postgres_db.connect() as connection:
        _, accepted_driver, state = _participants(connection, booking)
        if accepted_driver != driver:
            raise PermissionError("accepted_driver_required")
        if state != "ACCEPTED":
            raise ValueError("ride_not_ready_for_start")
        row = connection.execute(
            """SELECT code_hash,state,attempts,expires_at FROM oap_ride_journey_codes
               WHERE booking_id=%s FOR UPDATE""",
            (booking,),
        ).fetchone()
        if row is None or str(row[1]) != "ISSUED":
            raise PermissionError("active_journey_code_required")
        if row[3] <= datetime.now(timezone.utc):
            connection.execute("UPDATE oap_ride_journey_codes SET state='EXPIRED' WHERE booking_id=%s", (booking,))
            connection.commit()
            raise PermissionError("journey_code_expired")
        if not secrets.compare_digest(str(row[0]), digest):
            attempts = int(row[2]) + 1
            state_value = "LOCKED" if attempts >= 5 else "ISSUED"
            connection.execute(
                "UPDATE oap_ride_journey_codes SET attempts=%s,state=%s,updated_at=CURRENT_TIMESTAMP WHERE booking_id=%s",
                (attempts, state_value, booking),
            )
            connection.commit()
            raise PermissionError("journey_code_mismatch")
        connection.execute(
            "UPDATE oap_ride_journey_codes SET state='VERIFIED',updated_at=CURRENT_TIMESTAMP WHERE booking_id=%s",
            (booking,),
        )
        updated = connection.execute(
            """UPDATE oap_movement_bookings SET state='IN_PROGRESS',updated_at=CURRENT_TIMESTAMP
               WHERE booking_id=%s AND state='ACCEPTED' RETURNING updated_at""",
            (booking,),
        ).fetchone()
        if updated is None:
            raise ValueError("ride_start_transition_failed")
        connection.commit()
    return {"booking_id": booking, "state": "IN_PROGRESS", "journey_code_verified": True, "physical_dispatch_performed": False}


def complete(*, booking_id: object, driver_identity_id: object) -> dict[str, Any]:
    booking = _uuid(booking_id, "booking_id")
    driver = _uuid(driver_identity_id, "driver_identity_id")
    with postgres_db.connect() as connection:
        rider, accepted_driver, state = _participants(connection, booking)
        if accepted_driver != driver:
            raise PermissionError("accepted_driver_required")
        if state != "IN_PROGRESS":
            raise ValueError("ride_not_in_progress")
        try:
            payment_projection = oap_ride_payment_bridge.projection(booking_id=booking)
        except Exception:
            payment_projection = {
                "bound": False,
                "payment_status": "BRIDGE_UNAVAILABLE",
                "amount_minor": None,
                "currency": None,
                "submission_evidence": None,
                "settlement_proven": False,
            }
        if payment_projection.get("bound"):
            payment_state = str(payment_projection.get("payment_status") or "UNKNOWN")
            amount = payment_projection.get("amount_minor")
            currency = payment_projection.get("currency")
        else:
            payment = connection.execute(
                """SELECT state,amount_minor,currency FROM oap_movement_payment_intents
                   WHERE booking_id=%s ORDER BY created_at DESC LIMIT 1""",
                (booking,),
            ).fetchone()
            payment_state = str(payment[0]) if payment else str(payment_projection.get("payment_status") or "NOT_CREATED")
            amount = int(payment[1]) if payment else None
            currency = str(payment[2]) if payment else None
        completed = connection.execute(
            """UPDATE oap_movement_bookings SET state='COMPLETED',updated_at=CURRENT_TIMESTAMP
               WHERE booking_id=%s AND state='IN_PROGRESS' RETURNING updated_at""",
            (booking,),
        ).fetchone()
        if completed is None:
            raise ValueError("ride_complete_transition_failed")
        connection.execute(
            """INSERT INTO oap_ride_receipts
               (booking_id,rider_identity_id,driver_identity_id,completed_at,payment_state,amount_minor,currency)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (booking_id) DO NOTHING""",
            (booking, rider, driver, completed[0], payment_state, amount, currency),
        )
        connection.execute(
            """UPDATE oap_movement_availability SET availability_state='ONLINE',updated_at=CURRENT_TIMESTAMP
               WHERE identity_id=%s AND role_type='driver' AND availability_state='BUSY'""",
            (driver,),
        )
        connection.commit()
    return {
        "booking_id": booking,
        "state": "COMPLETED",
        "payment_state": payment_state,
        "amount_minor": amount,
        "currency": currency,
        "receipt_recorded": True,
        "canonical_sika_payment_bound": bool(payment_projection.get("bound")),
        "submission_evidence": payment_projection.get("submission_evidence"),
        "settlement_proven": bool(payment_projection.get("settlement_proven")),
        "payment_captured_by_ride_runtime": False,
        "physical_operation_performed": False,
    }


def receipt(*, booking_id: object, identity_id: object) -> dict[str, Any]:
    booking = _uuid(booking_id, "booking_id")
    identity = _uuid(identity_id, "identity_id")
    with postgres_db.connect(readonly=True) as connection:
        rider, driver, _ = _participants(connection, booking)
        if identity not in {rider, driver}:
            raise PermissionError("booking_participant_required")
        row = connection.execute(
            """SELECT completed_at,payment_state,amount_minor,currency
               FROM oap_ride_receipts WHERE booking_id=%s""",
            (booking,),
        ).fetchone()
    if row is None:
        raise PermissionError("ride_receipt_not_available")
    try:
        payment_projection = oap_ride_payment_bridge.projection(booking_id=booking)
    except Exception:
        payment_projection = {"bound": False, "submission_evidence": None, "settlement_proven": False}
    return {
        "booking_id": booking,
        "completed_at": row[0].isoformat(),
        "payment_state": str(row[1]),
        "amount_minor": int(row[2]) if row[2] is not None else None,
        "currency": str(row[3]) if row[3] else None,
        "canonical_sika_payment_bound": bool(payment_projection.get("bound")),
        "submission_evidence": payment_projection.get("submission_evidence"),
        "settlement_proven": bool(payment_projection.get("settlement_proven")),
    }


def leave_feedback(*, booking_id: object, author_identity_id: object, rating: object, note: object = "") -> dict[str, Any]:
    booking = _uuid(booking_id, "booking_id")
    author = _uuid(author_identity_id, "author_identity_id")
    try:
        stars = int(rating)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_rating") from exc
    if not 1 <= stars <= 5:
        raise ValueError("invalid_rating")
    text = " ".join(str(note or "").strip().split())[:500]
    with postgres_db.connect() as connection:
        rider, driver, state = _participants(connection, booking)
        if author not in {rider, driver}:
            raise PermissionError("booking_participant_required")
        if state != "COMPLETED":
            raise ValueError("completed_ride_required")
        row = connection.execute(
            """INSERT INTO oap_ride_feedback(booking_id,author_identity_id,rating,note)
               VALUES (%s,%s,%s,%s)
               ON CONFLICT (booking_id,author_identity_id) DO UPDATE SET
                 rating=EXCLUDED.rating,note=EXCLUDED.note
               RETURNING feedback_id,created_at""",
            (booking, author, stars, text),
        ).fetchone()
        connection.commit()
    return {"feedback_id": str(row[0]), "booking_id": booking, "rating": stars, "created_at": row[1].isoformat()}
