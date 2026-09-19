"""Founder-governed OAP certification roles over the existing authority store.

Certified Creator and Certified Merchant are identity certifications, not authority
levels and not permissions. They do not create profiles, grant Founder access,
perform payments, clear rights, certify legal compliance, or execute anything.
Only active level-zero Human Authority may grant or revoke them.
"""
from __future__ import annotations

import uuid
from typing import Any

from . import authority, postgres_db

CERTIFICATIONS: dict[str, dict[str, str]] = {
    "creator": {
        "role_id": "certified_creator",
        "name": "Certified Creator",
        "purpose": "OAP creator identity certification for governed creator surfaces.",
    },
    "merchant": {
        "role_id": "certified_merchant",
        "name": "Certified Merchant",
        "purpose": "OAP merchant identity certification for governed business surfaces.",
    },
}
ROLE_IDS = tuple(item["role_id"] for item in CERTIFICATIONS.values())
CERTIFICATION_AUTHORITY_LEVEL = 5


class CertificationUnavailable(RuntimeError):
    """Raised when the certification store cannot be checked safely."""


def _uuid(value: object, name: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _kind(value: object) -> tuple[str, dict[str, str]]:
    kind = str(value or "").strip().casefold()
    item = CERTIFICATIONS.get(kind)
    if item is None:
        raise ValueError("invalid_certification_kind")
    return kind, item


def _ensure_roles(connection: Any) -> None:
    for item in CERTIFICATIONS.values():
        connection.execute(
            """INSERT INTO oap_roles(role_id,name,authority_level)
               VALUES (%s,%s,%s) ON CONFLICT (role_id) DO NOTHING""",
            (item["role_id"], item["name"], CERTIFICATION_AUTHORITY_LEVEL),
        )


def _target_active(connection: Any, target_identity_id: str) -> bool:
    row = connection.execute(
        """SELECT 1
           FROM oap_identities i
           JOIN users u ON u.id=i.identity_id
           WHERE i.identity_id=%s AND i.status='ACTIVE' AND u.status='active'
           LIMIT 1""",
        (target_identity_id,),
    ).fetchone()
    return row is not None


def grant(
    *,
    target_identity_id: object,
    certification_kind: object,
    granted_by_identity_id: object,
    human_authority_approved: bool,
) -> dict[str, object]:
    """Grant one certification after an explicit level-zero approval."""

    if human_authority_approved is not True:
        raise PermissionError("human_authority_approval_required")
    target = _uuid(target_identity_id, "target_identity_id")
    granter = _uuid(granted_by_identity_id, "granted_by_identity_id")
    kind, item = _kind(certification_kind)
    try:
        with postgres_db.connect() as connection:
            authority.require_human_authority(connection, granter)
            if not _target_active(connection, target):
                raise ValueError("target_identity_unavailable")
            _ensure_roles(connection)
            connection.execute(
                """INSERT INTO oap_identity_roles(identity_id,role_id,granted_by)
                   VALUES (%s,%s,%s) ON CONFLICT DO NOTHING""",
                (target, item["role_id"], granter),
            )
            connection.commit()
    except (ValueError, PermissionError):
        raise
    except Exception as exc:
        raise CertificationUnavailable("certification_grant_unavailable") from exc
    return {
        "identity_id": target,
        "certification": kind,
        "role_id": item["role_id"],
        "name": item["name"],
        "certified": True,
        "grants_permissions": False,
        "grants_founder_access": False,
        "human_authority_final": True,
    }


def revoke(
    *,
    target_identity_id: object,
    certification_kind: object,
    revoked_by_identity_id: object,
    human_authority_approved: bool,
) -> dict[str, object]:
    """Revoke one certification after an explicit level-zero approval."""

    if human_authority_approved is not True:
        raise PermissionError("human_authority_approval_required")
    target = _uuid(target_identity_id, "target_identity_id")
    revoker = _uuid(revoked_by_identity_id, "revoked_by_identity_id")
    kind, item = _kind(certification_kind)
    try:
        with postgres_db.connect() as connection:
            authority.require_human_authority(connection, revoker)
            connection.execute(
                "DELETE FROM oap_identity_roles WHERE identity_id=%s AND role_id=%s",
                (target, item["role_id"]),
            )
            connection.commit()
    except (ValueError, PermissionError):
        raise
    except Exception as exc:
        raise CertificationUnavailable("certification_revoke_unavailable") from exc
    return {
        "identity_id": target,
        "certification": kind,
        "role_id": item["role_id"],
        "name": item["name"],
        "certified": False,
        "grants_permissions": False,
        "grants_founder_access": False,
        "human_authority_final": True,
    }


def identity_status(identity_id: object) -> dict[str, object]:
    """Return only certification role state for one OAP identity."""

    target = _uuid(identity_id, "identity_id")
    result = {
        "identity_id": target,
        "creator": False,
        "merchant": False,
        "certifications": [],
        "grants_permissions": False,
        "grants_founder_access": False,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT ir.role_id
                   FROM oap_identity_roles ir
                   JOIN oap_identities i ON i.identity_id=ir.identity_id
                   WHERE ir.identity_id=%s AND i.status='ACTIVE'
                     AND ir.role_id=ANY(%s)
                   ORDER BY ir.role_id""",
                (target, list(ROLE_IDS)),
            ).fetchall()
    except Exception as exc:
        raise CertificationUnavailable("certification_read_unavailable") from exc
    role_ids = {str(row[0]) for row in rows}
    for kind, item in CERTIFICATIONS.items():
        active = item["role_id"] in role_ids
        result[kind] = active
        if active:
            result["certifications"].append(item["name"])
    return result


def labels_for_identities(identity_ids: list[object]) -> dict[str, list[str]]:
    """Return only currently granted certification names for the supplied identities."""

    normalized: list[str] = []
    for value in identity_ids:
        try:
            normalized.append(_uuid(value, "identity_id"))
        except ValueError:
            continue
    if not normalized:
        return {}
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT identity_id,role_id
                   FROM oap_identity_roles
                   WHERE identity_id=ANY(%s::uuid[])
                     AND role_id=ANY(%s)""",
                (normalized, list(ROLE_IDS)),
            ).fetchall()
    except Exception as exc:
        raise CertificationUnavailable("certification_read_unavailable") from exc

    role_to_name = {
        item["role_id"]: item["name"] for item in CERTIFICATIONS.values()
    }
    result: dict[str, list[str]] = {identity_id: [] for identity_id in normalized}
    for identity_id, role_id in rows:
        name = role_to_name.get(str(role_id))
        if name:
            result.setdefault(str(identity_id), []).append(name)
    for names in result.values():
        names.sort()
    return result


def status() -> dict[str, object]:
    """Return redacted readiness and certification counts without identity data."""

    result: dict[str, object] = {
        "configured": postgres_db.configured(),
        "database_reachable": False,
        "roles_ready": False,
        "role_permissions_zero": False,
        "certified_creator_count": 0,
        "certified_merchant_count": 0,
        "software_ready": True,
        "runtime_ready": False,
        "human_authority_required": True,
        "grants_founder_access": False,
        "grants_permissions": False,
        "error": None,
    }
    if not result["configured"]:
        result["error"] = "database_url_not_configured"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            result["database_reachable"] = True
            role_rows = connection.execute(
                "SELECT role_id FROM oap_roles WHERE role_id=ANY(%s)",
                (list(ROLE_IDS),),
            ).fetchall()
            roles_present = {str(row[0]) for row in role_rows}
            result["roles_ready"] = set(ROLE_IDS) <= roles_present
            permission_row = connection.execute(
                "SELECT COUNT(*) FROM oap_role_permissions WHERE role_id=ANY(%s)",
                (list(ROLE_IDS),),
            ).fetchone()
            result["role_permissions_zero"] = int(permission_row[0] if permission_row else 0) == 0
            counts = connection.execute(
                """SELECT role_id,COUNT(*) FROM oap_identity_roles
                   WHERE role_id=ANY(%s) GROUP BY role_id""",
                (list(ROLE_IDS),),
            ).fetchall()
            by_role = {str(row[0]): int(row[1]) for row in counts}
            result["certified_creator_count"] = by_role.get("certified_creator", 0)
            result["certified_merchant_count"] = by_role.get("certified_merchant", 0)
    except Exception:  # noqa: BLE001 - readiness must degrade safely.
        result["error"] = "certification_store_unavailable"
        return result
    result["runtime_ready"] = bool(
        result["database_reachable"]
        and result["roles_ready"]
        and result["role_permissions_zero"]
    )
    return result
