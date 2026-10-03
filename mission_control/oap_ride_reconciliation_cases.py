"""Ride-specific ownership for SIKA reconciliation exceptions."""
from __future__ import annotations
import hashlib
from typing import Any
from uuid import UUID
from . import postgres_db, oap_ride_payment_bridge, sika_reconciliation_exception_store

MIGRATION="0008_oap_ride_reconciliation_cases"
TABLES=frozenset({"oap_ride_reconciliation_cases"})
STATEMENTS=(
"""CREATE TABLE IF NOT EXISTS oap_ride_reconciliation_cases (
 booking_id UUID NOT NULL REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
 exception_id TEXT NOT NULL UNIQUE,
 payment_id TEXT NOT NULL,
 state TEXT NOT NULL CHECK (state IN ('OPEN','IN_REVIEW','RESOLVED','CLOSED')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY (booking_id,exception_id))""",
)
CHECKSUM=hashlib.sha256("\n".join(STATEMENTS).encode()).hexdigest()

def _uuid(v,n):
    try:return str(UUID(str(v)))
    except Exception as exc: raise ValueError(f"invalid_{n}") from exc

def init_schema(*,assume_yes=False,dry_run=False)->dict[str,Any]:
    if not assume_yes: raise RuntimeError("explicit_human_approval_required")
    if dry_run:return {"dry_run":True,"migration":MIGRATION,"checksum":CHECKSUM,"tables":1}
    with postgres_db.connect() as c:
        c.execute("SELECT pg_advisory_xact_lock(%s)",(25800028,))
        row=c.execute("SELECT checksum FROM oap_schema_migrations WHERE version=%s",(MIGRATION,)).fetchone()
        if row is not None and str(row[0])!=CHECKSUM: raise RuntimeError("ride_reconciliation_case_migration_checksum_mismatch")
        if row is None:
            for stmt in STATEMENTS:c.execute(stmt)
            c.execute("INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",(MIGRATION,CHECKSUM))
        c.commit()
    return {"migration":MIGRATION,"schema_ready":True,"tables":1}

def create_case(*,booking_id:object,reconciliation_result:object,provider_id:object,provider_reference:object,evidence_hash:object)->dict[str,Any]:
    booking=_uuid(booking_id,"booking_id")
    if not isinstance(reconciliation_result,dict): raise TypeError("invalid_reconciliation_result")
    state=str(reconciliation_result.get("state") or "").upper()
    if state=="MATCHED": raise ValueError("matched_reconciliation_needs_no_exception")
    mapped="PENDING" if state=="PENDING" else "MISMATCH" if state=="MISMATCH" else "EXCEPTION"
    projection=oap_ride_payment_bridge.projection(booking_id=booking)
    if not projection.get("bound"): raise ValueError("ride_payment_not_bound")
    payment_id=str(projection.get("payment_id"))
    exception_id=f"ride:{booking}:{hashlib.sha256((payment_id+mapped+str(evidence_hash)).encode()).hexdigest()[:24]}"
    case=sika_reconciliation_exception_store.create_case(
        exception_id=exception_id,payment_id=payment_id,provider_id=provider_id,
        provider_reference=provider_reference,reconciliation_state=mapped,evidence_hash=evidence_hash
    )
    with postgres_db.connect() as c:
        c.execute("""INSERT INTO oap_ride_reconciliation_cases(booking_id,exception_id,payment_id,state)
        VALUES (%s,%s,%s,'OPEN') ON CONFLICT (booking_id,exception_id) DO NOTHING""",
        (booking,case.exception_id,payment_id)); c.commit()
    return {"booking_id":booking,"exception_id":case.exception_id,"payment_id":payment_id,
            "state":"OPEN","human_review_required":True,"money_moved":False}

def list_for_participant(*,identity_id:object,limit:int=50)->dict[str,Any]:
    identity=_uuid(identity_id,"identity_id"); bounded=min(max(int(limit),1),100)
    with postgres_db.connect(readonly=True) as c:
        rows=c.execute("""SELECT rc.booking_id,rc.exception_id,rc.payment_id,rc.state,rc.created_at
        FROM oap_ride_reconciliation_cases rc JOIN oap_movement_bookings b ON b.booking_id=rc.booking_id
        WHERE b.member_identity_id=%s OR EXISTS (
          SELECT 1 FROM oap_movement_match_proposals p WHERE p.booking_id=b.booking_id
          AND p.worker_identity_id=%s AND p.state='ACCEPTED')
        ORDER BY rc.created_at DESC LIMIT %s""",(identity,identity,bounded)).fetchall()
    return {"cases":[{"booking_id":str(r[0]),"exception_id":str(r[1]),"payment_id":str(r[2]),"state":str(r[3]),"created_at":r[4].isoformat()} for r in rows]}
