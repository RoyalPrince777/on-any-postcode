"""Canonical non-live OAP Distribution runtime.

Owns one shared lifecycle across Music, TV/Media, Sport, Clothing, Creator,
Market fulfilment and Local/Post. It records state and evidence only. It never
publishes externally, captures payment, dispatches a parcel, calls a carrier or
moves money.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from . import distribution_700, postgres_db

MIGRATION_VERSION = "distribution_runtime_v1"

STATES = (
    "CREATED",
    "RIGHTS_READY",
    "LISTED",
    "ORDERED",
    "DISTRIBUTION_READY",
    "ROUTED",
    "HANDED_OFF",
    "DELIVERED",
    "RECEIPT_RECORDED",
    "CLOSED",
    "STOPPED",
    "DISPUTED",
    "RETURNED",
    "FAILED",
    "RECOVERY_REQUIRED",
)

TERMINAL_STATES = frozenset({"CLOSED", "STOPPED", "RETURNED", "FAILED"})

TRANSITIONS: dict[str, frozenset[str]] = {
    "CREATED": frozenset({"RIGHTS_READY", "STOPPED", "FAILED"}),
    "RIGHTS_READY": frozenset({"LISTED", "STOPPED", "FAILED"}),
    "LISTED": frozenset({"ORDERED", "STOPPED", "FAILED"}),
    "ORDERED": frozenset({"DISTRIBUTION_READY", "DISPUTED", "STOPPED", "FAILED"}),
    "DISTRIBUTION_READY": frozenset({"ROUTED", "DISPUTED", "STOPPED", "FAILED", "RECOVERY_REQUIRED"}),
    "ROUTED": frozenset({"HANDED_OFF", "DELIVERED", "DISPUTED", "FAILED", "RECOVERY_REQUIRED"}),
    "HANDED_OFF": frozenset({"DELIVERED", "DISPUTED", "RETURNED", "FAILED", "RECOVERY_REQUIRED"}),
    "DELIVERED": frozenset({"RECEIPT_RECORDED", "DISPUTED", "RETURNED", "RECOVERY_REQUIRED"}),
    "RECEIPT_RECORDED": frozenset({"CLOSED", "DISPUTED", "RETURNED", "RECOVERY_REQUIRED"}),
    "DISPUTED": frozenset({"RECOVERY_REQUIRED", "RETURNED", "CLOSED"}),
    "RECOVERY_REQUIRED": frozenset({
        "DISTRIBUTION_READY", "ROUTED", "HANDED_OFF", "DELIVERED",
        "RECEIPT_RECORDED", "STOPPED", "FAILED",
    }),
    "CLOSED": frozenset(),
    "STOPPED": frozenset(),
    "RETURNED": frozenset(),
    "FAILED": frozenset({"RECOVERY_REQUIRED"}),
}

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_distribution_runtime (
        distribution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        lane TEXT NOT NULL,
        subject_type TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'CREATED',
        source_reference TEXT NOT NULL,
        destination_reference TEXT NOT NULL,
        order_id UUID NULL REFERENCES oap_commerce_orders(order_id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(owner_identity_id,lane,subject_type,subject_id))""",
    """CREATE TABLE IF NOT EXISTS oap_distribution_runtime_events (
        event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        distribution_id UUID NOT NULL REFERENCES oap_distribution_runtime(distribution_id) ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        from_state TEXT NULL,
        to_state TEXT NOT NULL,
        evidence_reference TEXT NOT NULL,
        previous_hash TEXT NOT NULL DEFAULT '',
        event_hash TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_distribution_runtime_owner_updated
       ON oap_distribution_runtime(owner_identity_id,updated_at DESC)""",
    """CREATE INDEX IF NOT EXISTS ix_distribution_runtime_events_distribution
       ON oap_distribution_runtime_events(distribution_id,created_at,event_id)""",
)

SCHEMA_CHECKSUM = hashlib.sha256("\n".join(SCHEMA_STATEMENTS).encode()).hexdigest()


class DistributionRuntimeError(ValueError):
    pass


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise DistributionRuntimeError(f"invalid_{name}") from exc


def _required(value: object, name: str, *, max_len: int = 500) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        raise DistributionRuntimeError(f"{name}_required")
    return text[:max_len]


def _lane(value: object) -> str:
    lane = str(value or "").strip().lower()
    if lane not in distribution_700.DISTRIBUTION_LANES:
        raise DistributionRuntimeError("unsupported_distribution_lane")
    return lane


def validate_transition(current_state: object, target_state: object) -> tuple[str, str]:
    current = str(current_state or "").strip().upper()
    target = str(target_state or "").strip().upper()
    if current not in TRANSITIONS or target not in STATES:
        raise DistributionRuntimeError("invalid_distribution_state")
    if target not in TRANSITIONS[current]:
        raise DistributionRuntimeError("distribution_transition_not_allowed")
    return current, target


