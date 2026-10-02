"""OAP Ride earnings projection.

Reads completed Ride receipts and reports gross ride value plus settlement truth.
It does not invent a driver/platform split or claim settlement.
"""
from __future__ import annotations
from typing import Any
from uuid import UUID
from . import postgres_db

def _uuid(value:object,name:str)->str:
    try:return str(UUID(str(value)))
    except Exception as exc: raise ValueError(f"invalid_{name}") from exc

def driver_summary(*,driver_identity_id:object,limit:int=50)->dict[str,Any]:
    driver=_uuid(driver_identity_id,"driver_identity_id")
    bounded=min(max(int(limit),1),200)
    with postgres_db.connect(readonly=True) as c:
        rows=c.execute(
            """SELECT booking_id,completed_at,payment_state,amount_minor,currency
               FROM oap_ride_receipts
               WHERE driver_identity_id=%s
               ORDER BY completed_at DESC LIMIT %s""",
            (driver,bounded),
        ).fetchall()
    totals={}
    journeys=[]
    for row in rows:
        currency=str(row[4]) if row[4] else None
        amount=int(row[3]) if row[3] is not None else None
        if currency and amount is not None:
            totals[currency]=totals.get(currency,0)+amount
        journeys.append({
            "booking_id":str(row[0]),
            "completed_at":row[1].isoformat(),
            "payment_state":str(row[2]),
            "gross_ride_value_minor":amount,
            "currency":currency,
            "driver_earnings_minor":None,
            "settlement_state":"UNCONFIGURED",
        })
    return {
        "journey_count":len(journeys),
        "gross_ride_value_by_currency_minor":totals,
        "driver_earnings_calculated":False,
        "earnings_split_configured":False,
        "settlement_performed":False,
        "journeys":journeys,
    }
