"""Durable, fail-closed OAP Movement operations.

This module owns the persistence boundary for booking drafts/requests, certified
worker availability, match proposals, tracking consent, eSIM connectivity
requests, payment intents and trip-to-Link-Up bindings. It does not activate a
carrier profile, capture money, dispatch a person or publish precise location.

Every schema mutation requires explicit Human Authority invocation. Normal
status reads are read-only and never create tables.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from . import postgres_db

MOVEMENT_MIGRATION_VERSION = "0005_movement_operations"
MOVEMENT_TABLES = frozenset(
    {
        "oap_movement_bookings",
        "oap_movement_availability",
        "oap_movement_match_proposals",
        "oap_movement_tracking_consents",
        "oap_movement_tracking_points",
        "oap_movement_esim_requests",
        "oap_movement_payment_intents",
        "oap_movement_trip_channels",
    }
)
MOVEMENT_ROLE_IDS = {
    "driver": "MOVEMENT_DRIVER",
    "rider": "MOVEMENT_RIDER",
    "courier": "MOVEMENT_COURIER",
    "merchant": "MOVEMENT_MERCHANT",
}
SERVICE_TYPES = frozenset({"ride", "ebike", "delivery"})
WORKER_ROLES = frozenset({"driver", "rider", "courier"})
AVAILABILITY_STATES = frozenset({"ONLINE", "BUSY", "OFFLINE"})
_IDEMPOTENCY = re.compile(r"^[A-Za-z0-9._:-]{8,160}$")

MOVEMENT_SCHEMA_STATEMENTS = (
    """INSERT INTO oap_roles(role_id,name,authority_level) VALUES
        ('MOVEMENT_DRIVER','Certified Movement Driver',5),
        ('MOVEMENT_RIDER','Certified Movement Rider',5),
        ('MOVEMENT_COURIER','Certified Movement Courier',5),
        ('MOVEMENT_MERCHANT','Certified Movement Merchant',5)
        ON CONFLICT (role_id) DO NOTHING""",
    """CREATE TABLE IF NOT EXISTS oap_movement_bookings (
        booking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        member_identity_id UUID NOT NULL,
        service_type TEXT NOT NULL
            CHECK (service_type IN ('ride','ebike','delivery')),
        pickup JSONB NOT NULL,
        destination JSONB,
        scheduled_for TIMESTAMPTZ,
        state TEXT NOT NULL DEFAULT 'REQUESTED'
            CHECK (state IN ('DRAFT','REQUESTED','MATCH_PROPOSED','ACCEPTED',
                             'IN_PROGRESS','COMPLETED','CANCELLED')),
        route_snapshot JSONB,
        idempotency_key TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_movement_booking_member_created
        ON oap_movement_bookings(member_identity_id, created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_movement_booking_state_scheduled
        ON oap_movement_bookings(state, scheduled_for)""",
    """CREATE TABLE IF NOT EXISTS oap_movement_availability (
        identity_id UUID NOT NULL,
        role_type TEXT NOT NULL
            CHECK (role_type IN ('driver','rider','courier')),
        availability_state TEXT NOT NULL
            CHECK (availability_state IN ('ONLINE','BUSY','OFFLINE')),
        zone TEXT NOT NULL DEFAULT '',
        available_until TIMESTAMPTZ,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (identity_id, role_type))""",
    """CREATE INDEX IF NOT EXISTS ix_movement_availability_match
        ON oap_movement_availability(
            role_type, availability_state, zone, updated_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_movement_match_proposals (
        proposal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id UUID NOT NULL
            REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        worker_identity_id UUID NOT NULL,
        worker_role TEXT NOT NULL
            CHECK (worker_role IN ('driver','rider','courier')),
        state TEXT NOT NULL DEFAULT 'PROPOSED'
            CHECK (state IN ('PROPOSED','ACCEPTED','DECLINED','EXPIRED')),
        score DOUBLE PRECISION NOT NULL CHECK (score >= 0 AND score <= 1),
        reason TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(booking_id, worker_identity_id, worker_role))""",
    """CREATE UNIQUE INDEX IF NOT EXISTS ux_movement_one_accepted_match
        ON oap_movement_match_proposals(booking_id)
        WHERE state='ACCEPTED'""",
    """CREATE TABLE IF NOT EXISTS oap_movement_tracking_consents (
        booking_id UUID NOT NULL
            REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        identity_id UUID NOT NULL,
        state TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (state IN ('ACTIVE','REVOKED','EXPIRED')),
        expires_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (booking_id, identity_id))""",
    """CREATE TABLE IF NOT EXISTS oap_movement_tracking_points (
        point_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id UUID NOT NULL
            REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        identity_id UUID NOT NULL,
        latitude DOUBLE PRECISION NOT NULL
            CHECK (latitude >= -90 AND latitude <= 90),
        longitude DOUBLE PRECISION NOT NULL
            CHECK (longitude >= -180 AND longitude <= 180),
        recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMPTZ NOT NULL)""",
    """CREATE INDEX IF NOT EXISTS ix_movement_tracking_booking_recorded
        ON oap_movement_tracking_points(booking_id, recorded_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_movement_esim_requests (
        request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id UUID
            REFERENCES oap_movement_bookings(booking_id) ON DELETE SET NULL,
        identity_id UUID NOT NULL,
        purpose TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
            CHECK (state IN ('PROVIDER_REQUIRED','REQUESTED','APPROVED',
                             'PROVISIONED','REJECTED','CANCELLED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_movement_esim_identity_created
        ON oap_movement_esim_requests(identity_id, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_movement_payment_intents (
        intent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id UUID NOT NULL
            REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        member_identity_id UUID NOT NULL,
        amount_minor BIGINT NOT NULL CHECK (amount_minor >= 0),
        currency TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'
            CHECK (state IN ('PROVIDER_REQUIRED','CREATED','AUTHORIZED',
                             'CAPTURED','CANCELLED','FAILED')),
        provider_reference TEXT,
        idempotency_key TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_movement_payment_booking_created
        ON oap_movement_payment_intents(booking_id, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_movement_trip_channels (
        channel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        booking_id UUID NOT NULL UNIQUE
            REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
        state TEXT NOT NULL DEFAULT 'PENDING_LINK_UP'
            CHECK (state IN ('PENDING_LINK_UP','READY','CLOSED')),
        linkup_conversation_id UUID,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
)
MOVEMENT_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(MOVEMENT_SCHEMA_STATEMENTS).encode("utf-8")
).hexdigest()


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _service(value: object) -> str:
    service = str(value or "").strip().casefold()
    if service not in SERVICE_TYPES:
        raise ValueError("invalid_service_type")
    return service


def _role(value: object) -> str:
    role = str(value or "").strip().casefold()
    if role not in WORKER_ROLES:
        raise ValueError("invalid_worker_role")
    return role


def _availability_state(value: object) -> str:
    state = str(value or "").strip().upper()
    if state not in AVAILABILITY_STATES:
        raise ValueError("invalid_availability_state")
    return state


def _idempotency(value: object) -> str:
    key = str(value or "").strip()
    if not _IDEMPOTENCY.fullmatch(key):
        raise ValueError("invalid_idempotency_key")
    return key


def _bounded_text(value: object, *, name: str, maximum: int, required: bool = True) -> str:
    text = " ".join(str(value or "").strip().split())
    if required and not text:
        raise ValueError(f"{name}_required")
    if len(text) > maximum:
        raise ValueError(f"{name}_too_long")
    return text


def _coordinate(value: object, *, name: str, minimum: float, maximum: float) -> float:
    try:
        number = round(float(value), 6)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{name}") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"invalid_{name}")
    return number


def normalize_place(value: object, *, name: str) -> dict[str, Any]:
    """Normalize a private booking place without allowing arbitrary JSON blobs."""

    if not isinstance(value, dict):
        raise ValueError(f"invalid_{name}")
    return {
        "label": _bounded_text(
            value.get("label"), name=f"{name}_label", maximum=160
        ),
        "zone": _bounded_text(
            value.get("zone", ""),
            name=f"{name}_zone",
            maximum=40,
            required=False,
        ),
        "latitude": _coordinate(
            value.get("latitude"),
            name=f"{name}_latitude",
            minimum=-90,
            maximum=90,
        ),
        "longitude": _coordinate(
            value.get("longitude"),
            name=f"{name}_longitude",
            minimum=-180,
            maximum=180,
        ),
    }


def _timestamp(value: object, *, name: str, required: bool = False) -> datetime | None:
    if value in (None, ""):
        if required:
            raise ValueError(f"{name}_required")
        return None
    if isinstance(value, datetime):
        result = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            result = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"invalid_{name}") from exc
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def movement_schema_status() -> dict[str, Any]:
    """Return redacted schema readiness without changing production state."""

    result: dict[str, Any] = {
        "migration": MOVEMENT_MIGRATION_VERSION,
        "checksum": MOVEMENT_MIGRATION_CHECKSUM,
        "schema_ready": False,
        "tables": 0,
        "error": None,
    }
    base = postgres_db.postgres_status()
    if not base.get("initialized"):
        result["error"] = "base_postgres_not_ready"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public'"
                ).fetchall()
            }
            result["tables"] = len(MOVEMENT_TABLES & tables)
            if not MOVEMENT_TABLES <= tables:
                result["error"] = "movement_schema_pending"
                return result
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (MOVEMENT_MIGRATION_VERSION,),
            ).fetchone()
            if row is None or str(row[0]) != MOVEMENT_MIGRATION_CHECKSUM:
                result["error"] = "movement_migration_not_verified"
                return result
            result["schema_ready"] = True
            return result
    except Exception:  # noqa: BLE001 - redact database/provider details.
        result["error"] = "movement_store_unavailable"
        return result


def init_movement_schema(
    *, assume_yes: bool = False, dry_run: bool = False
) -> dict[str, Any]:
    """Apply the Movement schema only after explicit Human Authority invocation."""

    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    base = postgres_db.postgres_status()
    if not base.get("initialized"):
        raise RuntimeError("Base PostgreSQL schema must be ready first")
    if dry_run:
        return {
            "dry_run": True,
            "migration": MOVEMENT_MIGRATION_VERSION,
            "checksum": MOVEMENT_MIGRATION_CHECKSUM,
            "tables": len(MOVEMENT_TABLES),
        }
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800005,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (MOVEMENT_MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != MOVEMENT_MIGRATION_CHECKSUM:
            raise RuntimeError("Applied Movement migration checksum mismatch")
        if row is None:
            for statement in MOVEMENT_SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (MOVEMENT_MIGRATION_VERSION, MOVEMENT_MIGRATION_CHECKSUM),
            )
        connection.commit()
    return movement_schema_status()


class PostgresMovementStore:
    """Private Movement store. Every read is object-authorized."""

    def create_booking(
        self,
        *,
        member_identity_id: object,
        service_type: object,
        pickup: object,
        destination: object | None,
        scheduled_for: object = None,
        route_snapshot: dict[str, Any] | None = None,
        idempotency_key: object,
    ) -> dict[str, Any]:
        member = _uuid(member_identity_id, "member_identity_id")
        service = _service(service_type)
        pickup_value = normalize_place(pickup, name="pickup")
        destination_value = (
            normalize_place(destination, name="destination")
            if destination is not None
            else None
        )
        if service in {"ride", "delivery"} and destination_value is None:
            raise ValueError("destination_required")
        schedule = _timestamp(scheduled_for, name="scheduled_for")
        key = _idempotency(idempotency_key)
        route_value = dict(route_snapshot or {})
        if len(json.dumps(route_value, separators=(",", ":"))) > 4096:
            raise ValueError("route_snapshot_too_large")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_movement_bookings
                   (member_identity_id,service_type,pickup,destination,
                    scheduled_for,state,route_snapshot,idempotency_key)
                   VALUES (%s,%s,%s::jsonb,%s::jsonb,%s,'REQUESTED',%s::jsonb,%s)
                   ON CONFLICT (idempotency_key) DO UPDATE
                   SET idempotency_key=EXCLUDED.idempotency_key
                   RETURNING booking_id,service_type,state,scheduled_for,
                             created_at,updated_at""",
                (
                    member,
                    service,
                    json.dumps(pickup_value),
                    json.dumps(destination_value) if destination_value else None,
                    schedule,
                    json.dumps(route_value) if route_value else None,
                    key,
                ),
            ).fetchone()
            connection.commit()
        return {
            "booking_id": str(row[0]),
            "service_type": str(row[1]),
            "state": str(row[2]),
            "scheduled_for": row[3].isoformat() if row[3] else None,
            "created_at": row[4].isoformat(),
            "updated_at": row[5].isoformat(),
        }

    def get_booking(self, *, booking_id: object, identity_id: object) -> dict[str, Any] | None:
        booking = _uuid(booking_id, "booking_id")
        identity = _uuid(identity_id, "identity_id")
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT booking_id,member_identity_id,service_type,pickup,
                          destination,scheduled_for,state,route_snapshot,
                          created_at,updated_at
                   FROM oap_movement_bookings
                   WHERE booking_id=%s AND member_identity_id=%s""",
                (booking, identity),
            ).fetchone()
        if row is None:
            return None
        return {
            "booking_id": str(row[0]),
            "member_identity_id": str(row[1]),
            "service_type": str(row[2]),
            "pickup": dict(row[3]),
            "destination": dict(row[4]) if row[4] else None,
            "scheduled_for": row[5].isoformat() if row[5] else None,
            "state": str(row[6]),
            "route_snapshot": dict(row[7]) if row[7] else None,
            "created_at": row[8].isoformat(),
            "updated_at": row[9].isoformat(),
        }

    def certified_for_role(self, *, identity_id: object, role_type: object) -> bool:
        identity = _uuid(identity_id, "identity_id")
        role = _role(role_type)
        role_id = MOVEMENT_ROLE_IDS[role]
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM oap_identity_roles
                   WHERE identity_id=%s AND role_id=%s LIMIT 1""",
                (identity, role_id),
            ).fetchone()
        return row is not None

    def set_availability(
        self,
        *,
        identity_id: object,
        role_type: object,
        state: object,
        zone: object = "",
        available_until: object = None,
    ) -> dict[str, Any]:
        identity = _uuid(identity_id, "identity_id")
        role = _role(role_type)
        if not self.certified_for_role(identity_id=identity, role_type=role):
            raise PermissionError("certified_movement_role_required")
        normalized_state = _availability_state(state)
        normalized_zone = _bounded_text(
            zone, name="zone", maximum=40, required=False
        ).upper()
        until = _timestamp(available_until, name="available_until")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_movement_availability
                   (identity_id,role_type,availability_state,zone,available_until)
                   VALUES (%s,%s,%s,%s,%s)
                   ON CONFLICT (identity_id,role_type) DO UPDATE SET
                     availability_state=EXCLUDED.availability_state,
                     zone=EXCLUDED.zone,
                     available_until=EXCLUDED.available_until,
                     updated_at=CURRENT_TIMESTAMP
                   RETURNING role_type,availability_state,zone,available_until,updated_at""",
                (identity, role, normalized_state, normalized_zone, until),
            ).fetchone()
            connection.commit()
        return {
            "role_type": str(row[0]),
            "availability_state": str(row[1]),
            "zone": str(row[2]),
            "available_until": row[3].isoformat() if row[3] else None,
            "updated_at": row[4].isoformat(),
            "precise_location_stored": False,
        }

    def propose_match(
        self, *, booking_id: object, member_identity_id: object
    ) -> dict[str, Any] | None:
        booking = _uuid(booking_id, "booking_id")
        member = _uuid(member_identity_id, "member_identity_id")
        with postgres_db.connect() as connection:
            booking_row = connection.execute(
                """SELECT service_type,pickup,state FROM oap_movement_bookings
                   WHERE booking_id=%s AND member_identity_id=%s
                   FOR UPDATE""",
                (booking, member),
            ).fetchone()
            if booking_row is None:
                raise PermissionError("booking_not_found")
            service = str(booking_row[0])
            if str(booking_row[2]) not in {"REQUESTED", "MATCH_PROPOSED"}:
                raise ValueError("booking_not_matchable")
            roles = {
                "ride": ("driver",),
                "delivery": ("rider", "courier"),
                "ebike": (),
            }[service]
            if not roles:
                return None
            pickup = dict(booking_row[1])
            zone = str(pickup.get("zone") or "").upper()
            role_placeholders = ",".join(["%s"] * len(roles))
            query = f"""SELECT identity_id,role_type,zone
                         FROM oap_movement_availability
                         WHERE availability_state='ONLINE'
                           AND role_type IN ({role_placeholders})
                           AND (available_until IS NULL
                                OR available_until > CURRENT_TIMESTAMP)
                         ORDER BY
                           CASE WHEN zone=%s AND %s<>'' THEN 0 ELSE 1 END,
                           updated_at DESC
                         LIMIT 1"""
            candidate = connection.execute(query, (*roles, zone, zone)).fetchone()
            if candidate is None:
                return None
            same_zone = bool(zone and str(candidate[2]).upper() == zone)
            score = 1.0 if same_zone else 0.5
            reason = "same_zone_available" if same_zone else "available_candidate"
            row = connection.execute(
                """INSERT INTO oap_movement_match_proposals
                   (booking_id,worker_identity_id,worker_role,score,reason)
                   VALUES (%s,%s,%s,%s,%s)
                   ON CONFLICT (booking_id,worker_identity_id,worker_role)
                   DO UPDATE SET updated_at=CURRENT_TIMESTAMP
                   RETURNING proposal_id,worker_identity_id,worker_role,state,
                             score,reason,created_at""",
                (booking, candidate[0], candidate[1], score, reason),
            ).fetchone()
            connection.execute(
                """UPDATE oap_movement_bookings
                   SET state='MATCH_PROPOSED',updated_at=CURRENT_TIMESTAMP
                   WHERE booking_id=%s""",
                (booking,),
            )
            connection.commit()
        return {
            "proposal_id": str(row[0]),
            "worker_identity_id": str(row[1]),
            "worker_role": str(row[2]),
            "state": str(row[3]),
            "score": float(row[4]),
            "reason": str(row[5]),
            "created_at": row[6].isoformat(),
            "dispatch_performed": False,
        }

    def accept_match(self, *, proposal_id: object, worker_identity_id: object) -> dict[str, Any]:
        proposal = _uuid(proposal_id, "proposal_id")
        worker = _uuid(worker_identity_id, "worker_identity_id")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_movement_match_proposals
                   SET state='ACCEPTED',updated_at=CURRENT_TIMESTAMP
                   WHERE proposal_id=%s AND worker_identity_id=%s
                     AND state='PROPOSED'
                   RETURNING booking_id,worker_role,updated_at""",
                (proposal, worker),
            ).fetchone()
            if row is None:
                raise PermissionError("match_proposal_not_available")
            connection.execute(
                """UPDATE oap_movement_bookings
                   SET state='ACCEPTED',updated_at=CURRENT_TIMESTAMP
                   WHERE booking_id=%s""",
                (row[0],),
            )
            connection.execute(
                """UPDATE oap_movement_availability
                   SET availability_state='BUSY',updated_at=CURRENT_TIMESTAMP
                   WHERE identity_id=%s AND role_type=%s""",
                (worker, row[1]),
            )
            connection.commit()
        return {
            "booking_id": str(row[0]),
            "worker_role": str(row[1]),
            "state": "ACCEPTED",
            "updated_at": row[2].isoformat(),
            "external_dispatch_performed": False,
        }

    def is_participant(self, *, booking_id: object, identity_id: object) -> bool:
        booking = _uuid(booking_id, "booking_id")
        identity = _uuid(identity_id, "identity_id")
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM oap_movement_bookings b
                   WHERE b.booking_id=%s AND (
                     b.member_identity_id=%s OR EXISTS (
                       SELECT 1 FROM oap_movement_match_proposals p
                       WHERE p.booking_id=b.booking_id
                         AND p.worker_identity_id=%s
                         AND p.state='ACCEPTED'))
                   LIMIT 1""",
                (booking, identity, identity),
            ).fetchone()
        return row is not None

    def grant_tracking_consent(
        self,
        *,
        booking_id: object,
        identity_id: object,
        expires_at: object,
    ) -> dict[str, Any]:
        booking = _uuid(booking_id, "booking_id")
        identity = _uuid(identity_id, "identity_id")
        expiry = _timestamp(expires_at, name="expires_at", required=True)
        if expiry <= datetime.now(timezone.utc):
            raise ValueError("tracking_consent_must_expire_in_future")
        if not self.is_participant(booking_id=booking, identity_id=identity):
            raise PermissionError("booking_participant_required")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_movement_tracking_consents
                   (booking_id,identity_id,state,expires_at)
                   VALUES (%s,%s,'ACTIVE',%s)
                   ON CONFLICT (booking_id,identity_id) DO UPDATE SET
                     state='ACTIVE',expires_at=EXCLUDED.expires_at,
                     updated_at=CURRENT_TIMESTAMP
                   RETURNING state,expires_at,updated_at""",
                (booking, identity, expiry),
            ).fetchone()
            connection.commit()
        return {
            "state": str(row[0]),
            "expires_at": row[1].isoformat(),
            "updated_at": row[2].isoformat(),
            "scope": "own_location_only",
        }

    def revoke_tracking_consent(
        self, *, booking_id: object, identity_id: object
    ) -> bool:
        booking = _uuid(booking_id, "booking_id")
        identity = _uuid(identity_id, "identity_id")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_movement_tracking_consents
                   SET state='REVOKED',updated_at=CURRENT_TIMESTAMP
                   WHERE booking_id=%s AND identity_id=%s AND state='ACTIVE'
                   RETURNING 1""",
                (booking, identity),
            ).fetchone()
            connection.commit()
        return row is not None

    def record_tracking_point(
        self,
        *,
        booking_id: object,
        identity_id: object,
        latitude: object,
        longitude: object,
    ) -> dict[str, Any]:
        booking = _uuid(booking_id, "booking_id")
        identity = _uuid(identity_id, "identity_id")
        lat = _coordinate(latitude, name="latitude", minimum=-90, maximum=90)
        lon = _coordinate(longitude, name="longitude", minimum=-180, maximum=180)
        with postgres_db.connect() as connection:
            consent = connection.execute(
                """SELECT expires_at FROM oap_movement_tracking_consents
                   WHERE booking_id=%s AND identity_id=%s AND state='ACTIVE'
                     AND expires_at > CURRENT_TIMESTAMP
                   FOR UPDATE""",
                (booking, identity),
            ).fetchone()
            if consent is None:
                raise PermissionError("active_tracking_consent_required")
            row = connection.execute(
                """INSERT INTO oap_movement_tracking_points
                   (booking_id,identity_id,latitude,longitude,expires_at)
                   VALUES (%s,%s,%s,%s,%s)
                   RETURNING point_id,recorded_at,expires_at""",
                (booking, identity, lat, lon, consent[0]),
            ).fetchone()
            connection.commit()
        return {
            "point_id": str(row[0]),
            "recorded_at": row[1].isoformat(),
            "expires_at": row[2].isoformat(),
            "publicly_visible": False,
        }

    def request_esim_connectivity(
        self,
        *,
        identity_id: object,
        purpose: object,
        booking_id: object | None = None,
    ) -> dict[str, Any]:
        identity = _uuid(identity_id, "identity_id")
        purpose_text = _bounded_text(purpose, name="purpose", maximum=200)
        booking = _uuid(booking_id, "booking_id") if booking_id else None
        if booking and not self.is_participant(booking_id=booking, identity_id=identity):
            raise PermissionError("booking_participant_required")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_movement_esim_requests
                   (booking_id,identity_id,purpose,state)
                   VALUES (%s,%s,%s,'PROVIDER_REQUIRED')
                   RETURNING request_id,state,created_at""",
                (booking, identity, purpose_text),
            ).fetchone()
            connection.commit()
        return {
            "request_id": str(row[0]),
            "state": str(row[1]),
            "created_at": row[2].isoformat(),
            "activation_performed": False,
            "carrier_identifier_exposed": False,
        }

    def create_payment_intent(
        self,
        *,
        booking_id: object,
        member_identity_id: object,
        amount_minor: object,
        currency: object,
        idempotency_key: object,
    ) -> dict[str, Any]:
        booking = _uuid(booking_id, "booking_id")
        member = _uuid(member_identity_id, "member_identity_id")
        try:
            amount = int(amount_minor)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_amount_minor") from exc
        if amount < 0 or amount > 10_000_000:
            raise ValueError("invalid_amount_minor")
        currency_code = _bounded_text(currency, name="currency", maximum=3).upper()
        if len(currency_code) != 3 or not currency_code.isalpha():
            raise ValueError("invalid_currency")
        key = _idempotency(idempotency_key)
        with postgres_db.connect() as connection:
            owner = connection.execute(
                """SELECT 1 FROM oap_movement_bookings
                   WHERE booking_id=%s AND member_identity_id=%s""",
                (booking, member),
            ).fetchone()
            if owner is None:
                raise PermissionError("booking_not_found")
            row = connection.execute(
                """INSERT INTO oap_movement_payment_intents
                   (booking_id,member_identity_id,amount_minor,currency,
                    state,idempotency_key)
                   VALUES (%s,%s,%s,%s,'PROVIDER_REQUIRED',%s)
                   ON CONFLICT (idempotency_key) DO UPDATE
                   SET idempotency_key=EXCLUDED.idempotency_key
                   RETURNING intent_id,state,amount_minor,currency,created_at""",
                (booking, member, amount, currency_code, key),
            ).fetchone()
            connection.commit()
        return {
            "intent_id": str(row[0]),
            "state": str(row[1]),
            "amount_minor": int(row[2]),
            "currency": str(row[3]),
            "created_at": row[4].isoformat(),
            "payment_captured": False,
        }

    def ensure_trip_channel(
        self, *, booking_id: object, identity_id: object
    ) -> dict[str, Any]:
        booking = _uuid(booking_id, "booking_id")
        identity = _uuid(identity_id, "identity_id")
        if not self.is_participant(booking_id=booking, identity_id=identity):
            raise PermissionError("booking_participant_required")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_movement_trip_channels
                   (booking_id,state) VALUES (%s,'PENDING_LINK_UP')
                   ON CONFLICT (booking_id) DO UPDATE
                   SET updated_at=CURRENT_TIMESTAMP
                   RETURNING channel_id,state,linkup_conversation_id,created_at,
                             updated_at""",
                (booking,),
            ).fetchone()
            connection.commit()
        return {
            "channel_id": str(row[0]),
            "state": str(row[1]),
            "linkup_conversation_id": str(row[2]) if row[2] else None,
            "created_at": row[3].isoformat(),
            "updated_at": row[4].isoformat(),
            "message_store_duplicated": False,
        }


def migration_sql() -> str:
    """Return the exact idempotent SQL for branch-first Neon migration review."""

    statements = list(MOVEMENT_SCHEMA_STATEMENTS)
    statements.append(
        "INSERT INTO oap_schema_migrations(version,checksum) "
        f"VALUES ('{MOVEMENT_MIGRATION_VERSION}','{MOVEMENT_MIGRATION_CHECKSUM}') "
        "ON CONFLICT (version) DO NOTHING"
    )
    return ";\n\n".join(statements) + ";\n"


STORE = PostgresMovementStore()
