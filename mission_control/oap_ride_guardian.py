# ruff: noqa: I001, BLE001
"""OAP Ride Guardian: participant-scoped digital safety records.

No covert tracking, emergency-service impersonation, or automatic physical response.
"""
from __future__ import annotations
import hashlib
from itertools import pairwise
from typing import Any
from uuid import UUID
from . import oap_ride_guardian_outbox, oap_ride_private_geometry, postgres_db

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
    outbox = None
    try:
        outbox = oap_ride_guardian_outbox.enqueue(
            booking_id=booking,
            event_type="SAFETY_CONCERN" if k in {"SAFETY_CONCERN","OTHER"} else k,
            payload={"kind": k, "incident_id": str(row[0])},
        )
    except Exception:
        outbox = None
    return {"incident_id":str(row[0]),"booking_id":booking,"kind":k,"created_at":row[1].isoformat(),
            "trusted_contact_notification":outbox,
            "automatic_emergency_dispatch":False}


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt
    earth_m = 6371000.0
    p1, p2 = radians(lat1), radians(lat2)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(p1) * cos(p2) * sin(dlon / 2) ** 2
    return 2 * earth_m * asin(sqrt(a))


def analyse_tracking(
    *,
    booking_id: object,
    identity_id: object,
    stop_minutes: object = 8,
    stop_radius_m: object = 40,
) -> dict[str, Any]:
    booking = _uuid(booking_id, "booking_id")
    identity = _uuid(identity_id, "identity_id")
    try:
        stop_window = int(stop_minutes)
        radius = float(stop_radius_m)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_guardian_threshold") from exc
    if not 2 <= stop_window <= 60 or not 5 <= radius <= 500:
        raise ValueError("invalid_guardian_threshold")
    with postgres_db.connect(readonly=True) as c:
        if not _participant(c, booking, identity):
            raise PermissionError("booking_participant_required")
        booking_row = c.execute(
            "SELECT state,route_snapshot FROM oap_movement_bookings WHERE booking_id=%s",
            (booking,),
        ).fetchone()
        points = c.execute(
            """SELECT latitude,longitude,recorded_at,identity_id
               FROM oap_movement_tracking_points
               WHERE booking_id=%s AND expires_at>CURRENT_TIMESTAMP
               ORDER BY recorded_at DESC LIMIT 6""",
            (booking,),
        ).fetchall()
    if booking_row is None:
        raise PermissionError("booking_not_found")
    state = str(booking_row[0])
    route_snapshot = booking_row[1] if isinstance(booking_row[1], dict) else {}
    if state != "IN_PROGRESS":
        return {
            "booking_id": booking,
            "journey_state": state,
            "unexpected_stop": False,
            "tracking_analysis": "INACTIVE_JOURNEY",
            "route_deviation_analysis": "NOT_RUN",
            "automatic_emergency_dispatch": False,
        }
    if len(points) < 2:
        return {
            "booking_id": booking,
            "journey_state": state,
            "unexpected_stop": False,
            "tracking_analysis": "INSUFFICIENT_CONSENTED_POINTS",
            "route_deviation_analysis": "UNAVAILABLE_NO_ROUTE_GEOMETRY",
            "automatic_emergency_dispatch": False,
        }
    latest = points[0]
    earlier = None
    for point in points[1:]:
        delta_min = (latest[2] - point[2]).total_seconds() / 60
        if delta_min >= stop_window:
            earlier = point
            break
    unexpected = False
    distance = None
    elapsed = None
    if earlier is not None:
        elapsed = (latest[2] - earlier[2]).total_seconds() / 60
        distance = _distance_m(
            float(earlier[0]), float(earlier[1]),
            float(latest[0]), float(latest[1]),
        )
        unexpected = distance <= radius
    geometry_present = bool(route_snapshot.get("geometry") or route_snapshot.get("geometry_polyline"))
    return {
        "booking_id": booking,
        "journey_state": state,
        "unexpected_stop": unexpected,
        "elapsed_minutes": round(elapsed, 2) if elapsed is not None else None,
        "movement_distance_m": round(distance, 1) if distance is not None else None,
        "tracking_analysis": "CONSENTED_PRIVATE_POINTS_ONLY",
        "route_deviation_analysis": "READY_FOR_GEOMETRY_CHECK" if geometry_present else "UNAVAILABLE_NO_ROUTE_GEOMETRY",
        "covert_tracking": False,
        "automatic_emergency_dispatch": False,
    }


