"""OAP Ride -> canonical SIKA payment bridge.

Binds an owner-scoped Ride booking to one canonical SIKA payment intent and
projects provider-submission evidence. It never authorises, submits, settles,
posts journals or moves money.
"""
from __future__ import annotations
import hashlib
from typing import Any
from uuid import UUID

from . import postgres_db, sika_payment_orchestrator

MIGRATION="0004_oap_ride_payment_bridge"
TABLES=frozenset({"oap_ride_payment_bindings"})
STATEMENTS=(
"""CREATE TABLE IF NOT EXISTS oap_ride_payment_bindings (
 booking_id UUID PRIMARY KEY REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
 payment_id TEXT NOT NULL UNIQUE,
 rider_identity_id UUID NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
)
CHECKSUM=hashlib.sha256("\n".join(STATEMENTS).encode()).hexdigest()

def _uuid(value:object,name:str)->str:
    try:return str(UUID(str(value)))
    except Exception as exc: raise ValueError(f"invalid_{name}") from exc

def init_schema(*,assume_yes:bool=False,dry_run:bool=False)->dict[str,Any]:
    if not assume_yes: raise RuntimeError("explicit_human_approval_required")
    if dry_run:return {"dry_run":True,"migration":MIGRATION,"checksum":CHECKSUM,"tables":len(TABLES)}
    with postgres_db.connect() as c:
        c.execute("SELECT pg_advisory_xact_lock(%s)",(25800024,))
        row=c.execute("SELECT checksum FROM oap_schema_migrations WHERE version=%s",(MIGRATION,)).fetchone()
        if row is not None and str(row[0])!=CHECKSUM: raise RuntimeError("ride_payment_bridge_migration_checksum_mismatch")
        if row is None:
            for stmt in STATEMENTS:c.execute(stmt)
            c.execute("INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",(MIGRATION,CHECKSUM))
        c.commit()
    return {"migration":MIGRATION,"schema_ready":True,"tables":len(TABLES)}

def bind(*,booking_id:object,rider_identity_id:object,payment_id:object)->dict[str,Any]:
    booking=_uuid(booking_id,"booking_id"); rider=_uuid(rider_identity_id,"rider_identity_id")
    payment=str(payment_id or "").strip()
    if not payment: raise ValueError("payment_id_required")
    intent=sika_payment_orchestrator.read_intent(payment)
    if intent is None: raise PermissionError("sika_payment_intent_not_found")
    with postgres_db.connect() as c:
        owner=c.execute("""SELECT 1 FROM oap_movement_bookings
          WHERE booking_id=%s AND member_identity_id=%s AND service_type='ride'""",(booking,rider)).fetchone()
        if owner is None: raise PermissionError("ride_owner_required")
        row=c.execute("""INSERT INTO oap_ride_payment_bindings(booking_id,payment_id,rider_identity_id)
          VALUES (%s,%s,%s)
          ON CONFLICT (booking_id) DO UPDATE SET payment_id=EXCLUDED.payment_id,
          rider_identity_id=EXCLUDED.rider_identity_id,updated_at=CURRENT_TIMESTAMP
          RETURNING booking_id,payment_id,updated_at""",(booking,payment,rider)).fetchone(); c.commit()
    return {"booking_id":str(row[0]),"payment_id":str(row[1]),"payment_status":intent.status,
            "updated_at":row[2].isoformat(),"money_moved":False}

def projection(*,booking_id:object)->dict[str,Any]:
    booking=_uuid(booking_id,"booking_id")
    with postgres_db.connect(readonly=True) as c:
        binding=c.execute("SELECT payment_id FROM oap_ride_payment_bindings WHERE booking_id=%s",(booking,)).fetchone()
        if binding is None:
            return {"bound":False,"payment_id":None,"payment_status":"NOT_BOUND","submission_evidence":None,
                    "settlement_proven":False,"money_moved_by_bridge":False}
        payment_id=str(binding[0])
        evidence=c.execute("""SELECT provider_id,provider_reference,outcome,evidence_hash,created_at
          FROM oap_sika_payment_submission_evidence
          WHERE payment_id=%s ORDER BY created_at DESC LIMIT 1""",(payment_id,)).fetchone()
    intent=sika_payment_orchestrator.read_intent(payment_id)
    if intent is None:
        return {"bound":True,"payment_id":payment_id,"payment_status":"MISSING",
                "submission_evidence":None,"settlement_proven":False,"money_moved_by_bridge":False}
    evidence_payload=None if evidence is None else {
        "provider_id":str(evidence[0]),"provider_reference":str(evidence[1]) if evidence[1] else None,
        "outcome":str(evidence[2]),"evidence_hash":str(evidence[3]),"created_at":evidence[4].isoformat(),
    }
    return {"bound":True,"payment_id":payment_id,"payment_status":intent.status,
            "amount_minor":int(intent.amount*100),"currency":intent.currency,
            "submission_evidence":evidence_payload,"settlement_proven":intent.status=="SETTLED",
            "money_moved_by_bridge":False}