def _event_hash(
    *,
    distribution_id: str,
    owner_identity_id: str,
    from_state: str | None,
    to_state: str,
    evidence_reference: str,
    previous_hash: str,
) -> str:
    payload = {
        "distribution_id": distribution_id,
        "owner_identity_id": owner_identity_id,
        "from_state": from_state,
        "to_state": to_state,
        "evidence_reference": evidence_reference,
        "previous_hash": previous_hash,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def verify_event_chain(events: object) -> dict[str, object]:
    rows = events if isinstance(events, (list, tuple)) else ()
    previous = ""
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            return {"verified": False, "reason": "event_invalid", "index": index}
        expected = _event_hash(
            distribution_id=str(row.get("distribution_id") or ""),
            owner_identity_id=str(row.get("owner_identity_id") or ""),
            from_state=row.get("from_state"),
            to_state=str(row.get("to_state") or ""),
            evidence_reference=str(row.get("evidence_reference") or ""),
            previous_hash=previous,
        )
        if row.get("previous_hash") != previous:
            return {"verified": False, "reason": "previous_hash_mismatch", "index": index}
        if row.get("event_hash") != expected:
            return {"verified": False, "reason": "event_hash_mismatch", "index": index}
        previous = expected
    return {"verified": True, "event_count": len(rows), "head_hash": previous}


class DistributionRuntimeStore:
    def create(
        self,
        *,
        owner_identity_id: object,
        lane: object,
        subject_type: object,
        subject_id: object,
        source_reference: object,
        destination_reference: object,
        order_id: object | None = None,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        safe_lane = _lane(lane)
        safe_subject_type = _required(subject_type, "subject_type", max_len=120)
        safe_subject_id = _required(subject_id, "subject_id", max_len=240)
        source = _required(source_reference, "source_reference")
        destination = _required(destination_reference, "destination_reference")
        order = _uuid(order_id, "order_id") if order_id is not None else None
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_distribution_runtime
                   (owner_identity_id,lane,subject_type,subject_id,source_reference,
                    destination_reference,order_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (owner_identity_id,lane,subject_type,subject_id)
                   DO UPDATE SET destination_reference=EXCLUDED.destination_reference
                   RETURNING distribution_id,state,created_at,updated_at""",
                (owner, safe_lane, safe_subject_type, safe_subject_id, source, destination, order),
            ).fetchone()
            distribution_id = str(row[0])
            existing = connection.execute(
                """SELECT event_hash FROM oap_distribution_runtime_events
                   WHERE distribution_id=%s ORDER BY created_at,event_id LIMIT 1""",
                (distribution_id,),
            ).fetchone()
            if existing is None:
                event_hash = _event_hash(
                    distribution_id=distribution_id,
                    owner_identity_id=owner,
                    from_state=None,
                    to_state="CREATED",
                    evidence_reference=source,
                    previous_hash="",
                )
                connection.execute(
                    """INSERT INTO oap_distribution_runtime_events
                       (distribution_id,owner_identity_id,from_state,to_state,
                        evidence_reference,previous_hash,event_hash)
                       VALUES (%s,%s,NULL,'CREATED',%s,'',%s)""",
                    (distribution_id, owner, source, event_hash),
                )
            connection.commit()
        return self.read(owner_identity_id=owner, distribution_id=distribution_id)

    def transition(
        self,
        *,
        owner_identity_id: object,
        distribution_id: object,
        target_state: object,
        evidence_reference: object,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        dist = _uuid(distribution_id, "distribution_id")
        evidence = _required(evidence_reference, "evidence_reference")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """SELECT state FROM oap_distribution_runtime
                   WHERE distribution_id=%s AND owner_identity_id=%s FOR UPDATE""",
                (dist, owner),
            ).fetchone()
            if row is None:
                raise PermissionError("distribution_not_owned")
            current, target = validate_transition(row[0], target_state)
            previous = connection.execute(
                """SELECT event_hash FROM oap_distribution_runtime_events
                   WHERE distribution_id=%s
                   ORDER BY created_at DESC,event_id DESC LIMIT 1""",
                (dist,),
            ).fetchone()
            previous_hash = str(previous[0]) if previous else ""
            event_hash = _event_hash(
                distribution_id=dist,
                owner_identity_id=owner,
                from_state=current,
                to_state=target,
                evidence_reference=evidence,
                previous_hash=previous_hash,
            )
            connection.execute(
                """UPDATE oap_distribution_runtime
                   SET state=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE distribution_id=%s AND owner_identity_id=%s""",
                (target, dist, owner),
            )
            connection.execute(
                """INSERT INTO oap_distribution_runtime_events
                   (distribution_id,owner_identity_id,from_state,to_state,
                    evidence_reference,previous_hash,event_hash)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (dist, owner, current, target, evidence, previous_hash, event_hash),
            )
            connection.commit()
        return self.read(owner_identity_id=owner, distribution_id=dist)

    def read(self, *, owner_identity_id: object, distribution_id: object) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        dist = _uuid(distribution_id, "distribution_id")
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT distribution_id,lane,subject_type,subject_id,state,
                          source_reference,destination_reference,order_id,
                          created_at,updated_at
                   FROM oap_distribution_runtime
                   WHERE distribution_id=%s AND owner_identity_id=%s""",
                (dist, owner),
            ).fetchone()
            if row is None:
                raise PermissionError("distribution_not_owned")
            events = connection.execute(
                """SELECT distribution_id,owner_identity_id,from_state,to_state,
                          evidence_reference,previous_hash,event_hash,created_at
                   FROM oap_distribution_runtime_events
                   WHERE distribution_id=%s AND owner_identity_id=%s
                   ORDER BY created_at,event_id""",
                (dist, owner),
            ).fetchall()
        event_rows = [
            {
                "distribution_id": str(event[0]),
                "owner_identity_id": str(event[1]),
                "from_state": event[2],
                "to_state": event[3],
                "evidence_reference": event[4],
                "previous_hash": event[5],
                "event_hash": event[6],
                "created_at": event[7].isoformat(),
            }
            for event in events
        ]
        return {
            "distribution_id": str(row[0]),
            "lane": row[1],
            "subject_type": row[2],
            "subject_id": row[3],
            "state": row[4],
            "source_reference": row[5],
            "destination_reference": row[6],
            "order_id": str(row[7]) if row[7] else None,
            "created_at": row[8].isoformat(),
            "updated_at": row[9].isoformat(),
            "events": event_rows,
            "chain": verify_event_chain(event_rows),
            "external_execution_performed": False,
            "payment_capture_performed": False,
            "dispatch_performed": False,
            "carrier_handoff_performed": False,
            "human_authority_final": True,
        }

    def list_for_owner(self, *, owner_identity_id: object) -> list[dict[str, object]]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT distribution_id,lane,subject_type,subject_id,state,
                          destination_reference,updated_at
                   FROM oap_distribution_runtime
                   WHERE owner_identity_id=%s
                   ORDER BY updated_at DESC,distribution_id""",
                (owner,),
            ).fetchall()
        return [
            {
                "distribution_id": str(row[0]),
                "lane": row[1],
                "subject_type": row[2],
                "subject_id": row[3],
                "state": row[4],
                "destination_reference": row[5],
                "updated_at": row[6].isoformat(),
            }
            for row in rows
        ]

    def analytics(self, *, owner_identity_id: object) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        with postgres_db.connect(readonly=True) as connection:
            by_state = connection.execute(
                """SELECT state,COUNT(*) FROM oap_distribution_runtime
                   WHERE owner_identity_id=%s GROUP BY state ORDER BY state""",
                (owner,),
            ).fetchall()
            by_lane = connection.execute(
                """SELECT lane,COUNT(*) FROM oap_distribution_runtime
                   WHERE owner_identity_id=%s GROUP BY lane ORDER BY lane""",
                (owner,),
            ).fetchall()
        state_counts = {str(state): int(count) for state, count in by_state}
        lane_counts = {str(lane): int(count) for lane, count in by_lane}
        return {
            "total": sum(state_counts.values()),
            "by_state": state_counts,
            "by_lane": lane_counts,
            "closed": state_counts.get("CLOSED", 0),
            "recovery_required": state_counts.get("RECOVERY_REQUIRED", 0),
            "disputed": state_counts.get("DISPUTED", 0),
            "external_execution_performed": False,
            "human_authority_final": True,
        }


def init_schema(*, assume_yes: bool = False, dry_run: bool = True) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "dry_run": True,
            "migration": MIGRATION_VERSION,
            "checksum": SCHEMA_CHECKSUM,
            "statements": len(SCHEMA_STATEMENTS),
        }
    with postgres_db.connect() as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.execute(
            """INSERT INTO oap_schema_migrations(version,checksum)
               VALUES (%s,%s) ON CONFLICT (version) DO NOTHING""",
            (MIGRATION_VERSION, SCHEMA_CHECKSUM),
        )
        connection.commit()
    return {
        "dry_run": False,
        "migration": MIGRATION_VERSION,
        "checksum": SCHEMA_CHECKSUM,
        "statements": len(SCHEMA_STATEMENTS),
    }


def status() -> dict[str, object]:
    return {
        "system": "OAP Distribution Runtime",
        "lanes": distribution_700.DISTRIBUTION_LANES,
        "states": STATES,
        "append_only_event_chain": True,
        "owner_scoped_tracking": True,
        "analytics_available": True,
        "recovery_state_supported": True,
        "external_execution_enabled": False,
        "payment_capture": False,
        "dispatch_execution": False,
        "carrier_handoff_execution": False,
        "human_authority_final": True,
    }