def _distance_to_route_vertices_m(latitude: float, longitude: float, geometry: dict[str, Any]) -> float | None:
    """Return point-to-LineString distance using nearest route segment, not vertex."""
    from math import cos, radians

    if geometry.get("type") != "LineString":
        return None
    raw = geometry.get("coordinates")
    if not isinstance(raw, list) or not raw:
        return None
    points = []
    for point in raw[:5000]:
        if not isinstance(point, list) or len(point) < 2:
            continue
        try:
            points.append((float(point[1]), float(point[0])))
        except (TypeError, ValueError):
            continue
    if not points:
        return None
    if len(points) == 1:
        return _distance_m(latitude, longitude, points[0][0], points[0][1])

    earth_m = 6371000.0
    lat0 = radians(latitude)
    cos_lat = max(abs(cos(lat0)), 1e-12)

    def xy(lat: float, lon: float) -> tuple[float, float]:
        return (
            earth_m * radians(lon - longitude) * cos_lat,
            earth_m * radians(lat - latitude),
        )

    best = None
    for start, end in pairwise(points):
        ax, ay = xy(start[0], start[1])
        bx, by = xy(end[0], end[1])
        vx, vy = bx - ax, by - ay
        denom = vx * vx + vy * vy
        if denom == 0:
            distance = (ax * ax + ay * ay) ** 0.5
        else:
            t = max(0.0, min(1.0, -(ax * vx + ay * vy) / denom))
            px, py = ax + t * vx, ay + t * vy
            distance = (px * px + py * py) ** 0.5
        best = distance if best is None else min(best, distance)
    return best


def analyse_route_deviation(
    *,
    booking_id: object,
    identity_id: object,
    deviation_threshold_m: object = 250,
) -> dict[str, Any]:
    booking = _uuid(booking_id, "booking_id")
    identity = _uuid(identity_id, "identity_id")
    try:
        threshold = float(deviation_threshold_m)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_deviation_threshold") from exc
    if not 25 <= threshold <= 5000:
        raise ValueError("invalid_deviation_threshold")
    with postgres_db.connect(readonly=True) as c:
        if not _participant(c, booking, identity):
            raise PermissionError("booking_participant_required")
        latest = c.execute(
            """SELECT latitude,longitude,recorded_at FROM oap_movement_tracking_points
               WHERE booking_id=%s AND expires_at>CURRENT_TIMESTAMP
               ORDER BY recorded_at DESC LIMIT 1""",
            (booking,),
        ).fetchone()
    if latest is None:
        return {
            "booking_id": booking,
            "route_deviation": False,
            "analysis": "INSUFFICIENT_CONSENTED_POINTS",
            "automatic_emergency_dispatch": False,
        }
    private = oap_ride_private_geometry.read_private(
        booking_id=booking, identity_id=identity
    )
    distance = _distance_to_route_vertices_m(
        float(latest[0]), float(latest[1]), private["geometry"]
    )
    if distance is None:
        return {
            "booking_id": booking,
            "route_deviation": False,
            "analysis": "INVALID_PRIVATE_ROUTE_GEOMETRY",
            "automatic_emergency_dispatch": False,
        }
    return {
        "booking_id": booking,
        "route_deviation": distance > threshold,
        "distance_to_route_m": round(distance, 1),
        "threshold_m": threshold,
        "analysis": "CONSENTED_POINT_VS_PRIVATE_OAP_ROUTE",
        "geometry_sha256": private["geometry_sha256"],
        "covert_tracking": False,
        "automatic_emergency_dispatch": False,
    }
