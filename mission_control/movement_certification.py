"""Governed worker/vehicle certification for OAP Movement.

Internal review never substitutes for transport, insurance, right-to-work, telecom
or other external compliance. No Driver/Rider/Courier role is granted by this
module until a later provider-backed compliance gate exists and is explicitly
approved by Human Authority.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from . import authority, postgres_db

MIGRATION_VERSION = "0006_movement_certification"
MIGRATION_CHECKSUM = "c12f0478ad0bd9ec8f5bb7b1b6865d525acb4a23abc78205eb31e55ba1377c6e"
TABLES = frozenset(
    {
        "oap_movement_worker_applications",
        "oap_movement_vehicles",
        "oap_movement_certification_reviews",
    }
)
WORKER_ROLES = frozenset({"driver", "rider", "courier"})
VEHICLE_TYPES = frozenset(
    {"car", "van", "ebike", "bicycle", "moped", "motorcycle", "none"}
)
ROLE_VEHICLES = {
    "driver": frozenset({"car", "van"}),
    "rider": frozenset({"ebike", "bicycle", "moped", "motorcycle"}),
    "courier": frozenset(
        {"car", "van", "ebike", "bicycle", "moped", "motorcycle"}
    ),
}
REVIEW_DECISIONS = frozenset(
    {"UNDER_REVIEW", "NEEDS_INFO", "INTERNAL_APPROVED", "REJECTED"}
)
ROLE_IDS = {
    "driver": "MOVEMENT_DRIVER",
    "rider": "MOVEMENT_RIDER",
    "courier": "MOVEMENT_COURIER",
}


class CertificationUnavailable(RuntimeError):
    """Raised when certification state cannot be read or written safely."""


def _identity(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_identity_id") from exc


def _role(value: object) -> str:
    role = str(value or "").strip().casefold()
    if role not in WORKER_ROLES:
        raise ValueError("invalid_movement_worker_role")
    return role


def _vehicle(value: object, *, role: str) -> str:
    vehicle = str(value or "").strip().casefold()
    if vehicle not in VEHICLE_TYPES or vehicle not in ROLE_VEHICLES[role]:
        raise ValueError("invalid_vehicle_for_role")
    return vehicle


def _text(value: object, *, maximum: int) -> str:
    return " ".join(str(value or "").strip().split())[:maximum]


def _declarations(value: object) -> dict[str, bool]:
    source = value if isinstance(value, dict) else {}
    normalized = {
        "age_18_or_over": source.get("age_18_or_over") is True,
        "terms_accepted": source.get("terms_accepted") is True,
        "licence_declared": source.get("licence_declared") is True,
        "insurance_declared": source.get("insurance_declared") is True,
    }
    if not normalized["age_18_or_over"] or not normalized["terms_accepted"]:
        raise ValueError("movement_worker_declarations_required")
    return normalized


def schema_status() -> dict[str, object]:
    result: dict[str, object] = {
        "configured": postgres_db.configured(),
        "reachable": False,
        "migration_applied": False,
        "tables_ready": False,
        "ready": False,
        "external_compliance_provider_connected": False,
        "automatic_role_grant_enabled": False,
        "error": None,
    }
    if not postgres_db.configured():
        result["error"] = "database_url_not_configured"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            result["reachable"] = True
            row = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (MIGRATION_VERSION,),
            ).fetchone()
            result["migration_applied"] = bool(
                row is not None and str(row[0]) == MIGRATION_CHECKSUM
            )
            table_rows = connection.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema='public' AND table_name = ANY(%s)""",
                (list(TABLES),),
            ).fetchall()
            result["tables_ready"] = {str(item[0]) for item in table_rows} == TABLES
    except Exception:
        result["error"] = "movement_certification_store_unavailable"
    result["ready"] = bool(
        result["reachable"]
        and result["migration_applied"]
        and result["tables_ready"]
    )
    return result


