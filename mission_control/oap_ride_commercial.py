"""OAP Ride commercial rules and accessibility preferences.

Extends Ride without duplicating the SIKA payment orchestrator. Stores explicit
driver/platform split rules and rider accessibility preferences. Settlement
records are projections only; money movement remains owned elsewhere.
"""
from __future__ import annotations
import hashlib
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID
from . import postgres_db

MIGRATION="0003_oap_ride_commercial_accessibility"
TABLES=frozenset({"oap_ride_split_rules","oap_ride_accessibility"})
STATEMENTS=(
"""CREATE TABLE IF NOT EXISTS oap_ride_split_rules (
 rule_id TEXT PRIMARY KEY,
 driver_basis_points INTEGER NOT NULL CHECK (driver_basis_points BETWEEN 0 AND 10000),
 platform_basis_points INTEGER NOT NULL CHECK (platform_basis_points BETWEEN 0 AND 10000),
 state TEXT NOT NULL CHECK (state IN ('DRAFT','ACTIVE','RETIRED')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CHECK (driver_basis_points + platform_basis_points = 10000))""",
"""CREATE TABLE IF NOT EXISTS oap_ride_accessibility (
 booking_id UUID PRIMARY KEY REFERENCES oap_movement_bookings(booking_id) ON DELETE CASCADE,
 rider_identity_id UUID NOT NULL,
 wheelchair BOOLEAN NOT NULL DEFAULT FALSE,
 step_free BOOLEAN NOT NULL DEFAULT FALSE,
 reduced_walking BOOLEAN NOT NULL DEFAULT FALSE,
 assistance_required BOOLEAN NOT NULL DEFAULT FALSE,
 extra_transfer_minutes INTEGER NOT NULL DEFAULT 0 CHECK (extra_transfer_minutes BETWEEN 0 AND 180),
 notes TEXT NOT NULL DEFAULT '',
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
        c.execute("SELECT pg_advisory_xact_lock(%s)",(25800023,))
        row=c.execute("SELECT checksum FROM oap_schema_migrations WHERE version=%s",(MIGRATION,)).fetchone()
        if row is not None and str(row[0])!=CHECKSUM: raise RuntimeError("ride_commercial_migration_checksum_mismatch")
        if row is None:
            for stmt in STATEMENTS:c.execute(stmt)
            c.execute("INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",(MIGRATION,CHECKSUM))
        c.commit()
    return {"migration":MIGRATION,"schema_ready":True,"tables":len(TABLES)}

def set_split_rule(*,rule_id:object,driver_percent:object,state:object="DRAFT")->dict[str,Any]:
    ident=str(rule_id or "").strip()
    if not ident or len(ident)>80: raise ValueError("invalid_split_rule_id")
    try: percent=Decimal(str(driver_percent))
    except (InvalidOperation,TypeError,ValueError) as exc: raise ValueError("invalid_driver_percent") from exc
    if percent<0 or percent>100: raise ValueError("invalid_driver_percent")
    driver_bps=int((percent*100).quantize(Decimal("1")))
    platform_bps=10000-driver_bps
    target=str(state or "").strip().upper()
    if target not in {"DRAFT","ACTIVE","RETIRED"}: raise ValueError("invalid_split_rule_state")
    with postgres_db.connect() as c:
        if target=="ACTIVE":
            c.execute("UPDATE oap_ride_split_rules SET state='RETIRED',updated_at=CURRENT_TIMESTAMP WHERE state='ACTIVE'")
        row=c.execute("""INSERT INTO oap_ride_split_rules(rule_id,driver_basis_points,platform_basis_points,state)
        VALUES (%s,%s,%s,%s) ON CONFLICT (rule_id) DO UPDATE SET
        driver_basis_points=EXCLUDED.driver_basis_points,platform_basis_points=EXCLUDED.platform_basis_points,
        state=EXCLUDED.state,updated_at=CURRENT_TIMESTAMP
        RETURNING rule_id,driver_basis_points,platform_basis_points,state,updated_at""",
        (ident,driver_bps,platform_bps,target)).fetchone(); c.commit()
    return {"rule_id":str(row[0]),"driver_percent":int(row[1])/100,"platform_percent":int(row[2])/100,"state":str(row[3]),"updated_at":row[4].isoformat(),"money_moved":False}

def active_split()->dict[str,Any]|None:
    with postgres_db.connect(readonly=True) as c:
        row=c.execute("""SELECT rule_id,driver_basis_points,platform_basis_points
        FROM oap_ride_split_rules WHERE state='ACTIVE' ORDER BY updated_at DESC LIMIT 1""").fetchone()
    if row is None:return None
    return {"rule_id":str(row[0]),"driver_basis_points":int(row[1]),"platform_basis_points":int(row[2])}

def project_split(*,amount_minor:object)->dict[str,Any]:
    try: amount=int(amount_minor)
    except (TypeError,ValueError) as exc: raise ValueError("invalid_amount_minor") from exc
    if amount<0: raise ValueError("invalid_amount_minor")
    rule=active_split()
    if rule is None:return {"configured":False,"driver_earnings_minor":None,"platform_amount_minor":None,"settlement_performed":False}
    driver=(amount*rule["driver_basis_points"])//10000
    platform=amount-driver
    return {"configured":True,"rule_id":rule["rule_id"],"driver_earnings_minor":driver,"platform_amount_minor":platform,"settlement_performed":False}

def set_accessibility(*,booking_id:object,rider_identity_id:object,preferences:object)->dict[str,Any]:
    booking=_uuid(booking_id,"booking_id"); rider=_uuid(rider_identity_id,"rider_identity_id")
    if not isinstance(preferences,dict): raise TypeError("invalid_accessibility_preferences")
    allowed={"wheelchair","step_free","reduced_walking","assistance_required","extra_transfer_minutes","notes"}
    if not set(preferences)<=allowed: raise ValueError("unsupported_accessibility_fields")
    flags={k:bool(preferences.get(k,False)) for k in ("wheelchair","step_free","reduced_walking","assistance_required")}
    try: extra=int(preferences.get("extra_transfer_minutes",0))
    except (TypeError,ValueError) as exc: raise ValueError("invalid_extra_transfer_minutes") from exc
    if not 0<=extra<=180: raise ValueError("invalid_extra_transfer_minutes")
    notes=" ".join(str(preferences.get("notes","")).strip().split())[:500]
    with postgres_db.connect() as c:
        owner=c.execute("SELECT 1 FROM oap_movement_bookings WHERE booking_id=%s AND member_identity_id=%s",(booking,rider)).fetchone()
        if owner is None: raise PermissionError("ride_owner_required")
        c.execute("""INSERT INTO oap_ride_accessibility
        (booking_id,rider_identity_id,wheelchair,step_free,reduced_walking,assistance_required,extra_transfer_minutes,notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (booking_id) DO UPDATE SET wheelchair=EXCLUDED.wheelchair,step_free=EXCLUDED.step_free,
        reduced_walking=EXCLUDED.reduced_walking,assistance_required=EXCLUDED.assistance_required,
        extra_transfer_minutes=EXCLUDED.extra_transfer_minutes,notes=EXCLUDED.notes,updated_at=CURRENT_TIMESTAMP""",
        (booking,rider,flags["wheelchair"],flags["step_free"],flags["reduced_walking"],flags["assistance_required"],extra,notes)); c.commit()
    return {"booking_id":booking,**flags,"extra_transfer_minutes":extra,"notes":notes}
