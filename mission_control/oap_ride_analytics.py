# ruff: noqa: I001
"""OAP Ride participant analytics.

Read-only private summaries over Ride bookings, receipts and feedback.
"""
from __future__ import annotations
from typing import Any
from uuid import UUID
from . import postgres_db

def _uuid(v,n):
    try:return str(UUID(str(v)))
    except Exception as exc: raise ValueError(f"invalid_{n}") from exc

def summary(*,identity_id:object)->dict[str,Any]:
    identity=_uuid(identity_id,"identity_id")
    with postgres_db.connect(readonly=True) as c:
        rider=c.execute("""SELECT
          COUNT(*) FILTER (WHERE service_type='ride'),
          COUNT(*) FILTER (WHERE service_type='ride' AND state='COMPLETED'),
          COUNT(*) FILTER (WHERE service_type='ride' AND state='CANCELLED')
          FROM oap_movement_bookings WHERE member_identity_id=%s""",(identity,)).fetchone()
        driver=c.execute("""SELECT
          COUNT(DISTINCT b.booking_id) FILTER (WHERE b.service_type='ride'),
          COUNT(DISTINCT b.booking_id) FILTER (WHERE b.service_type='ride' AND b.state='COMPLETED')
          FROM oap_movement_match_proposals p
          JOIN oap_movement_bookings b ON b.booking_id=p.booking_id
          WHERE p.worker_identity_id=%s AND p.state='ACCEPTED'""",(identity,)).fetchone()
        feedback=c.execute("""SELECT COUNT(*),AVG(rating)::float
          FROM oap_ride_feedback WHERE author_identity_id=%s""",(identity,)).fetchone()
        received=c.execute("""SELECT COUNT(*),AVG(f.rating)::float FROM oap_ride_feedback f
          JOIN oap_movement_bookings b ON b.booking_id=f.booking_id
          LEFT JOIN oap_movement_match_proposals p ON p.booking_id=b.booking_id AND p.state='ACCEPTED'
          WHERE (b.member_identity_id=%s OR p.worker_identity_id=%s) AND f.author_identity_id<>%s""",
          (identity,identity,identity)).fetchone()
    return {
      "rider":{"journeys":int(rider[0] or 0),"completed":int(rider[1] or 0),"cancelled":int(rider[2] or 0)},
      "driver":{"journeys":int(driver[0] or 0),"completed":int(driver[1] or 0)},
      "feedback_given":{"count":int(feedback[0] or 0),"average":None if feedback[1] is None else round(float(feedback[1]),2)},
      "feedback_received":{"count":int(received[0] or 0),"average":None if received[1] is None else round(float(received[1]),2)},
      "private_projection":True,
      "other_user_directory_exposed":False,
    }
