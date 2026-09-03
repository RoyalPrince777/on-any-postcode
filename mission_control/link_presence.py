"""First-party OAP Link presence and Live Spot store.

Schema activation is explicit. Around Now and Live Spot are private-by-default,
short-lived and scoped to an accepted, unblocked Link.
"""
from __future__ import annotations

import uuid
from typing import Any

from . import link_relationships, linkup_safety, postgres_db

SCHEMA_VERSION = "link_presence_v1"
PRESENCE_TTL_SECONDS = 120
MIN_LIVE_SPOT_MINUTES = 1
MAX_LIVE_SPOT_MINUTES = 60

SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS link_presence_state (
        identity_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        around_now BOOLEAN NOT NULL DEFAULT FALSE,
        expires_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS link_presence_visibility (
        owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        viewer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        around_now BOOLEAN NOT NULL DEFAULT FALSE,
        live_spot BOOLEAN NOT NULL DEFAULT FALSE,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (owner_id, viewer_id),
        CHECK (owner_id <> viewer_id))""",
    """CREATE TABLE IF NOT EXISTS link_live_spot (
        owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        viewer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
        longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
        accuracy_m DOUBLE PRECISION CHECK (accuracy_m IS NULL OR (accuracy_m >= 0 AND accuracy_m <= 100000)),
        expires_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (owner_id, viewer_id),
        CHECK (owner_id <> viewer_id))""",
    "CREATE INDEX IF NOT EXISTS idx_link_presence_expiry ON link_presence_state(expires_at)",
    "CREATE INDEX IF NOT EXISTS idx_link_live_spot_expiry ON link_live_spot(expires_at)",
    "CREATE INDEX IF NOT EXISTS idx_link_live_spot_viewer ON link_live_spot(viewer_id,expires_at)",
)


class LinkPresenceUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _peer_guard(owner_id: object, viewer_id: object) -> tuple[str, str]:
    owner = _uuid(owner_id, "invalid_owner")
    viewer = _uuid(viewer_id, "invalid_viewer")
    if owner == viewer:
        raise ValueError("cannot_share_with_self")
    try:
        if linkup_safety.blocked_between(owner, viewer):
            raise ValueError("link_blocked")
        if not link_relationships.accepted_between(owner, viewer):
            raise ValueError("accepted_link_required")
    except ValueError:
        raise
    except (linkup_safety.LinkUpSafetyUnavailable, link_relationships.LinkRelationshipsUnavailable) as exc:
        raise LinkPresenceUnavailable("link_guard_unavailable") from exc
    return owner, viewer


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes and not dry_run:
        raise PermissionError("explicit_confirmation_required")
    if dry_run:
        return {"version": SCHEMA_VERSION, "statements": list(SCHEMA_SQL), "applied": False}
    try:
        with postgres_db.connect() as connection:
            for statement in SCHEMA_SQL:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise LinkPresenceUnavailable("link_presence_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def status() -> dict[str, Any]:
    result: dict[str, Any] = {
        "configured": postgres_db.configured(),
        "schema_ready": False,
        "ready": False,
        "around_now_ttl_seconds": PRESENCE_TTL_SECONDS,
        "live_spot_max_minutes": MAX_LIVE_SPOT_MINUTES,
        "private_by_default": True,
        "first_party": True,
    }
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema='public' AND table_name IN
                   ('link_presence_state','link_presence_visibility','link_live_spot')"""
            ).fetchall()
        tables = sorted(str(row[0]) for row in rows)
        result["schema_ready"] = tables == [
            "link_live_spot",
            "link_presence_state",
            "link_presence_visibility",
        ]
    except Exception:
        return result
    result["ready"] = bool(result["schema_ready"])
    return result


def set_visibility(
    owner_id: object,
    viewer_id: object,
    *,
    around_now: object = False,
    live_spot: object = False,
) -> dict[str, bool]:
    owner, viewer = _peer_guard(owner_id, viewer_id)
    if not isinstance(around_now, bool) or not isinstance(live_spot, bool):
        raise ValueError("invalid_visibility")
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO link_presence_visibility(owner_id,viewer_id,around_now,live_spot)
                   VALUES (%s,%s,%s,%s)
                   ON CONFLICT (owner_id,viewer_id) DO UPDATE SET
                     around_now=EXCLUDED.around_now,
                     live_spot=EXCLUDED.live_spot,
                     updated_at=CURRENT_TIMESTAMP""",
                (owner, viewer, around_now, live_spot),
            )
            if not live_spot:
                connection.execute(
                    "DELETE FROM link_live_spot WHERE owner_id=%s AND viewer_id=%s",
                    (owner, viewer),
                )
            connection.commit()
    except Exception as exc:
        raise LinkPresenceUnavailable("presence_visibility_update_failed") from exc
    return {"around_now": around_now, "live_spot": live_spot}


def heartbeat(identity_id: object, *, around_now: object) -> dict[str, object]:
    identity = _uuid(identity_id, "invalid_identity")
    if not isinstance(around_now, bool):
        raise ValueError("invalid_around_now")
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO link_presence_state(identity_id,around_now,expires_at)
                   VALUES (%s,%s,CURRENT_TIMESTAMP + (%s * INTERVAL '1 second'))
                   ON CONFLICT (identity_id) DO UPDATE SET
                     around_now=EXCLUDED.around_now,
                     expires_at=EXCLUDED.expires_at,
                     updated_at=CURRENT_TIMESTAMP""",
                (identity, around_now, PRESENCE_TTL_SECONDS),
            )
            connection.commit()
    except Exception as exc:
        raise LinkPresenceUnavailable("presence_heartbeat_failed") from exc
    return {"around_now": around_now, "ttl_seconds": PRESENCE_TTL_SECONDS}


