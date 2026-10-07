"""Governed Koradaso Royal House invitation runtime.

Access invitations are not statements of genealogy or Royal status.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from . import postgres_db

ISSUE_PERMISSION = "KORADASO_ISSUE_INVITE"
DEFAULT_TTL_HOURS = 72


class KoradasoInviteDenied(PermissionError):
    pass


def _uuid(value: object, field: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{field}") from exc


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _has_permission(connection, identity_id: UUID, permission: str) -> bool:
    row = connection.execute(
        """SELECT 1
           FROM oap_identity_roles ir
           JOIN oap_role_permissions rp ON rp.role_id = ir.role_id
           JOIN oap_identities i ON i.identity_id = ir.identity_id
           WHERE ir.identity_id = %s AND rp.permission_id = %s
             AND i.status = 'ACTIVE'
           LIMIT 1""",
        (identity_id, permission),
    ).fetchone()
    return bool(row)


def _audit(connection, *, actor: UUID, action: str, target: str, reason: str,
           metadata: dict[str, object] | None = None) -> None:
    previous = connection.execute(
        "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1 FOR UPDATE"
    ).fetchone()
    prev_hash = str(previous[0]) if previous else ""
    event_id = uuid4()
    correlation_id = uuid4()
    timestamp = datetime.now(timezone.utc)
    safe_metadata = metadata or {}
    payload = "|".join((
        prev_hash, str(event_id), str(actor), action, target, reason,
        str(correlation_id), timestamp.isoformat(), repr(sorted(safe_metadata.items())),
    ))
    curr_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    connection.execute(
        """INSERT INTO audit_events
           (event_id,prev_hash,curr_hash,actor_id,actor_type,authority_level,
            action,target,reason,correlation_id,metadata,timestamp)
           VALUES (%s,%s,%s,%s,'HUMAN',0,%s,%s,%s,%s,%s::jsonb,%s)""",
        (event_id, prev_hash, curr_hash, str(actor), action, target, reason,
         correlation_id, __import__("json").dumps(safe_metadata), timestamp),
    )


def issue_invite(*, invited_by: object, ttl_hours: int = DEFAULT_TTL_HOURS) -> dict[str, object]:
    issuer = _uuid(invited_by, "invited_by")
    if ttl_hours < 1 or ttl_hours > 168:
        raise ValueError("invalid_invite_ttl")
    token = secrets.token_urlsafe(32)
    digest = _token_hash(token)
    invite_id = uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    with postgres_db.connect() as connection:
        if not _has_permission(connection, issuer, ISSUE_PERMISSION):
            raise KoradasoInviteDenied("koradaso_invite_permission_required")
        connection.execute(
            """INSERT INTO koradaso_invites
               (invite_id,invited_by,token_hash,expires_at)
               VALUES (%s,%s,%s,%s)""",
            (invite_id, issuer, digest, expires_at),
        )
        _audit(connection, actor=issuer, action="KORADASO_INVITE_ISSUED",
               target=str(invite_id), reason="Royal House access invitation issued",
               metadata={"expires_at": expires_at.isoformat()})
        connection.commit()
    return {"invite_id": str(invite_id), "token": token, "expires_at": expires_at.isoformat()}


def claim_invite(*, token: str, identity_id: object) -> dict[str, object]:
    if not token:
        raise ValueError("invite_token_required")
    claimant = _uuid(identity_id, "identity_id")
    digest = _token_hash(token)
    now = datetime.now(timezone.utc)
    with postgres_db.connect() as connection:
        row = connection.execute(
            """SELECT invite_id,invited_by,expires_at,claimed_at,revoked_at
               FROM koradaso_invites WHERE token_hash=%s FOR UPDATE""",
            (digest,),
        ).fetchone()
        if not row:
            raise KoradasoInviteDenied("invalid_invite")
        invite_id, invited_by, expires_at, claimed_at, revoked_at = row
        if revoked_at is not None:
            raise KoradasoInviteDenied("invite_revoked")
        if claimed_at is not None:
            raise KoradasoInviteDenied("invite_already_claimed")
        if expires_at <= now:
            raise KoradasoInviteDenied("invite_expired")
        active = connection.execute(
            "SELECT 1 FROM oap_identities WHERE identity_id=%s AND status='ACTIVE'",
            (claimant,),
        ).fetchone()
        if not active:
            raise KoradasoInviteDenied("active_identity_required")
        connection.execute(
            """UPDATE koradaso_invites SET claimed_by=%s,claimed_at=%s
               WHERE invite_id=%s""",
            (claimant, now, invite_id),
        )
        _audit(connection, actor=claimant, action="KORADASO_INVITE_CLAIMED",
               target=str(invite_id), reason="Royal House access invitation claimed",
               metadata={"invited_by": str(invited_by)})
        connection.commit()
    return {"invite_id": str(invite_id), "claimed": True, "royal_status_granted": False}


def revoke_invite(*, invite_id: object, revoked_by: object) -> dict[str, object]:
    iid = _uuid(invite_id, "invite_id")
    actor = _uuid(revoked_by, "revoked_by")
    now = datetime.now(timezone.utc)
    with postgres_db.connect() as connection:
        if not _has_permission(connection, actor, ISSUE_PERMISSION):
            raise KoradasoInviteDenied("koradaso_invite_permission_required")
        row = connection.execute(
            "SELECT claimed_at,revoked_at FROM koradaso_invites WHERE invite_id=%s FOR UPDATE",
            (iid,),
        ).fetchone()
        if not row:
            raise KoradasoInviteDenied("invite_not_found")
        if row[0] is not None:
            raise KoradasoInviteDenied("claimed_invite_cannot_be_revoked")
        if row[1] is None:
            connection.execute(
                "UPDATE koradaso_invites SET revoked_at=%s WHERE invite_id=%s",
                (now, iid),
            )
            _audit(connection, actor=actor, action="KORADASO_INVITE_REVOKED",
                   target=str(iid), reason="Royal House access invitation revoked")
            connection.commit()
    return {"invite_id": str(iid), "revoked": True}
