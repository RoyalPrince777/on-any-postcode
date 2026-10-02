"""OAP Ride Guardian: participant-scoped digital safety records.

No covert tracking, emergency-service impersonation, or automatic physical response.
"""
from __future__ import annotations
import hashlib
from typing import Any
from uuid import UUID
from . import postgres_db

MIGRATION="0002_oap_ride_guardian"
TABLES=frozenset({"oap_ride_guardian_sessions","oap_ride_guardian_incidents"})
STATEMENTS=(
"""CREATE TABLE IF NOT EXISTS oap_ride_guardian_sessions (
 booking_id UUID PRIMARY KEY REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
 enabled BOOLEAN NOT NULL DEFAULT FALSE,
 trusted_contact_ref TEXT NOT NULL DEFAULT '',
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
"""CREATE TABLE IF NOT EXISTS oap_ride_guardian_incidents (
 incident_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 booking_id UUID NOT NULL REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
 reporter_identity_id UUID NOT NULL,
 kind TEXT NOT NULL CHECK (kind IN ('SAFETY_CONCERN','UNEXPECTED_STOP','ROUTE_DEVIATION','OTHER')),
 note TEXT NOT NULL DEFAULT '',
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
)
CHECKSUM=hashlib.sha256("\n".join(STATEMENTS).encode()).hexdigest()

def _uuid(value:object,name:str)->str:
    try:return str(UUID(str(value)))
    except Exception as exc: raise ValueError(f"invalid_{name}") from exc

def _participant(connection,booking:str,identity:str)->bool:
    return connection.execute(
        """SELECT 1 FROM oap_movement_bookings b WHERE b.booking_id=%s AND
        (b.member_identity_id=%s OR EXISTS (
          SELECT 1 FROM oap_movement_match_proposals p
          WHERE p.booking_id=b.booking_id AND p.worker_identity_id=%s AND p.state='ACCEPTED'
        )) LIMIT 1""",(booking,identity,identity)).fetchone() is not None

def init_schema(*,assume_yes:bool=False,dry_run:bool=False)->dict[str,Any]:
    if not assume_yes: raise RuntimeError("explicit_human_approval_required")
    if dry_run:return {"dry_run":True,"migration":MIGRATION,"checksum":CHECKSUM,"tables":len(TABLES)}
    with postgres_db.connect() as c:
        c.execute("SELECT pg_advisory_xact_lock(%s)",(25800022,))
        row=c.execute("SELECT checksum FROM oap_schema_migrations WHERE version=%s",(MIGRATION,)).fetchone()
        if row is not None and str(row[0])!=CHECKSUM: raise RuntimeError("ride_guardian_migration_checksum_mismatch")
        if row is None:
            for stmt in STATEMENTS:c.execute(stmt)
            c.execute("INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",(MIGRATION,CHECKSUM))
        c.commit()
    return status()

def status()->dict[str,Any]:
    result={"migration":MIGRATION,"schema_ready":False,"tables":0,"covert_tracking":False,"automatic_emergency_dispatch":False}
    try:
        with postgres_db.connect(readonly=True) as c:
            tables={str(r[0]) for r in c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'").fetchall()}
            result["tables"]=len(TABLES & tables)
            row=c.execute("SELECT checksum FROM oap_schema_migrations WHERE version=%s",(MIGRATION,)).fetchone()
            result["schema_ready"]=TABLES<=tables and row is not None and str(row[0])==CHECKSUM
    except Exception: result["error"]="ride_guardian_store_unavailable"
    return result

def set_session(*,booking_id:object,identity_id:object,enabled:bool,trusted_contact_ref:object="")->dict[str,Any]:
    booking=_uuid(booking_id,"booking_id"); identity=_uuid(identity_id,"identity_id")
    if type(enabled) is not bool: raise ValueError("invalid_guardian_state")
    ref=" ".join(str(trusted_contact_ref or "").strip().split())[:160]
    with postgres_db.connect() as c:
        if not _participant(c,booking,identity): raise PermissionError("booking_participant_required")
        row=c.execute("""INSERT INTO oap_ride_guardian_sessions(booking_id,enabled,trusted_contact_ref)
        VALUES (%s,%s,%s) ON CONFLICT (booking_id) DO UPDATE SET enabled=EXCLUDED.enabled,
        trusted_contact_ref=EXCLUDED.trusted_contact_ref,updated_at=CURRENT_TIMESTAMP
        RETURNING enabled,trusted_contact_ref,updated_at""",(booking,enabled,ref)).fetchone(); c.commit()
    return {"booking_id":booking,"enabled":bool(row[0]),"trusted_contact_ref":str(row[1]),"updated_at":row[2].isoformat(),"covert_tracking":False}

def report_incident(*,booking_id:object,identity_id:object,kind:object,note:object="")->dict[str,Any]:
    booking=_uuid(booking_id,"booking_id"); identity=_uuid(identity_id,"identity_id")
    kinds={"SAFETY_CONCERN","UNEXPECTED_STOP","ROUTE_DEVIATION","OTHER"}
    k=str(kind or "").strip().upper()
    if k not in kinds: raise ValueError("invalid_guardian_incident")
    text=" ".join(str(note or "").strip().split())[:500]
    with postgres_db.connect() as c:
        if not _participant(c,booking,identity): raise PermissionError("booking_participant_required")
        row=c.execute("""INSERT INTO oap_ride_guardian_incidents(booking_id,reporter_identity_id,kind,note)
        VALUES (%s,%s,%s,%s) RETURNING incident_id,created_at""",(booking,identity,k,text)).fetchone(); c.commit()
    return {"incident_id":str(row[0]),"booking_id":booking,"kind":k,"created_at":row[1].isoformat(),"automatic_emergency_dispatch":False}
