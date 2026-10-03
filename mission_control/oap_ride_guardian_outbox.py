# ruff: noqa: I001
"""OAP Ride Guardian trusted-contact outbox.

Creates durable first-party notification jobs. It does not claim external
delivery; a separate approved delivery adapter must mark delivery evidence.
"""
from __future__ import annotations
import hashlib
from typing import Any
from uuid import UUID
from . import postgres_db

MIGRATION="0007_oap_ride_guardian_outbox"
TABLES=frozenset({"oap_ride_guardian_outbox"})
STATEMENTS=(
"""CREATE TABLE IF NOT EXISTS oap_ride_guardian_outbox (
 notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 booking_id UUID NOT NULL REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
 trusted_contact_ref TEXT NOT NULL,
 event_type TEXT NOT NULL CHECK (event_type IN ('GUARDIAN_ENABLED','SAFETY_CONCERN','UNEXPECTED_STOP','ROUTE_DEVIATION')),
 payload JSONB NOT NULL,
 state TEXT NOT NULL DEFAULT 'PENDING_ADAPTER' CHECK (state IN ('PENDING_ADAPTER','DELIVERED','FAILED','CANCELLED')),
 delivery_evidence_ref TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
)
CHECKSUM=hashlib.sha256("\n".join(STATEMENTS).encode()).hexdigest()

def _uuid(value:object,name:str)->str:
    try:return str(UUID(str(value)))
    except Exception as exc: raise ValueError(f"invalid_{name}") from exc

def init_schema(*,assume_yes:bool=False,dry_run:bool=False)->dict[str,Any]:
    if not assume_yes: raise RuntimeError("explicit_human_approval_required")
    if dry_run:return {"dry_run":True,"migration":MIGRATION,"checksum":CHECKSUM,"tables":1}
    with postgres_db.connect() as c:
        c.execute("SELECT pg_advisory_xact_lock(%s)",(25800027,))
        row=c.execute("SELECT checksum FROM oap_schema_migrations WHERE version=%s",(MIGRATION,)).fetchone()
        if row is not None and str(row[0])!=CHECKSUM: raise RuntimeError("ride_guardian_outbox_migration_checksum_mismatch")
        if row is None:
            for stmt in STATEMENTS:c.execute(stmt)
            c.execute("INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",(MIGRATION,CHECKSUM))
        c.commit()
    return {"migration":MIGRATION,"schema_ready":True,"tables":1}

def enqueue(*,booking_id:object,event_type:object,payload:object)->dict[str,Any]:
    booking=_uuid(booking_id,"booking_id")
    event=str(event_type or "").strip().upper()
    if event not in {"GUARDIAN_ENABLED","SAFETY_CONCERN","UNEXPECTED_STOP","ROUTE_DEVIATION"}:
        raise ValueError("invalid_guardian_outbox_event")
    if not isinstance(payload,dict): raise TypeError("invalid_guardian_outbox_payload")
    import json
    encoded=json.dumps(payload,separators=(",",":"))
    if len(encoded)>4096: raise ValueError("guardian_outbox_payload_too_large")
    with postgres_db.connect() as c:
        session=c.execute("""SELECT trusted_contact_ref,enabled FROM oap_ride_guardian_sessions
          WHERE booking_id=%s""",(booking,)).fetchone()
        if session is None or session[1] is not True: raise PermissionError("guardian_session_required")
        contact=str(session[0] or "").strip()
        if not contact: raise PermissionError("trusted_contact_reference_required")
        row=c.execute("""INSERT INTO oap_ride_guardian_outbox
          (booking_id,trusted_contact_ref,event_type,payload)
          VALUES (%s,%s,%s,%s::jsonb)
          RETURNING notification_id,state,created_at""",
          (booking,contact,event,encoded)).fetchone(); c.commit()
    return {"notification_id":str(row[0]),"booking_id":booking,"event_type":event,
            "state":str(row[1]),"created_at":row[2].isoformat(),"delivered":False}
