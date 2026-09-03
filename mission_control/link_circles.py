"""First-party OAP Link Circle membership and invite store.

Schema activation is explicit. Import/startup never mutates production.
Circle membership is certified before any Circle messaging/calling runtime is enabled.
"""
from __future__ import annotations

import uuid
from typing import Any

from . import link_relationships, linkup_safety, postgres_db

SCHEMA_VERSION = "link_circles_v1"
MAX_CIRCLE_MEMBERS = 32
MAX_CIRCLE_NAME = 80
SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS link_circles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        host_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name TEXT NOT NULL CHECK (char_length(name) BETWEEN 1 AND 80),
        status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','closed')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS link_circle_members (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        circle_id UUID NOT NULL REFERENCES link_circles(id) ON DELETE CASCADE,
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        role TEXT NOT NULL CHECK (role IN ('host','member')),
        status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','left')),
        joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        left_at TIMESTAMPTZ,
        CHECK ((status='active' AND left_at IS NULL) OR status='left')
    )""",
    """CREATE UNIQUE INDEX IF NOT EXISTS uq_link_circle_active_member
        ON link_circle_members(circle_id,user_id) WHERE status='active'""",
    "CREATE INDEX IF NOT EXISTS idx_link_circle_members_user ON link_circle_members(user_id,status,joined_at DESC)",
    """CREATE TABLE IF NOT EXISTS link_circle_invites (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        circle_id UUID NOT NULL REFERENCES link_circles(id) ON DELETE CASCADE,
        inviter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        invitee_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','accepted','declined','revoked')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMPTZ,
        CHECK (inviter_id <> invitee_id)
    )""",
    """CREATE UNIQUE INDEX IF NOT EXISTS uq_link_circle_pending_invite
        ON link_circle_invites(circle_id,invitee_id) WHERE status='pending'""",
    "CREATE INDEX IF NOT EXISTS idx_link_circle_invites_invitee ON link_circle_invites(invitee_id,status,created_at DESC)",
)


class LinkCirclesUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _name(value: object) -> str:
    name = " ".join(str(value or "").split())[:MAX_CIRCLE_NAME]
    if not name:
        raise ValueError("circle_name_required")
    return name


def _guard_link(first: str, second: str) -> None:
    if linkup_safety.blocked_between(first, second):
        raise ValueError("link_blocked")
    if not link_relationships.accepted_between(first, second):
        raise ValueError("accepted_link_required")


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
        raise LinkCirclesUnavailable("link_circles_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def status() -> dict[str, Any]:
    needed = {"link_circles", "link_circle_members", "link_circle_invites"}
    result: dict[str, Any] = {"configured": postgres_db.configured(), "ready": False, "first_party": True}
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name=ANY(%s)",
                (list(needed),),
            ).fetchall()
        result["ready"] = needed <= {str(row[0]) for row in rows}
    except Exception:  # noqa: BLE001 - coarse fail-closed readiness only.
        return result
    return result


def create_circle(host_id: object, name: object) -> str:
    host = _uuid(host_id, "invalid_host")
    circle_name = _name(name)
    try:
        with postgres_db.connect() as connection:
            active = connection.execute("SELECT 1 FROM users WHERE id=%s AND status='active'", (host,)).fetchone()
            if active is None:
                raise ValueError("host_unavailable")
            row = connection.execute(
                "INSERT INTO link_circles(host_id,name) VALUES (%s,%s) RETURNING id",
                (host, circle_name),
            ).fetchone()
            circle_id = str(row[0])
            connection.execute(
                "INSERT INTO link_circle_members(circle_id,user_id,role) VALUES (%s,%s,'host')",
                (circle_id, host),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkCirclesUnavailable("circle_create_failed") from exc
    return circle_id


def bring_in(host_id: object, circle_id: object, invitee_id: object) -> str:
    host = _uuid(host_id, "invalid_host")
    circle = _uuid(circle_id, "invalid_circle")
    invitee = _uuid(invitee_id, "invalid_invitee")
    if host == invitee:
        raise ValueError("cannot_bring_in_self")
    _guard_link(host, invitee)
    try:
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1 FROM link_circles c JOIN link_circle_members m ON m.circle_id=c.id
                   WHERE c.id=%s AND c.status='active' AND c.host_id=%s
                     AND m.user_id=%s AND m.role='host' AND m.status='active'""",
                (circle, host, host),
            ).fetchone()
            if owned is None:
                raise ValueError("circle_host_required")
            count = connection.execute(
                "SELECT COUNT(*) FROM link_circle_members WHERE circle_id=%s AND status='active'",
                (circle,),
            ).fetchone()
            if count and int(count[0]) >= MAX_CIRCLE_MEMBERS:
                raise ValueError("circle_full")
            member = connection.execute(
                "SELECT 1 FROM link_circle_members WHERE circle_id=%s AND user_id=%s AND status='active'",
                (circle, invitee),
            ).fetchone()
            if member:
                raise ValueError("already_in_circle")
            row = connection.execute(
                """INSERT INTO link_circle_invites(circle_id,inviter_id,invitee_id)
                   VALUES (%s,%s,%s) RETURNING id""",
                (circle, host, invitee),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkCirclesUnavailable("bring_in_failed") from exc
    return str(row[0])


def respond_invite(invitee_id: object, invite_id: object, decision: object) -> bool:
    invitee = _uuid(invitee_id, "invalid_invitee")
    invite = _uuid(invite_id, "invalid_invite")
    choice = str(decision or "").strip().casefold()
    if choice not in {"accepted", "declined"}:
        raise ValueError("invalid_circle_decision")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """SELECT i.circle_id,i.inviter_id,c.status
                   FROM link_circle_invites i JOIN link_circles c ON c.id=i.circle_id
                   WHERE i.id=%s AND i.invitee_id=%s AND i.status='pending'""",
                (invite, invitee),
            ).fetchone()
            if row is None:
                return False
            circle, inviter, circle_status = str(row[0]), str(row[1]), str(row[2])
            if circle_status != "active":
                raise ValueError("circle_closed")
            if choice == "accepted":
                _guard_link(inviter, invitee)
                count = connection.execute(
                    "SELECT COUNT(*) FROM link_circle_members WHERE circle_id=%s AND status='active'",
                    (circle,),
                ).fetchone()
                if count and int(count[0]) >= MAX_CIRCLE_MEMBERS:
                    raise ValueError("circle_full")
                existing = connection.execute(
                    "SELECT 1 FROM link_circle_members WHERE circle_id=%s AND user_id=%s AND status='active'",
                    (circle, invitee),
                ).fetchone()
                if existing is None:
                    connection.execute(
                        "INSERT INTO link_circle_members(circle_id,user_id,role) VALUES (%s,%s,'member')",
                        (circle, invitee),
                    )
            updated = connection.execute(
                """UPDATE link_circle_invites SET status=%s,resolved_at=CURRENT_TIMESTAMP
                   WHERE id=%s AND invitee_id=%s AND status='pending' RETURNING id""",
                (choice, invite, invitee),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise LinkCirclesUnavailable("circle_link_in_failed") from exc
    return updated is not None


def step_out(identity_id: object, circle_id: object) -> bool:
    identity = _uuid(identity_id, "invalid_identity")
    circle = _uuid(circle_id, "invalid_circle")
    try:
        with postgres_db.connect() as connection:
            membership = connection.execute(
                """SELECT id,role FROM link_circle_members
                   WHERE circle_id=%s AND user_id=%s AND status='active' FOR UPDATE""",
                (circle, identity),
            ).fetchone()
            if membership is None:
                return False
            membership_id, role = str(membership[0]), str(membership[1])
            if role == "host":
                successor = connection.execute(
                    """SELECT id,user_id FROM link_circle_members
                       WHERE circle_id=%s AND status='active' AND user_id<>%s
                       ORDER BY joined_at,id LIMIT 1 FOR UPDATE""",
                    (circle, identity),
                ).fetchone()
                if successor:
                    successor_member, successor_user = str(successor[0]), str(successor[1])
                    connection.execute("UPDATE link_circle_members SET role='host' WHERE id=%s", (successor_member,))
                    connection.execute(
                        "UPDATE link_circles SET host_id=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                        (successor_user, circle),
                    )
                else:
                    connection.execute(
                        "UPDATE link_circles SET status='closed',updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                        (circle,),
                    )
                    connection.execute(
                        """UPDATE link_circle_invites SET status='revoked',resolved_at=CURRENT_TIMESTAMP
                           WHERE circle_id=%s AND status='pending'""",
                        (circle,),
                    )
            connection.execute(
                """UPDATE link_circle_members SET status='left',left_at=CURRENT_TIMESTAMP
                   WHERE id=%s""",
                (membership_id,),
            )
            connection.commit()
    except Exception as exc:
        raise LinkCirclesUnavailable("circle_step_out_failed") from exc
    return True


def dashboard(identity_id: object) -> dict[str, Any]:
    identity = _uuid(identity_id, "invalid_identity")
    try:
        with postgres_db.connect(readonly=True) as connection:
            circle_rows = connection.execute(
                """SELECT c.id,c.name,c.host_id,m.role,c.created_at
                   FROM link_circle_members m JOIN link_circles c ON c.id=m.circle_id
                   WHERE m.user_id=%s AND m.status='active' AND c.status='active'
                   ORDER BY c.updated_at DESC LIMIT 50""",
                (identity,),
            ).fetchall()
            invite_rows = connection.execute(
                """SELECT i.id,i.circle_id,c.name,i.inviter_id,
                          COALESCE(u.display_name,u.username),i.created_at
                   FROM link_circle_invites i
                   JOIN link_circles c ON c.id=i.circle_id
                   JOIN users u ON u.id=i.inviter_id
                   WHERE i.invitee_id=%s AND i.status='pending' AND c.status='active'
                   ORDER BY i.created_at DESC LIMIT 50""",
                (identity,),
            ).fetchall()
            circles = []
            for row in circle_rows:
                members = connection.execute(
                    """SELECT m.user_id,m.role,COALESCE(u.display_name,u.username),m.joined_at
                       FROM link_circle_members m JOIN users u ON u.id=m.user_id
                       WHERE m.circle_id=%s AND m.status='active'
                       ORDER BY CASE WHEN m.role='host' THEN 0 ELSE 1 END,m.joined_at LIMIT %s""",
                    (row[0], MAX_CIRCLE_MEMBERS),
                ).fetchall()
                circles.append({
                    "circle_id": str(row[0]),
                    "name": str(row[1]),
                    "host_id": str(row[2]),
                    "my_role": str(row[3]),
                    "created_at": row[4].isoformat(),
                    "members": [
                        {"identity_id": str(member[0]), "role": str(member[1]), "display_name": str(member[2]), "joined_at": member[3].isoformat()}
                        for member in members
                    ],
                })
    except Exception as exc:
        raise LinkCirclesUnavailable("circle_dashboard_failed") from exc
    return {
        "circles": circles,
        "invites": [
            {"invite_id": str(row[0]), "circle_id": str(row[1]), "circle_name": str(row[2]), "inviter_id": str(row[3]), "inviter": str(row[4]), "created_at": row[5].isoformat()}
            for row in invite_rows
        ],
        "max_members": MAX_CIRCLE_MEMBERS,
    }