def submit_application(
    *,
    user: dict[str, object],
    role_type: object,
    vehicle_type: object,
    service_zone: object,
    declarations: object,
    vehicle_label: object = "",
    registration_last4: object = "",
) -> dict[str, object]:
    """Submit an internal OAP application; this never grants a worker role."""

    identity = _identity(user.get("id"))
    role = _role(role_type)
    vehicle = _vehicle(vehicle_type, role=role)
    declaration = _declarations(declarations)
    zone = _text(service_zone, maximum=40)
    label = _text(vehicle_label, maximum=80)
    last4 = _text(registration_last4, maximum=4).upper()
    if last4 and not last4.isalnum():
        raise ValueError("invalid_registration_last4")

    try:
        with postgres_db.connect() as connection:
            authority.sync_authenticated_identity(
                connection,
                identity_id=identity,
                email=user.get("email"),
                display_name=user.get("name"),
                email_verified=bool(user.get("email_verified")),
            )
            certified = connection.execute(
                """SELECT 1 FROM oap_identity_roles
                   WHERE identity_id=%s AND role_id=%s LIMIT 1""",
                (identity, ROLE_IDS[role]),
            ).fetchone()
            if certified is not None:
                raise ValueError("movement_role_already_certified")
            row = connection.execute(
                """INSERT INTO oap_movement_worker_applications(
                       identity_id,role_type,vehicle_type,service_zone,
                       declaration_json,state,external_compliance_state)
                   VALUES (%s,%s,%s,%s,%s::jsonb,'SUBMITTED','PROVIDER_REQUIRED')
                   RETURNING application_id::text,state,external_compliance_state,
                             submitted_at""",
                (
                    identity,
                    role,
                    vehicle,
                    zone,
                    postgres_db.json_dumps(declaration),
                ),
            ).fetchone()
            application_id = str(row[0])
            connection.execute(
                """INSERT INTO oap_movement_vehicles(
                       application_id,identity_id,vehicle_type,display_label,
                       registration_last4,electric,compliance_state,active)
                   VALUES (%s,%s,%s,%s,%s,%s,'PROVIDER_REQUIRED',FALSE)""",
                (
                    application_id,
                    identity,
                    vehicle,
                    label,
                    last4,
                    vehicle in {"ebike"},
                ),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise CertificationUnavailable("movement_certification_unavailable") from exc

    return {
        "application_id": application_id,
        "role_type": role,
        "vehicle_type": vehicle,
        "state": str(row[1]),
        "external_compliance_state": str(row[2]),
        "submitted_at": row[3].isoformat(),
        "role_granted": False,
        "external_compliance_required": True,
    }


def own_applications(identity_id: object, *, limit: int = 20) -> list[dict[str, object]]:
    identity = _identity(identity_id)
    bounded = min(max(int(limit), 1), 50)
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT a.application_id::text,a.role_type,a.vehicle_type,
                          a.service_zone,a.state,a.external_compliance_state,
                          a.submitted_at,a.updated_at,v.display_label,
                          v.registration_last4,v.electric,v.compliance_state,v.active
                   FROM oap_movement_worker_applications a
                   LEFT JOIN oap_movement_vehicles v
                     ON v.application_id=a.application_id
                   WHERE a.identity_id=%s
                   ORDER BY a.submitted_at DESC LIMIT %s""",
                (identity, bounded),
            ).fetchall()
    except Exception as exc:
        raise CertificationUnavailable("movement_certification_unavailable") from exc
    return [
        {
            "application_id": str(row[0]),
            "role_type": str(row[1]),
            "vehicle_type": str(row[2]),
            "service_zone": str(row[3] or ""),
            "state": str(row[4]),
            "external_compliance_state": str(row[5]),
            "submitted_at": row[6].isoformat(),
            "updated_at": row[7].isoformat(),
            "vehicle_label": str(row[8] or ""),
            "registration_last4": str(row[9] or ""),
            "electric": bool(row[10]),
            "vehicle_compliance_state": str(row[11] or "PROVIDER_REQUIRED"),
            "vehicle_active": bool(row[12]),
            "role_granted": False,
        }
        for row in rows
    ]


def review_queue(reviewer_identity_id: object, *, limit: int = 50) -> list[dict[str, object]]:
    reviewer = _identity(reviewer_identity_id)
    bounded = min(max(int(limit), 1), 100)
    try:
        with postgres_db.connect(readonly=True) as connection:
            authority.require_human_authority(connection, reviewer)
            rows = connection.execute(
                """SELECT a.application_id::text,a.identity_id::text,
                          a.role_type,a.vehicle_type,a.service_zone,a.state,
                          a.external_compliance_state,a.submitted_at,
                          v.display_label,v.registration_last4,v.electric,
                          v.compliance_state
                   FROM oap_movement_worker_applications a
                   LEFT JOIN oap_movement_vehicles v
                     ON v.application_id=a.application_id
                   WHERE a.state IN ('SUBMITTED','UNDER_REVIEW','NEEDS_INFO',
                                     'INTERNAL_APPROVED')
                   ORDER BY a.submitted_at ASC LIMIT %s""",
                (bounded,),
            ).fetchall()
    except authority.HumanAuthorityRequired:
        raise
    except Exception as exc:
        raise CertificationUnavailable("movement_certification_unavailable") from exc
    return [
        {
            "application_id": str(row[0]),
            "identity_id": str(row[1]),
            "role_type": str(row[2]),
            "vehicle_type": str(row[3]),
            "service_zone": str(row[4] or ""),
            "state": str(row[5]),
            "external_compliance_state": str(row[6]),
            "submitted_at": row[7].isoformat(),
            "vehicle_label": str(row[8] or ""),
            "registration_last4": str(row[9] or ""),
            "electric": bool(row[10]),
            "vehicle_compliance_state": str(row[11] or "PROVIDER_REQUIRED"),
            "role_granted": False,
        }
        for row in rows
    ]


def review_application(
    *,
    reviewer_identity_id: object,
    application_id: object,
    decision: object,
    reason: object,
) -> dict[str, object]:
    """Record Human Authority internal review; never grant a Movement worker role."""

    reviewer = _identity(reviewer_identity_id)
    application = _identity(application_id)
    normalized_decision = str(decision or "").strip().upper()
    if normalized_decision not in REVIEW_DECISIONS:
        raise ValueError("invalid_certification_review_decision")
    normalized_reason = _text(reason, maximum=500)
    if len(normalized_reason) < 3:
        raise ValueError("certification_review_reason_required")
    try:
        with postgres_db.connect() as connection:
            authority.require_human_authority(connection, reviewer)
            current = connection.execute(
                """SELECT state,external_compliance_state
                   FROM oap_movement_worker_applications
                   WHERE application_id=%s FOR UPDATE""",
                (application,),
            ).fetchone()
            if current is None:
                raise ValueError("movement_application_not_found")
            connection.execute(
                """UPDATE oap_movement_worker_applications
                   SET state=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE application_id=%s""",
                (normalized_decision, application),
            )
            review = connection.execute(
                """INSERT INTO oap_movement_certification_reviews(
                       application_id,reviewer_identity_id,decision,reason,role_granted)
                   VALUES (%s,%s,%s,%s,FALSE)
                   RETURNING review_id::text,created_at""",
                (application, reviewer, normalized_decision, normalized_reason),
            ).fetchone()
            connection.commit()
    except (ValueError, authority.HumanAuthorityRequired):
        raise
    except Exception as exc:
        raise CertificationUnavailable("movement_certification_unavailable") from exc
    return {
        "review_id": str(review[0]),
        "application_id": application,
        "decision": normalized_decision,
        "created_at": review[1].isoformat(),
        "role_granted": False,
        "external_compliance_state": str(current[1]),
        "external_compliance_required": str(current[1]) != "VERIFIED",
    }
