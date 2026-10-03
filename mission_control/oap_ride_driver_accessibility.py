"""OAP Ride driver accessibility capabilities.

Stores driver/vehicle capability declarations and evaluates them against the
rider's booking-scoped accessibility preferences. No statutory certification
is inferred from these records.
"""
from __future__ import annotations
import hashlib
from typing import Any
from uuid import UUID
from . import postgres_db

MIGRATION="0005_oap_ride_driver_accessibility"
TABLES=frozenset({"oap_ride_driver_accessibility"})
STATEMENTS=(
"""CREATE TABLE IF NOT EXISTS oap_ride_driver_accessibility (
 driver_identity_id UUID PRIMARY KEY,
 wheelchair_capable BOOLEAN NOT NULL DEFAULT FALSE,
 step_free_capable BOOLEAN NOT NULL DEFAULT FALSE,
 assistance_capable BOOLEAN NOT NULL DEFAULT FALSE,
 extra_transfer_time_supported BOOLEAN NOT NULL DEFAULT TRUE,
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
    if dry_run:return {"dry_run":True,"migration":MIGRATION,"checksum":CHECKSUM,"tables":1}
    with postgres_db.connect() as c:
        c.execute("SELECT pg_advisory_xact_lock(%s)",(25800025,))
        row=c.execute("SELECT checksum FROM oap_schema_migrations WHERE version=%s",(MIGRATION,)).fetchone()
        if row is not None and str(row[0])!=CHECKSUM: raise RuntimeError("ride_driver_accessibility_migration_checksum_mismatch")
        if row is None:
            for stmt in STATEMENTS:c.execute(stmt)
            c.execute("INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",(MIGRATION,CHECKSUM))
        c.commit()
    return {"migration":MIGRATION,"schema_ready":True,"tables":1}

def set_capabilities(*,driver_identity_id:object,capabilities:object)->dict[str,Any]:
    driver=_uuid(driver_identity_id,"driver_identity_id")
    if not isinstance(capabilities,dict): raise TypeError("invalid_driver_accessibility_capabilities")
    allowed={"wheelchair_capable","step_free_capable","assistance_capable","extra_transfer_time_supported","notes"}
    if not set(capabilities)<=allowed: raise ValueError("unsupported_driver_accessibility_fields")
    values={k:bool(capabilities.get(k,False)) for k in ("wheelchair_capable","step_free_capable","assistance_capable")}
    extra=bool(capabilities.get("extra_transfer_time_supported",True))
    notes=" ".join(str(capabilities.get("notes","")).strip().split())[:500]
    with postgres_db.connect() as c:
        row=c.execute("""SELECT 1 FROM oap_identity_roles
          WHERE identity_id=%s AND role_id='MOVEMENT_DRIVER' LIMIT 1""",(driver,)).fetchone()
        if row is None: raise PermissionError("certified_movement_driver_required")
        c.execute("""INSERT INTO oap_ride_driver_accessibility
          (driver_identity_id,wheelchair_capable,step_free_capable,assistance_capable,extra_transfer_time_supported,notes)
          VALUES (%s,%s,%s,%s,%s,%s)
          ON CONFLICT (driver_identity_id) DO UPDATE SET
          wheelchair_capable=EXCLUDED.wheelchair_capable,
          step_free_capable=EXCLUDED.step_free_capable,
          assistance_capable=EXCLUDED.assistance_capable,
          extra_transfer_time_supported=EXCLUDED.extra_transfer_time_supported,
          notes=EXCLUDED.notes,updated_at=CURRENT_TIMESTAMP""",
          (driver,values["wheelchair_capable"],values["step_free_capable"],values["assistance_capable"],extra,notes)); c.commit()
    return {"driver_identity_id":driver,**values,"extra_transfer_time_supported":extra,"notes":notes,"statutory_certification_inferred":False}

def eligible(*,booking_id:object,driver_identity_id:object)->dict[str,Any]:
    booking=_uuid(booking_id,"booking_id"); driver=_uuid(driver_identity_id,"driver_identity_id")
    with postgres_db.connect(readonly=True) as c:
        pref=c.execute("""SELECT wheelchair,step_free,reduced_walking,assistance_required,extra_transfer_minutes
          FROM oap_ride_accessibility WHERE booking_id=%s""",(booking,)).fetchone()
        cap=c.execute("""SELECT wheelchair_capable,step_free_capable,assistance_capable,extra_transfer_time_supported
          FROM oap_ride_driver_accessibility WHERE driver_identity_id=%s""",(driver,)).fetchone()
    if pref is None:
        return {"eligible":True,"reason":"no_accessibility_preferences","requirements_present":False}
    if cap is None:
        required=bool(pref[0] or pref[1] or pref[3] or int(pref[4] or 0)>0)
        return {"eligible":not required,"reason":"capability_record_missing" if required else "no_special_capability_required","requirements_present":required}
    failures=[]
    if pref[0] and not cap[0]: failures.append("wheelchair")
    if pref[1] and not cap[1]: failures.append("step_free")
    if pref[3] and not cap[2]: failures.append("assistance")
    if int(pref[4] or 0)>0 and not cap[3]: failures.append("extra_transfer_time")
    return {"eligible":not failures,"reason":"eligible" if not failures else "missing_capability","missing":failures,"requirements_present":True}
