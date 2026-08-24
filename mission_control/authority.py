"""Canonical Neon-authenticated Human Authority binding.

The authenticated email is only a bootstrap selector. Authority is granted in
the OAP identity/role/permission tables and is always re-checked there before a
decision can be recorded. No password or Neon session token is stored here.
"""

from __future__ import annotations

import hmac
import os
import uuid
from typing import Any

from . import postgres_db

HUMAN_AUTHORITY_ROLE = "human_authority"
COMMUNITY_MEMBER_ROLE = "community_member"
APPROVAL_PERMISSION = "APPROVE_RECOMMENDATION"
REQUEST_PERMISSION = "REQUEST_RECOMMENDATION"


class AuthorityUnavailable(RuntimeError):
    """Raised when the canonical authority store cannot be checked safely."""


class HumanAuthorityRequired(PermissionError):
    """Raised when a verified user is not active level-zero authority."""


def configured_email() -> str:
    """Return the configured bootstrap email without exposing it in status."""

    return os.environ.get("OAP_HUMAN_AUTHORITY_EMAIL", "").strip().casefold()


def configured_identity() -> str:
    """Return the exact authority UUID selector, or an empty string."""

    value = os.environ.get("OAP_HUMAN_AUTHORITY_ID", "").strip()
    if not value:
        return ""
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return ""


def _validated_uuid(value: object) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_identity") from exc


def email_is_authority(email: object) -> bool:
    """Match one authenticated email to the configured level-zero selector."""

    expected = configured_email()
    candidate = str(email or "").strip().casefold()
    return bool(expected and candidate) and hmac.compare_digest(expected, candidate)


def identity_is_authority(identity_id: object) -> bool:
    """Match an authenticated Neon UUID to the exact configured selector."""

    expected = configured_identity()
    try:
        candidate = _validated_uuid(identity_id)
    except ValueError:
        return False
    return bool(expected) and hmac.compare_digest(expected, candidate)


def sync_authenticated_identity(
    connection: Any,
    *,
    identity_id: object,
    email: object,
    display_name: object,
    email_verified: bool = False,
) -> dict[str, object]:
    """Bind one verified Neon UUID to its canonical OAP role.

    Existing Human Authority is never downgraded if the environment selector is
    temporarily absent. A non-authority account receives only the community
    recommendation permission.
    """

    identity = _validated_uuid(identity_id)
    name = str(display_name or "OAP Member").strip()[:120] or "OAP Member"
    make_authority = identity_is_authority(identity) or (
        bool(email_verified) and email_is_authority(email)
    )
    identity_type = "HUMAN_AUTHORITY" if make_authority else "HUMAN"
    connection.execute(
        """INSERT INTO oap_identities(
               identity_id,display_name,identity_type,status
           ) VALUES (%s,%s,%s,'ACTIVE')
           ON CONFLICT (identity_id) DO UPDATE SET
             display_name=EXCLUDED.display_name,
             identity_type=CASE
               WHEN oap_identities.identity_type='HUMAN_AUTHORITY'
                 THEN oap_identities.identity_type
               ELSE EXCLUDED.identity_type
             END,
             updated_at=CURRENT_TIMESTAMP""",
        (identity, name, identity_type),
    )
    connection.execute(
        """INSERT INTO oap_permissions(permission_id,description) VALUES
             (%s,'Request a governed SMI recommendation'),
             (%s,'Record a level-zero Human Authority decision')
           ON CONFLICT (permission_id) DO NOTHING""",
        (REQUEST_PERMISSION, APPROVAL_PERMISSION),
    )
    connection.execute(
        """INSERT INTO oap_roles(role_id,name,authority_level) VALUES
             (%s,'Community Member',5),
             (%s,'Human Authority',0)
           ON CONFLICT (role_id) DO NOTHING""",
        (COMMUNITY_MEMBER_ROLE, HUMAN_AUTHORITY_ROLE),
    )
    connection.execute(
        """INSERT INTO oap_role_permissions(role_id,permission_id)
           VALUES (%s,%s) ON CONFLICT DO NOTHING""",
        (COMMUNITY_MEMBER_ROLE, REQUEST_PERMISSION),
    )
    connection.execute(
        """INSERT INTO oap_identity_roles(identity_id,role_id,granted_by)
           VALUES (%s,%s,NULL) ON CONFLICT DO NOTHING""",
        (identity, COMMUNITY_MEMBER_ROLE),
    )
    if make_authority:
        connection.execute(
            """INSERT INTO oap_role_permissions(role_id,permission_id) VALUES
                 (%s,%s),(%s,%s)
               ON CONFLICT DO NOTHING""",
            (
                HUMAN_AUTHORITY_ROLE,
                REQUEST_PERMISSION,
                HUMAN_AUTHORITY_ROLE,
                APPROVAL_PERMISSION,
            ),
        )
        connection.execute(
            """INSERT INTO oap_identity_roles(identity_id,role_id,granted_by)
               VALUES (%s,%s,%s) ON CONFLICT DO NOTHING""",
            (identity, HUMAN_AUTHORITY_ROLE, identity),
        )
    record = authority_record(connection, identity)
    return record or {
        "identity_id": identity,
        "is_human_authority": False,
        "authority_level": 5,
        "permissions": (REQUEST_PERMISSION,),
    }


