"""Governed worker and vehicle certification for OAP Movement.

Internal review never substitutes for transport, insurance, right-to-work,
telecom, or other external compliance. This module never grants a Driver,
Rider, or Courier role. External evidence and a later Human Authority gate are
required before any role activation path may be introduced.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from uuid import UUID

from . import authority, postgres_db

MIGRATION_VERSION = "0006_movement_certification"
MIGRATION_CHECKSUM = "444ba01632473bc3d8fea794d2bd3cf799e327cbb2a32b73606e9729daa102c9"
MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "0006_movement_certification.sql"
)
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
MOTOR_VEHICLES = frozenset({"car", "van", "moped", "motorcycle"})
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
REVIEW_TRANSITIONS = {
    "SUBMITTED": frozenset(REVIEW_DECISIONS),
    "UNDER_REVIEW": frozenset({"NEEDS_INFO", "INTERNAL_APPROVED", "REJECTED"}),
    "NEEDS_INFO": frozenset({"REJECTED"}),
    "INTERNAL_APPROVED": frozenset(),
    "REJECTED": frozenset(),
    "CANCELLED": frozenset(),
}
CANCELLABLE_STATES = frozenset(
    {"SUBMITTED", "UNDER_REVIEW", "NEEDS_INFO", "INTERNAL_APPROVED"}
)
ROLE_IDS = {
    "driver": "MOVEMENT_DRIVER",
    "rider": "MOVEMENT_RIDER",
    "courier": "MOVEMENT_COURIER",
}
APPLICATION_NOTICE_VERSION = "movement-worker-application-notice-v1"
APPLICATION_NOTICE_TEXT = (
    "This application records limited internal declarations only. It is not "
    "legal clearance, external compliance verification, certification, a job "
    "offer, or permission to perform Movement work. OAP schedules the submitted "
    "application and review record for Human Authority-reviewed deletion after "
    "90 days unless the applicant deletes it sooner. Do not submit licence "
    "numbers, identity documents, "
    "health information, or other sensitive personal data."
)
APPLICATION_NOTICE_DIGEST = hashlib.sha256(
    APPLICATION_NOTICE_TEXT.encode("utf-8")
).hexdigest()
RETENTION_DAYS = 90
_REGISTRATION_SUFFIX = re.compile(r"^[A-Z0-9]{0,4}$")


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


def _text(
    value: object,
    *,
    name: str,
    maximum: int,
    required: bool = False,
) -> str:
    normalized = " ".join(str(value or "").strip().split())
    if required and not normalized:
        raise ValueError(f"{name}_required")
    if len(normalized) > maximum:
        raise ValueError(f"{name}_too_long")
    return normalized


def _registration(value: object) -> str:
    suffix = _text(
        value,
        name="registration_last4",
        maximum=4,
    ).upper()
    if not _REGISTRATION_SUFFIX.fullmatch(suffix):
        raise ValueError("invalid_registration_last4")
    return suffix


def _declarations(value: object, *, vehicle: str) -> dict[str, bool]:
    source = value if isinstance(value, dict) else {}
    normalized = {
        "age_18_or_over": source.get("age_18_or_over") is True,
        "terms_accepted": source.get("terms_accepted") is True,
        "licence_declared": source.get("licence_declared") is True,
        "insurance_declared": source.get("insurance_declared") is True,
    }
    if not normalized["age_18_or_over"] or not normalized["terms_accepted"]:
        raise ValueError("movement_worker_declarations_required")
    if vehicle in MOTOR_VEHICLES and (
        not normalized["licence_declared"]
        or not normalized["insurance_declared"]
    ):
        raise ValueError("motor_vehicle_declarations_required")
    return normalized


def migration_sql() -> str:
    """Return the reviewed, immutable SQL receipt for branch-first migration."""

    return MIGRATION_PATH.read_text(encoding="utf-8")


def _migration_statements() -> tuple[str, ...]:
    text = migration_sql()
    schema_sql, receipt = text.split("\nINSERT INTO oap_schema_migrations", 1)
    calculated = hashlib.sha256((schema_sql + "\n").encode("utf-8")).hexdigest()
    if calculated != MIGRATION_CHECKSUM:
        raise RuntimeError("Movement certification migration checksum mismatch")
    if MIGRATION_CHECKSUM not in receipt or MIGRATION_VERSION not in receipt:
        raise RuntimeError("Movement certification migration receipt mismatch")
    return tuple(
        statement.strip().rstrip(";")
        for statement in schema_sql.strip().split(";\n\n")
        if statement.strip()
    )


def schema_status() -> dict[str, object]:
    result: dict[str, object] = {
        "configured": postgres_db.configured(),
        "reachable": False,
        "migration_applied": False,
        "tables_ready": False,
        "ready": False,
        "terms_version": APPLICATION_NOTICE_VERSION,
        "retention_days": RETENTION_DAYS,
        "expired_records": 0,
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
            if result["tables_ready"]:
                expired = connection.execute(
                    """SELECT COUNT(*) FROM oap_movement_worker_applications
                       WHERE retention_expires_at <= CURRENT_TIMESTAMP"""
                ).fetchone()
                result["expired_records"] = int(expired[0]) if expired else 0
    except Exception:  # noqa: BLE001 - status redacts backend/provider detail.
        result["error"] = "movement_certification_store_unavailable"
    result["ready"] = bool(
        result["reachable"]
        and result["migration_applied"]
        and result["tables_ready"]
    )
    return result


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, object]:
    """Apply the reviewed schema only after explicit Human Authority invocation."""

    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    base = postgres_db.postgres_status()
    if not base.get("initialized"):
        raise RuntimeError("Base PostgreSQL schema must be ready first")
    statements = _migration_statements()
    if dry_run:
        return {
            "dry_run": True,
            "migration": MIGRATION_VERSION,
            "checksum": MIGRATION_CHECKSUM,
            "tables": len(TABLES),
        }
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800007,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != MIGRATION_CHECKSUM:
            raise RuntimeError("Applied Movement certification checksum mismatch")
        if row is None:
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (MIGRATION_VERSION, MIGRATION_CHECKSUM),
            )
        connection.commit()
    status = schema_status()
    if not status.get("ready"):
        raise RuntimeError("Movement certification migration did not become ready")
    return status


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
    declaration = _declarations(declarations, vehicle=vehicle)
    zone = _text(service_zone, name="service_zone", maximum=40)
    label = _text(vehicle_label, name="vehicle_label", maximum=80)
    suffix = _registration(registration_last4)

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
            active = connection.execute(
                """SELECT 1 FROM oap_movement_worker_applications
                   WHERE identity_id=%s AND role_type=%s
                     AND state NOT IN ('REJECTED','CANCELLED') LIMIT 1""",
                (identity, role),
            ).fetchone()
            if active is not None:
                raise ValueError("movement_application_already_active")
            row = connection.execute(
                """INSERT INTO oap_movement_worker_applications(
                       identity_id,role_type,vehicle_type,service_zone,
                       declaration_json,terms_version,terms_digest,state,
                       external_compliance_state)
                   VALUES (%s,%s,%s,%s,%s::jsonb,%s,%s,'SUBMITTED',
                           'PROVIDER_REQUIRED')
                   RETURNING application_id::text,state,external_compliance_state,
                             submitted_at,retention_expires_at""",
                (
                    identity,
                    role,
                    vehicle,
                    zone,
                    json.dumps(declaration, separators=(",", ":"), sort_keys=True),
                    APPLICATION_NOTICE_VERSION,
                    APPLICATION_NOTICE_DIGEST,
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
                    suffix,
                    vehicle == "ebike",
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
        "retention_expires_at": row[4].isoformat(),
        "terms_version": APPLICATION_NOTICE_VERSION,
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
                          v.registration_last4,v.electric,v.compliance_state,v.active,
                          a.terms_version,a.retention_expires_at,
                          COALESCE(latest.applicant_message,'')
                   FROM oap_movement_worker_applications a
                   LEFT JOIN oap_movement_vehicles v
                     ON v.application_id=a.application_id
                   LEFT JOIN LATERAL (
                     SELECT applicant_message
                     FROM oap_movement_certification_reviews r
                     WHERE r.application_id=a.application_id
                     ORDER BY r.created_at DESC,r.review_id DESC LIMIT 1
                   ) latest ON TRUE
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
            "terms_version": str(row[13]),
            "retention_expires_at": row[14].isoformat(),
            "applicant_message": str(row[15] or ""),
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
                          v.compliance_state,a.applicant_response,
                          a.terms_version,a.retention_expires_at
                   FROM oap_movement_worker_applications a
                   LEFT JOIN oap_movement_vehicles v
                     ON v.application_id=a.application_id
                   WHERE a.state IN ('SUBMITTED','UNDER_REVIEW','NEEDS_INFO',
                                     'INTERNAL_APPROVED')
                     AND a.retention_expires_at > CURRENT_TIMESTAMP
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
            "applicant_response": str(row[12] or ""),
            "terms_version": str(row[13]),
            "retention_expires_at": row[14].isoformat(),
            "allowed_decisions": tuple(
                sorted(REVIEW_TRANSITIONS.get(str(row[5]), frozenset()))
            ),
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
    applicant_message: object = "",
) -> dict[str, object]:
    """Record a guarded internal review; never grant a Movement worker role."""

    reviewer = _identity(reviewer_identity_id)
    application = _identity(application_id)
    normalized_decision = str(decision or "").strip().upper()
    if normalized_decision not in REVIEW_DECISIONS:
        raise ValueError("invalid_certification_review_decision")
    normalized_reason = _text(
        reason,
        name="certification_review_reason",
        maximum=500,
        required=True,
    )
    if len(normalized_reason) < 3:
        raise ValueError("certification_review_reason_required")
    public_message = _text(
        applicant_message,
        name="applicant_message",
        maximum=500,
        required=normalized_decision == "NEEDS_INFO",
    )
    if normalized_decision == "NEEDS_INFO" and len(public_message) < 3:
        raise ValueError("applicant_message_required")
    try:
        with postgres_db.connect() as connection:
            authority.require_human_authority(connection, reviewer)
            current = connection.execute(
                """SELECT state,external_compliance_state
                   FROM oap_movement_worker_applications
                   WHERE application_id=%s
                     AND retention_expires_at > CURRENT_TIMESTAMP
                   FOR UPDATE""",
                (application,),
            ).fetchone()
            if current is None:
                raise ValueError("movement_application_not_found")
            current_state = str(current[0])
            if normalized_decision not in REVIEW_TRANSITIONS.get(
                current_state, frozenset()
            ):
                raise ValueError("invalid_certification_state_transition")
            connection.execute(
                """UPDATE oap_movement_worker_applications
                   SET state=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE application_id=%s""",
                (normalized_decision, application),
            )
            review = connection.execute(
                """INSERT INTO oap_movement_certification_reviews(
                       application_id,reviewer_identity_id,decision,reason,
                       applicant_message,role_granted)
                   VALUES (%s,%s,%s,%s,%s,FALSE)
                   RETURNING review_id::text,created_at""",
                (
                    application,
                    reviewer,
                    normalized_decision,
                    normalized_reason,
                    public_message,
                ),
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
        "applicant_message": public_message,
        "created_at": review[1].isoformat(),
        "role_granted": False,
        "external_compliance_state": str(current[1]),
        "external_compliance_required": str(current[1]) != "VERIFIED",
    }


def resubmit_application(
    *,
    identity_id: object,
    application_id: object,
    service_zone: object,
    declarations: object,
    response_message: object,
    vehicle_label: object = "",
    registration_last4: object = "",
) -> dict[str, object]:
    """Let only the applicant answer NEEDS_INFO and return to SUBMITTED."""

    identity = _identity(identity_id)
    application = _identity(application_id)
    zone = _text(service_zone, name="service_zone", maximum=40)
    label = _text(vehicle_label, name="vehicle_label", maximum=80)
    suffix = _registration(registration_last4)
    response = _text(
        response_message,
        name="applicant_response",
        maximum=500,
        required=True,
    )
    if len(response) < 3:
        raise ValueError("applicant_response_required")
    try:
        with postgres_db.connect() as connection:
            current = connection.execute(
                """SELECT state,vehicle_type FROM oap_movement_worker_applications
                   WHERE application_id=%s AND identity_id=%s
                     AND retention_expires_at > CURRENT_TIMESTAMP
                   FOR UPDATE""",
                (application, identity),
            ).fetchone()
            if current is None:
                raise ValueError("movement_application_not_found")
            if str(current[0]) != "NEEDS_INFO":
                raise ValueError("movement_application_not_resubmittable")
            vehicle = str(current[1])
            declaration = _declarations(declarations, vehicle=vehicle)
            connection.execute(
                """UPDATE oap_movement_worker_applications
                   SET service_zone=%s,declaration_json=%s::jsonb,
                       terms_version=%s,terms_digest=%s,applicant_response=%s,
                       state='SUBMITTED',updated_at=CURRENT_TIMESTAMP,
                       retention_expires_at=CURRENT_TIMESTAMP + INTERVAL '90 days'
                   WHERE application_id=%s AND identity_id=%s""",
                (
                    zone,
                    json.dumps(declaration, separators=(",", ":"), sort_keys=True),
                    APPLICATION_NOTICE_VERSION,
                    APPLICATION_NOTICE_DIGEST,
                    response,
                    application,
                    identity,
                ),
            )
            connection.execute(
                """UPDATE oap_movement_vehicles
                   SET display_label=%s,registration_last4=%s,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE application_id=%s AND identity_id=%s""",
                (label, suffix, application, identity),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise CertificationUnavailable("movement_certification_unavailable") from exc
    return {
        "application_id": application,
        "state": "SUBMITTED",
        "terms_version": APPLICATION_NOTICE_VERSION,
        "role_granted": False,
        "external_compliance_required": True,
    }


def cancel_application(*, identity_id: object, application_id: object) -> dict[str, object]:
    """Withdraw an application and immediately scrub optional vehicle/location data."""

    identity = _identity(identity_id)
    application = _identity(application_id)
    try:
        with postgres_db.connect() as connection:
            current = connection.execute(
                """SELECT state FROM oap_movement_worker_applications
                   WHERE application_id=%s AND identity_id=%s FOR UPDATE""",
                (application, identity),
            ).fetchone()
            if current is None:
                raise ValueError("movement_application_not_found")
            if str(current[0]) not in CANCELLABLE_STATES:
                raise ValueError("movement_application_not_cancellable")
            connection.execute(
                """UPDATE oap_movement_worker_applications
                   SET state='CANCELLED',service_zone='',declaration_json='{}'::jsonb,
                       applicant_response='',updated_at=CURRENT_TIMESTAMP,
                       retention_expires_at=LEAST(
                         retention_expires_at,
                         CURRENT_TIMESTAMP + INTERVAL '7 days')
                   WHERE application_id=%s AND identity_id=%s""",
                (application, identity),
            )
            connection.execute(
                """UPDATE oap_movement_vehicles
                   SET display_label='',registration_last4='',active=FALSE,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE application_id=%s AND identity_id=%s""",
                (application, identity),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise CertificationUnavailable("movement_certification_unavailable") from exc
    return {
        "application_id": application,
        "state": "CANCELLED",
        "personal_fields_scrubbed": True,
        "role_granted": False,
    }


def delete_application(*, identity_id: object, application_id: object) -> dict[str, object]:
    """Delete a closed applicant-owned record and its cascading review/vehicle data."""

    identity = _identity(identity_id)
    application = _identity(application_id)
    try:
        with postgres_db.connect() as connection:
            current = connection.execute(
                """SELECT state FROM oap_movement_worker_applications
                   WHERE application_id=%s AND identity_id=%s FOR UPDATE""",
                (application, identity),
            ).fetchone()
            if current is None:
                raise ValueError("movement_application_not_found")
            if str(current[0]) not in {"CANCELLED", "REJECTED"}:
                raise ValueError("movement_application_not_deletable")
            connection.execute(
                """DELETE FROM oap_movement_worker_applications
                   WHERE application_id=%s AND identity_id=%s""",
                (application, identity),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise CertificationUnavailable("movement_certification_unavailable") from exc
    return {"application_id": application, "deleted": True}


def purge_expired_applications(
    *, reviewer_identity_id: object, limit: int = 500
) -> dict[str, object]:
    """Human Authority-only bounded deletion of records past their stated retention."""

    reviewer = _identity(reviewer_identity_id)
    bounded = min(max(int(limit), 1), 1000)
    try:
        with postgres_db.connect() as connection:
            authority.require_human_authority(connection, reviewer)
            rows = connection.execute(
                """WITH expired AS (
                     SELECT application_id
                     FROM oap_movement_worker_applications
                     WHERE retention_expires_at <= CURRENT_TIMESTAMP
                     ORDER BY retention_expires_at ASC
                     LIMIT %s FOR UPDATE SKIP LOCKED
                   )
                   DELETE FROM oap_movement_worker_applications a
                   USING expired
                   WHERE a.application_id=expired.application_id
                   RETURNING a.application_id::text""",
                (bounded,),
            ).fetchall()
            connection.commit()
    except authority.HumanAuthorityRequired:
        raise
    except Exception as exc:
        raise CertificationUnavailable("movement_certification_unavailable") from exc
    return {
        "deleted": len(rows),
        "limit": bounded,
        "role_grants_changed": False,
    }
