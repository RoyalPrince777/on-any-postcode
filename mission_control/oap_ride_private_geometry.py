"""Private route geometry for OAP Ride Guardian.

Persists only route geometry proven by the OAP-owned production-gated route
engine. Geometry is participant-private and never exposed by public Movement.
"""
from __future__ import annotations
import hashlib, json
from typing import Any
from uuid import UUID
from . import first_party_route_proof, postgres_db

MIGRATION="0006_oap_ride_private_geometry"
TABLES=frozenset({"oap_ride_private_route_geometry"})
STATEMENTS=(
"""CREATE TABLE IF NOT EXISTS oap_ride_private_route_geometry (
 booking_id UUID PRIMARY KEY REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
 geometry JSONB NOT NULL,
 geometry_sha256 TEXT NOT NULL,
 source TEXT NOT NULL,
 source_timestamp TIMESTAMPTZ NOT NULL,
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
        c.execute("SELECT pg_advisory_xact_lock(%s)",(25800026,))
        row=c.execute("SELECT checksum FROM oap_schema_migrations WHERE version=%s",(MIGRATION,)).fetchone()
        if row is not None and str(row[0])!=CHECKSUM: raise RuntimeError("ride_geometry_migration_checksum_mismatch")
        if row is None:
            for stmt in STATEMENTS:c.execute(stmt)
            c.execute("INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",(MIGRATION,CHECKSUM))
        c.commit()
    return {"migration":MIGRATION,"schema_ready":True,"tables":1}

def prove_and_store(*,booking_id:object,identity_id:object)->dict[str,Any]:
    booking=_uuid(booking_id,"booking_id"); identity=_uuid(identity_id,"identity_id")
    with postgres_db.connect(readonly=True) as c:
        row=c.execute("""SELECT member_identity_id,pickup,destination,state
          FROM oap_movement_bookings WHERE booking_id=%s AND service_type='ride'""",(booking,)).fetchone()
        accepted=c.execute("""SELECT worker_identity_id FROM oap_movement_match_proposals
          WHERE booking_id=%s AND state='ACCEPTED' LIMIT 1""",(booking,)).fetchone()
    if row is None: raise PermissionError("ride_booking_required")
    participants={str(row[0])}
    if accepted is not None: participants.add(str(accepted[0]))
    if identity not in participants: raise PermissionError("booking_participant_required")
    pickup=dict(row[1]); destination=dict(row[2]) if row[2] else None
    if destination is None: raise ValueError("destination_required")
    proof=first_party_route_proof.prove_route_geometry(
        pickup_latitude=pickup.get("latitude"),pickup_longitude=pickup.get("longitude"),
        destination_latitude=destination.get("latitude"),destination_longitude=destination.get("longitude"),
        profile="driving",
    )
    geometry=proof["geometry"]
    canonical=json.dumps(geometry,sort_keys=True,separators=(",",":"))
    digest=hashlib.sha256(canonical.encode()).hexdigest()
    if digest!=proof.get("geometry_sha256"): raise RuntimeError("route_geometry_hash_mismatch")
    with postgres_db.connect() as c:
        c.execute("""INSERT INTO oap_ride_private_route_geometry
          (booking_id,geometry,geometry_sha256,source,source_timestamp)
          VALUES (%s,%s::jsonb,%s,%s,%s)
          ON CONFLICT (booking_id) DO UPDATE SET geometry=EXCLUDED.geometry,
          geometry_sha256=EXCLUDED.geometry_sha256,source=EXCLUDED.source,
          source_timestamp=EXCLUDED.source_timestamp,updated_at=CURRENT_TIMESTAMP""",
          (booking,canonical,digest,str(proof.get("source") or "OAP Routing"),proof["source_timestamp"])); c.commit()
    return {"booking_id":booking,"geometry_sha256":digest,"route_geometry_proven":True,
            "provider_ownership":"oap_owned","public_geometry_exposed":False}

def read_private(*,booking_id:object,identity_id:object)->dict[str,Any]:
    booking=_uuid(booking_id,"booking_id"); identity=_uuid(identity_id,"identity_id")
    with postgres_db.connect(readonly=True) as c:
        participant=c.execute("""SELECT 1 FROM oap_movement_bookings b WHERE b.booking_id=%s AND
          (b.member_identity_id=%s OR EXISTS (SELECT 1 FROM oap_movement_match_proposals p
          WHERE p.booking_id=b.booking_id AND p.worker_identity_id=%s AND p.state='ACCEPTED')) LIMIT 1""",
          (booking,identity,identity)).fetchone()
        if participant is None: raise PermissionError("booking_participant_required")
        row=c.execute("""SELECT geometry,geometry_sha256,source,source_timestamp
          FROM oap_ride_private_route_geometry WHERE booking_id=%s""",(booking,)).fetchone()
    if row is None: raise PermissionError("private_route_geometry_not_available")
    return {"booking_id":booking,"geometry":dict(row[0]),"geometry_sha256":str(row[1]),
            "source":str(row[2]),"source_timestamp":row[3].isoformat(),"public_geometry_exposed":False}