def authority_record(connection: Any, identity_id: object) -> dict[str, object] | None:
    """Read one active identity's effective authority and permissions."""

    identity = _validated_uuid(identity_id)
    row = connection.execute(
        """SELECT i.identity_id,i.identity_type,MIN(r.authority_level)
           FROM oap_identities i
           JOIN oap_identity_roles ir ON ir.identity_id=i.identity_id
           JOIN oap_roles r ON r.role_id=ir.role_id
           WHERE i.identity_id=%s AND i.status='ACTIVE'
           GROUP BY i.identity_id,i.identity_type""",
        (identity,),
    ).fetchone()
    if row is None:
        return None
    permissions = connection.execute(
        """SELECT DISTINCT rp.permission_id
           FROM oap_identity_roles ir
           JOIN oap_role_permissions rp ON rp.role_id=ir.role_id
           WHERE ir.identity_id=%s ORDER BY rp.permission_id""",
        (identity,),
    ).fetchall()
    permission_values = tuple(str(item[0]) for item in permissions)
    authority_level = int(row[2])
    is_authority = (
        str(row[1]) == "HUMAN_AUTHORITY"
        and authority_level == 0
        and APPROVAL_PERMISSION in permission_values
    )
    return {
        "identity_id": str(row[0]),
        "identity_type": str(row[1]),
        "authority_level": authority_level,
        "permissions": permission_values,
        "is_human_authority": is_authority,
    }


def require_human_authority(connection: Any, identity_id: object) -> dict[str, object]:
    """Return a verified authority record or fail closed."""

    record = authority_record(connection, identity_id)
    if not record or not record["is_human_authority"]:
        raise HumanAuthorityRequired("level_zero_human_authority_required")
    return record


def status() -> dict[str, object]:
    """Return redacted live authority readiness."""

    result: dict[str, object] = {
        "identity_selector_configured": bool(configured_identity()),
        "email_selector_configured": bool(configured_email()),
        "database_reachable": False,
        "active_level_zero": False,
        "approval_permission": False,
        "ready": False,
        "error": None,
    }
    if not postgres_db.configured():
        result["error"] = "database_url_not_configured"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            result["database_reachable"] = True
            row = connection.execute(
                """SELECT 1
                   FROM oap_identities i
                   JOIN oap_identity_roles ir ON ir.identity_id=i.identity_id
                   JOIN oap_roles r ON r.role_id=ir.role_id
                   JOIN oap_role_permissions rp ON rp.role_id=r.role_id
                   WHERE i.status='ACTIVE' AND i.identity_type='HUMAN_AUTHORITY'
                     AND r.authority_level=0
                     AND rp.permission_id=%s LIMIT 1""",
                (APPROVAL_PERMISSION,),
            ).fetchone()
            result["active_level_zero"] = row is not None
            result["approval_permission"] = row is not None
    except Exception:  # noqa: BLE001 - readiness must degrade safely.
        result["error"] = "authority_store_unavailable"
    result["ready"] = bool(
        (
            result["identity_selector_configured"]
            or result["email_selector_configured"]
        )
        and result["database_reachable"]
        and result["active_level_zero"]
        and result["approval_permission"]
    )
    return result
