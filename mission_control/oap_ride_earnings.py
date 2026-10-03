# ruff: noqa: I001
"""OAP Ride earnings projection.

Reads completed Ride receipts and reports gross ride value plus settlement truth.
It does not invent a driver/platform split or claim settlement.
"""
from __future__ import annotations
from typing import Any
from uuid import UUID
from . import postgres_db, oap_ride_commercial

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
        split = oap_ride_commercial.project_split(amount_minor=amount) if amount is not None else {"configured": False, "driver_earnings_minor": None, "platform_amount_minor": None, "settlement_performed": False}
        journeys.append({
            "booking_id":str(row[0]),
            "completed_at":row[1].isoformat(),
            "payment_state":str(row[2]),
            "gross_ride_value_minor":amount,
            "currency":currency,
            "driver_earnings_minor":split.get("driver_earnings_minor"),
            "platform_amount_minor":split.get("platform_amount_minor"),
            "split_rule_id":split.get("rule_id"),
            "settlement_state":"PROJECTED" if split.get("configured") else "UNCONFIGURED",
        })
    return {
        "journey_count":len(journeys),
        "gross_ride_value_by_currency_minor":totals,
        "driver_earnings_calculated":any(item["driver_earnings_minor"] is not None for item in journeys),
        "earnings_split_configured":any(item["split_rule_id"] is not None for item in journeys),
        "settlement_performed":False,
        "journeys":journeys,
    }