def around_now(viewer_id: object, owner_id: object) -> bool:
    owner, viewer = _peer_guard(owner_id, viewer_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1
                   FROM link_presence_state s
                   JOIN link_presence_visibility v ON v.owner_id=s.identity_id
                   WHERE s.identity_id=%s AND v.viewer_id=%s
                     AND v.around_now=TRUE
                     AND s.around_now=TRUE
                     AND s.expires_at>CURRENT_TIMESTAMP
                   LIMIT 1""",
                (owner, viewer),
            ).fetchone()
    except Exception as exc:
        raise LinkPresenceUnavailable("presence_read_failed") from exc
    return row is not None


def start_live_spot(
    owner_id: object,
    viewer_id: object,
    *,
    latitude: object,
    longitude: object,
    accuracy_m: object = None,
    duration_minutes: object = 15,
) -> dict[str, object]:
    owner, viewer = _peer_guard(owner_id, viewer_id)
    try:
        lat = float(latitude)
        lon = float(longitude)
        accuracy = None if accuracy_m is None else float(accuracy_m)
        duration = int(duration_minutes)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_live_spot") from exc
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("invalid_live_spot_coordinates")
    if accuracy is not None and not 0 <= accuracy <= 100000:
        raise ValueError("invalid_live_spot_accuracy")
    if not MIN_LIVE_SPOT_MINUTES <= duration <= MAX_LIVE_SPOT_MINUTES:
        raise ValueError("invalid_live_spot_duration")
    try:
        with postgres_db.connect() as connection:
            allowed = connection.execute(
                """SELECT 1 FROM link_presence_visibility
                   WHERE owner_id=%s AND viewer_id=%s AND live_spot=TRUE LIMIT 1""",
                (owner, viewer),
            ).fetchone()
            if allowed is None:
                raise ValueError("live_spot_visibility_required")
            connection.execute(
                """INSERT INTO link_live_spot(owner_id,viewer_id,latitude,longitude,accuracy_m,expires_at)
                   VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP + (%s * INTERVAL '1 minute'))
                   ON CONFLICT (owner_id,viewer_id) DO UPDATE SET
                     latitude=EXCLUDED.latitude,
                     longitude=EXCLUDED.longitude,
                     accuracy_m=EXCLUDED.accuracy_m,
                     expires_at=EXCLUDED.expires_at,
                     updated_at=CURRENT_TIMESTAMP""",
                (owner, viewer, lat, lon, accuracy, duration),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkPresenceUnavailable("live_spot_start_failed") from exc
    return {"active": True, "duration_minutes": duration}


def read_live_spot(viewer_id: object, owner_id: object) -> dict[str, object] | None:
    owner, viewer = _peer_guard(owner_id, viewer_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT s.latitude,s.longitude,s.accuracy_m,s.expires_at,s.updated_at
                   FROM link_live_spot s
                   JOIN link_presence_visibility v
                     ON v.owner_id=s.owner_id AND v.viewer_id=s.viewer_id
                   WHERE s.owner_id=%s AND s.viewer_id=%s
                     AND v.live_spot=TRUE
                     AND s.expires_at>CURRENT_TIMESTAMP
                   LIMIT 1""",
                (owner, viewer),
            ).fetchone()
    except Exception as exc:
        raise LinkPresenceUnavailable("live_spot_read_failed") from exc
    if row is None:
        return None
    return {
        "latitude": float(row[0]),
        "longitude": float(row[1]),
        "accuracy_m": None if row[2] is None else float(row[2]),
        "expires_at": row[3].isoformat(),
        "updated_at": row[4].isoformat(),
    }


def stop_live_spot(owner_id: object, viewer_id: object) -> bool:
    owner = _uuid(owner_id, "invalid_owner")
    viewer = _uuid(viewer_id, "invalid_viewer")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                "DELETE FROM link_live_spot WHERE owner_id=%s AND viewer_id=%s RETURNING owner_id",
                (owner, viewer),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise LinkPresenceUnavailable("live_spot_stop_failed") from exc
    return row is not None


def purge_expired() -> int:
    try:
        with postgres_db.connect() as connection:
            presence = connection.execute(
                "DELETE FROM link_presence_state WHERE expires_at<=CURRENT_TIMESTAMP"
            ).rowcount
            spots = connection.execute(
                "DELETE FROM link_live_spot WHERE expires_at<=CURRENT_TIMESTAMP"
            ).rowcount
            connection.commit()
    except Exception as exc:
        raise LinkPresenceUnavailable("presence_purge_failed") from exc
    return int(presence or 0) + int(spots or 0)
