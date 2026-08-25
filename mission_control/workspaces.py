"""Owner-scoped My World workspaces backed by Neon Postgres."""

from __future__ import annotations

import uuid

from . import postgres_db

WORKSPACES: tuple[dict[str, str], ...] = (
    {"id": "ecosystem", "name": "Ecosystem", "icon": "🌍", "purpose": "Products, systems and connections."},
    {"id": "signals", "name": "Signals", "icon": "📡", "purpose": "Saved announcements and local observations."},
    {"id": "hrm-memory", "name": "HRM & Memory", "icon": "🧠", "purpose": "Private lessons, reviews and continuity notes."},
    {"id": "governance", "name": "Governance", "icon": "🛡️", "purpose": "Policies, decisions and protected review notes."},
    {"id": "performance", "name": "Performance", "icon": "📈", "purpose": "Clarity, stability, pace and outcomes."},
    {"id": "news", "name": "News", "icon": "📰", "purpose": "Local stories and verified information leads."},
    {"id": "transport", "name": "Transport", "icon": "🚚", "purpose": "Movement, bookings and route notes."},
    {"id": "market", "name": "Market", "icon": "🛍️", "purpose": "Listings, merchants and commerce planning."},
    {"id": "maps", "name": "Maps", "icon": "🗺️", "purpose": "Saved places, routes and location intelligence."},
    {"id": "identity", "name": "Identity", "icon": "👤", "purpose": "Your postcode identity and profile work."},
    {"id": "tv", "name": "OAP TV", "icon": "📺", "purpose": "Media, culture and creator planning."},
    {"id": "sika", "name": "SIKA", "icon": "💎", "purpose": "Contribution and trust-value records; not money."},
)
WORKSPACE_BY_ID = {item["id"]: item for item in WORKSPACES}


class WorkspaceUnavailable(RuntimeError):
    """Raised when owner-scoped workspace persistence fails safely."""


def get(workspace_id: object) -> dict[str, str] | None:
    return WORKSPACE_BY_ID.get(str(workspace_id or "").strip().casefold())


def _identity(value: object) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_workspace_identity") from exc


def list_records(
    identity_id: object, workspace_id: object, *, limit: int = 50
) -> list[dict[str, str]]:
    identity = _identity(identity_id)
    workspace = get(workspace_id)
    if workspace is None:
        raise ValueError("invalid_workspace")
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT record_id,title,body,status,created_at,updated_at
                   FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id=%s
                     AND status <> 'archived'
                   ORDER BY updated_at DESC LIMIT %s""",
                (identity, workspace["id"], min(100, max(1, int(limit)))),
            ).fetchall()
    except Exception as exc:
        raise WorkspaceUnavailable("workspace_read_failed") from exc
    return [
        {
            "record_id": str(row[0]),
            "title": str(row[1]),
            "body": str(row[2]),
            "status": str(row[3]),
            "created_at": row[4].isoformat(),
            "updated_at": row[5].isoformat(),
        }
        for row in rows
    ]


def add_record(
    identity_id: object,
    workspace_id: object,
    *,
    title: object,
    body: object,
    status: object = "active",
) -> str:
    identity = _identity(identity_id)
    workspace = get(workspace_id)
    if workspace is None:
        raise ValueError("invalid_workspace")
    title_value = str(title or "").strip()[:160]
    body_value = str(body or "").strip()[:5000]
    status_value = str(status or "active").strip().casefold()
    if not title_value or not body_value:
        raise ValueError("workspace_title_and_body_required")
    if status_value not in {"draft", "active"}:
        raise ValueError("invalid_workspace_status")
    try:
        with postgres_db.connect() as connection:
            recent = connection.execute(
                """SELECT COUNT(*) FROM oap_workspace_records
                   WHERE identity_id=%s
                     AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 minute'""",
                (identity,),
            ).fetchone()
            if recent and int(recent[0]) >= 20:
                raise ValueError("workspace_rate_limit")
            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,%s,%s,%s,%s) RETURNING record_id""",
                (identity, workspace["id"], title_value, body_value, status_value),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise WorkspaceUnavailable("workspace_write_failed") from exc
    return str(row[0])


def status() -> dict[str, object]:
    result: dict[str, object] = {
        "workspaces": len(WORKSPACES),
        "schema_ready": False,
        "records": 0,
        "ready": False,
        "error": None,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            exists = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='oap_workspace_records'"""
            ).fetchone()
            result["schema_ready"] = exists is not None
            if exists:
                result["records"] = int(
                    connection.execute(
                        "SELECT COUNT(*) FROM oap_workspace_records"
                    ).fetchone()[0]
                )
    except Exception:  # noqa: BLE001
        result["error"] = "workspace_store_unavailable"
    result["ready"] = bool(result["schema_ready"] and result["workspaces"] == 12)
    return result

