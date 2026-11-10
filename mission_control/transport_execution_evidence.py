"""Evidence-gated transport execution authority.

Stores Founder-reviewed external evidence references in the canonical audit trail.
A recorded reference is not software verification of a licence, provider or receipt.
Execution areas become authorised only when every required evidence item has a
reviewed VERIFIED reference. Human Authority remains final.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any

from . import approval_service, authority, postgres_db

ACTION = "TRANSPORT_EXECUTION_EVIDENCE_ACCEPTED"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EXECUTION_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "carrier_dispatch": (
        "licensed_carrier_binding",
        "capacity_evidence",
        "dispatch_receipt",
    ),
    "ride_dispatch": (
        "eligible_driver_binding",
        "vehicle_evidence",
        "dispatch_receipt",
    ),
    "ticket_issuance": (
        "issuer_authority",
        "inventory_or_entitlement_proof",
        "issued_ticket_receipt",
    ),
    "fare_capture": (
        "regulated_payment_executor",
        "customer_authorisation",
        "capture_receipt",
    ),
    "payment_movement": (
        "regulated_payment_executor",
        "submission_evidence",
        "settlement_evidence",
    ),
    "customs_clearance": (
        "customs_authority_or_broker_binding",
        "declaration_reference",
        "clearance_receipt",
    ),
    "external_tracking_feed": (
        "tracking_source_binding",
        "consent",
        "fresh_signed_or_verified_observation",
    ),
    "vehicle_control": (
        "vehicle_identity_binding",
        "device_or_oem_authority",
        "command_receipt",
    ),
}


def _uuid(value: object, name: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _clean(value: object, *, name: str, maximum: int) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        raise ValueError(f"{name}_required")
    return text[:maximum]


def record_evidence_reference(
    *,
    identity_id: object,
    area: object,
    requirement: object,
    evidence_ref: object,
    evidence_hash: object,
    issuer: object,
    scope: object,
    attestor_type: object,
    verification_state: object,
) -> dict[str, object]:
    """Record one reviewed evidence reference without claiming software authenticity."""

    identity = _uuid(identity_id, "identity_id")
    area_key = str(area or "").strip().lower()
    requirement_key = str(requirement or "").strip().lower()
    if area_key not in EXECUTION_REQUIREMENTS:
        raise ValueError("unsupported_execution_area")
    if requirement_key not in EXECUTION_REQUIREMENTS[area_key]:
        raise ValueError("unsupported_execution_requirement")

    ref = _clean(evidence_ref, name="evidence_ref", maximum=500)
    digest = str(evidence_hash or "").strip().lower()
    if not _SHA256_RE.fullmatch(digest):
        raise ValueError("evidence_hash_must_be_sha256")
    issuer_value = _clean(issuer, name="issuer", maximum=200)
    scope_value = _clean(scope, name="scope", maximum=500)
    attestor = str(attestor_type or "").strip().upper()
    if attestor not in {"EXTERNAL", "INDEPENDENT_VERIFIER", "REGULATED_PROVIDER"}:
        raise ValueError("external_attestor_required")
    state = str(verification_state or "").strip().upper()
    if state not in {"DOCUMENTED", "VERIFIED"}:
        raise ValueError("invalid_verification_state")

    fingerprint = hashlib.sha256(
        f"{area_key}|{requirement_key}|{digest}|{issuer_value}|{scope_value}".encode()
    ).hexdigest()

    with postgres_db.connect() as connection:
        authority_record = authority.require_human_authority(connection, identity)
        if int(authority_record["authority_level"]) != 0:
            raise authority.HumanAuthorityRequired("human_authority_level_required")
        existing = connection.execute(
            """SELECT 1 FROM audit_events
               WHERE action=%s
                 AND metadata->>'fingerprint'=%s
                 AND metadata->>'verification_state'=%s
               LIMIT 1""",
            (ACTION, fingerprint, state),
        ).fetchone()
        if existing is None:
            approval_service._write_audit(
                connection,
                actor_id=identity,
                action=ACTION,
                target=f"{area_key}:{requirement_key}",
                reason="Human Authority recorded transport execution evidence reference.",
                correlation_id=str(uuid.uuid4()),
                metadata={
                    "passed": state == "VERIFIED",
                    "area": area_key,
                    "requirement": requirement_key,
                    "verification_state": state,
                    "evidence_hash": digest,
                    "evidence_ref_hash": hashlib.sha256(ref.encode()).hexdigest(),
                    "issuer_hash": hashlib.sha256(issuer_value.encode()).hexdigest(),
                    "scope_hash": hashlib.sha256(scope_value.encode()).hexdigest(),
                    "attestor_type": attestor,
                    "fingerprint": fingerprint,
                    "software_verified_external_authenticity": False,
                    "human_authority_final": True,
                },
            )
            connection.commit()

    return {
        "recorded": True,
        "area": area_key,
        "requirement": requirement_key,
        "verification_state": state,
        "fingerprint": fingerprint,
        "sensitive_evidence_stored": False,
        "raw_reference_stored": False,
        "raw_issuer_stored": False,
        "raw_scope_stored": False,
        "software_verified_external_authenticity": False,
        "execution_authorised_by_this_receipt_alone": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    """Return coarse execution-evidence coverage; fail closed if unreadable."""

    result: dict[str, Any] = {
        "store_reachable": False,
        "areas": {},
        "all_authorised": False,
        "software_verified_external_authenticity": False,
        "human_authority_final": True,
        "error": None,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT metadata->>'area', metadata->>'requirement',
                          metadata->>'verification_state'
                   FROM audit_events
                   WHERE action=%s AND metadata->>'passed'='true'""",
                (ACTION,),
            ).fetchall()
        verified = {
            (str(row[0]), str(row[1]))
            for row in rows
            if str(row[2]) == "VERIFIED"
        }
        areas: dict[str, Any] = {}
        for area, requirements in EXECUTION_REQUIREMENTS.items():
            present = [req for req in requirements if (area, req) in verified]
            missing = [req for req in requirements if (area, req) not in verified]
            areas[area] = {
                "required": list(requirements),
                "verified": present,
                "missing": missing,
                "live_execution_authorised": not missing,
            }
        result["store_reachable"] = True
        result["areas"] = areas
        result["all_authorised"] = bool(areas) and all(
            item["live_execution_authorised"] for item in areas.values()
        )
    except Exception:  # noqa: BLE001 - execution evidence must fail closed.
        result["error"] = "transport_execution_evidence_unavailable"
        result["areas"] = {
            area: {
                "required": list(requirements),
                "verified": [],
                "missing": list(requirements),
                "live_execution_authorised": False,
            }
            for area, requirements in EXECUTION_REQUIREMENTS.items()
        }
    return result
