"""Personal-use first-party OAP telecom control plane.

One owner, one OAP Number and one Network Passport. Four real-world unlock
tracks are modelled as evidence-gated state machines. This module prepares and
verifies non-sensitive readiness evidence only. It cannot issue production
carrier credentials, activate a carrier, transmit radio, allocate public
numbers or claim external certification by itself.
"""
from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from typing import Any

PERSONAL_LINE: dict[str, Any] = {
    "owner_scope": "self",
    "line_name": "My Line",
    "oap_number": "OAP-25-8-000001",
    "network_passport": {
        "status": "registered",
        "credential_material_exposed": False,
        "carrier_profile_bound": False,
        "production_esim_active": False,
    },
    "device_binding": {
        "mode": "single-primary-device",
        "device_label": "My Phone",
        "hardware_identifiers_exposed": False,
        "binding_status": "ready-for-owner-enrolment",
    },
    "services": {
        "link_call": "identity-ready",
        "link_message": "identity-ready",
        "ptt": "identity-ready",
    },
    "recovery": {
        "preserve_oap_number": True,
        "revoke_old_device_before_rebind": True,
        "human_authority_required": True,
    },
}

PERSONAL_EXECUTION_BOUNDARY: dict[str, bool] = {
    "real_carrier_profile_installed": False,
    "real_carrier_activation_enabled": False,
    "private_radio_transmission_enabled": False,
    "public_number_assigned": False,
    "sensitive_material_exposed": False,
}

UNLOCK_TRACKS: tuple[dict[str, Any], ...] = (
    {
        "id": "carrier_profile",
        "name": "Real carrier profile",
        "execution_flag": "real_carrier_profile_installed",
        "external_gate": "authorised production carrier profile",
        "required_evidence": (
            "authorised_profile_source",
            "owner_profile_binding",
            "device_compatibility",
            "successful_install_receipt",
        ),
    },
    {
        "id": "carrier_activation",
        "name": "Real carrier activation",
        "execution_flag": "real_carrier_activation_enabled",
        "external_gate": "authorised mobile-network subscription and activation",
        "required_evidence": (
            "network_entitlement",
            "activation_receipt",
            "live_attach",
            "live_data_session",
            "disable_recovery_proof",
        ),
    },
    {
        "id": "private_radio",
        "name": "Private OAP 4G/5G radio",
        "execution_flag": "private_radio_transmission_enabled",
        "external_gate": "lawful spectrum authority and compliant radio equipment",
        "required_evidence": (
            "spectrum_authority",
            "frequency_power_location_authority",
            "radio_configuration_receipt",
            "controlled_zone_attach",
        ),
    },
    {
        "id": "public_number",
        "name": "Public phone number",
        "execution_flag": "public_number_assigned",
        "external_gate": "lawful public-number allocation or adoption",
        "required_evidence": (
            "number_allocation_or_adoption",
            "my_line_binding",
            "incoming_route",
            "outgoing_route",
            "port_recovery_state",
        ),
    },
)

TRACK_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "carrier_profile": (),
    "carrier_activation": ("carrier_profile",),
    "private_radio": (),
    "public_number": (),
}

EXTERNAL_APPLICATION_PACKETS: dict[str, dict[str, Any]] = {
    "carrier_profile": {
        "authority": "GSMA eSIM compliance / authorised production profile source",
        "routes": (
            "authorised carrier or profile issuer",
            "OAP SM-DP+ candidate through SAS-SM, functional compliance, declaration and production PKI",
        ),
        "submission_items": (
            "site compliance evidence where OAP operates SM-DP+",
            "functional compliance evidence",
            "GSMA compliance declaration/confirmation where applicable",
            "production PKI/TLS eligibility where applicable",
            "device/eUICC compatibility evidence",
        ),
    },
    "carrier_activation": {
        "authority": "authorised mobile-network operator or network authority",
        "routes": (
            "carrier subscription activation",
            "authorised private-network subscriber activation",
        ),
        "submission_items": (
            "subscriber/network entitlement",
            "profile-to-line binding",
            "activation receipt",
            "live network attach evidence",
            "data-session evidence",
            "disable/recovery evidence",
        ),
    },
    "private_radio": {
        "authority": "Ofcom spectrum licensing framework",
        "routes": (
            "Shared Access licence",
            "other lawful spectrum authority evidenced for the exact deployment",
        ),
        "submission_items": (
            "deployment location",
            "candidate band",
            "requested frequency/channel",
            "power class",
            "antenna characteristics",
            "equipment frequency-agility evidence",
            "approved authority reference",
        ),
    },
    "public_number": {
        "authority": "Ofcom telephone numbering framework",
        "routes": (
            "Number Management System allocation for an eligible communications provider",
            "lawful number adoption/hosting route",
        ),
        "submission_items": (
            "communications-provider or adoption route evidence",
            "number resource reference",
            "My Line binding",
            "incoming route proof",
            "outgoing presentation/routing proof",
            "port and recovery state",
        ),
    },
}


def _track(track_id: str) -> dict[str, Any]:
    track = next((item for item in UNLOCK_TRACKS if item["id"] == track_id), None)
    if track is None:
        raise ValueError("unknown personal telecom unlock track")
    return track


def build_evidence_receipt(
    track_id: str,
    evidence_id: str,
    reference: str,
    issuer: str,
    observed_at: str,
) -> dict[str, str]:
    """Create a non-sensitive immutable-style evidence receipt.

    The receipt hashes the supplied reference instead of exposing external
    account identifiers, credentials, SIM authentication data or certificate
    private material.
    """

    track = _track(track_id)
    if evidence_id not in track["required_evidence"]:
        raise ValueError("evidence item is not required by this unlock track")
    if not all(str(value).strip() for value in (reference, issuer, observed_at)):
        raise ValueError("evidence receipt fields must be non-empty")

    fingerprint = sha256(
        f"{track_id}|{evidence_id}|{reference}|{issuer}|{observed_at}".encode()
    ).hexdigest()
    return {
        "track_id": track_id,
        "evidence_id": evidence_id,
        "issuer": issuer,
        "observed_at": observed_at,
        "reference_fingerprint": fingerprint,
    }


def evaluate_track(
    track_id: str,
    evidence: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    """Evaluate one unlock track from non-sensitive proof flags."""

    track = _track(track_id)
    supplied = dict(evidence or {})
    required = tuple(track["required_evidence"])
    proven = tuple(item for item in required if supplied.get(item) is True)
    missing = tuple(item for item in required if item not in proven)
    external_proof_complete = not missing
    execution_enabled = bool(PERSONAL_EXECUTION_BOUNDARY[track["execution_flag"]])

    if execution_enabled and not external_proof_complete:
        state = "invalid-open-execution"
    elif execution_enabled and external_proof_complete:
        state = "active-proven"
    elif external_proof_complete:
        state = "proof-complete-awaiting-explicit-activation"
    elif proven:
        state = "evidence-in-progress"
    else:
        state = "readiness-open"

    return {
        "id": track["id"],
        "name": track["name"],
        "state": state,
        "software_control_plane_ready": True,
        "external_gate": track["external_gate"],
        "required_evidence": required,
        "proven_evidence": proven,
        "missing_evidence": missing,
        "evidence_count": len(proven),
        "evidence_total": len(required),
        "external_proof_complete": external_proof_complete,
        "execution_enabled": execution_enabled,
        "dependencies": TRACK_DEPENDENCIES[track_id],
    }


def unlock_status(
    evidence_by_track: Mapping[str, Mapping[str, bool]] | None = None,
) -> tuple[dict[str, Any], ...]:
    evidence_by_track = evidence_by_track or {}
    return tuple(
        evaluate_track(track["id"], evidence_by_track.get(track["id"]))
        for track in UNLOCK_TRACKS
    )


def activation_decision(
    track_id: str,
    evidence_by_track: Mapping[str, Mapping[str, bool]] | None = None,
    *,
    human_approved: bool = False,
) -> dict[str, Any]:
    """Evaluate activation eligibility without performing activation."""

    evidence_by_track = evidence_by_track or {}
    assessment = evaluate_track(track_id, evidence_by_track.get(track_id))
    dependency_checks = {
        dependency: evaluate_track(
            dependency, evidence_by_track.get(dependency)
        )["external_proof_complete"]
        for dependency in TRACK_DEPENDENCIES[track_id]
    }
    dependencies_complete = all(dependency_checks.values())
    eligible = bool(
        assessment["external_proof_complete"]
        and dependencies_complete
        and human_approved
        and not assessment["execution_enabled"]
    )
    return {
        "track_id": track_id,
        "eligible": eligible,
        "human_approved": human_approved,
        "external_proof_complete": assessment["external_proof_complete"],
        "dependencies_complete": dependencies_complete,
        "dependency_checks": dependency_checks,
        "execution_enabled": assessment["execution_enabled"],
        "decision": "eligible-for-explicit-external-activation" if eligible else "blocked",
    }


def can_activate(
    track_id: str,
    evidence: Mapping[str, bool] | None = None,
) -> bool:
    """Compatibility helper: proof complete, execution still closed."""

    assessment = evaluate_track(track_id, evidence)
    return bool(
        assessment["external_proof_complete"]
        and not assessment["execution_enabled"]
    )


def application_packet(track_id: str) -> dict[str, Any]:
    """Return a submission-ready requirements manifest, not an application."""

    _track(track_id)
    packet = EXTERNAL_APPLICATION_PACKETS[track_id]
    return {
        "track_id": track_id,
        "authority": packet["authority"],
        "routes": tuple(packet["routes"]),
        "submission_items": tuple(packet["submission_items"]),
        "contains_credentials": False,
        "performs_submission": False,
        "human_review_required": True,
    }


def remaining_gates() -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "track_id": track["id"],
            "name": track["name"],
            "application_packet": application_packet(track["id"]),
            "assessment": evaluate_track(track["id"]),
        }
        for track in UNLOCK_TRACKS
    )


def recovery_plan() -> tuple[str, ...]:
    """Canonical fail-safe recovery order for the personal line."""

    return (
        "freeze affected external execution",
        "preserve OAP Number",
        "revoke old device/profile binding",
        "verify owner authority",
        "rebind replacement device/profile",
        "reconcile service and network evidence",
        "close recovery only after read-back proof",
    )


def validate() -> dict[str, Any]:
    errors: list[str] = []
    number = str(PERSONAL_LINE["oap_number"])
    passport = PERSONAL_LINE["network_passport"]
    binding = PERSONAL_LINE["device_binding"]
    recovery = PERSONAL_LINE["recovery"]
    track_ids = [track["id"] for track in UNLOCK_TRACKS]

    if not number.startswith("OAP-"):
        errors.append("Personal OAP Number must remain inside the OAP namespace")
    if PERSONAL_LINE["owner_scope"] != "self":
        errors.append("Personal line owner scope must remain self")
    if passport["credential_material_exposed"]:
        errors.append("Network Passport credential material must never be exposed")
    if binding["hardware_identifiers_exposed"]:
        errors.append("Hardware identifiers must remain private")
    if not recovery["human_authority_required"]:
        errors.append("Personal recovery must require human authority")
    if any(PERSONAL_EXECUTION_BOUNDARY.values()):
        errors.append("External telecom execution must remain fail-closed without proof")
    if len(track_ids) != len(set(track_ids)):
        errors.append("Personal telecom unlock track IDs must be unique")
    if set(track_ids) != {
        "carrier_profile",
        "carrier_activation",
        "private_radio",
        "public_number",
    }:
        errors.append("Personal telecom must retain all four canonical unlock tracks")
    if set(TRACK_DEPENDENCIES) != set(track_ids):
        errors.append("Every unlock track must have an explicit dependency contract")
    if set(EXTERNAL_APPLICATION_PACKETS) != set(track_ids):
        errors.append("Every unlock track must have an external application packet")

    return {
        "passed": not errors,
        "errors": errors,
        "single_owner": True,
        "single_primary_line": True,
        "unlock_track_count": len(UNLOCK_TRACKS),
        "application_packet_count": len(EXTERNAL_APPLICATION_PACKETS),
    }


def status() -> dict[str, Any]:
    return {
        "system": "OAP Personal Telecom",
        "path": (
            "My Card -> My Line -> OAP Number -> Network Passport -> "
            "My Phone -> Link Call / Link Message / PTT"
        ),
        "line": {
            "owner_scope": PERSONAL_LINE["owner_scope"],
            "line_name": PERSONAL_LINE["line_name"],
            "oap_number": PERSONAL_LINE["oap_number"],
            "network_passport": dict(PERSONAL_LINE["network_passport"]),
            "device_binding": dict(PERSONAL_LINE["device_binding"]),
            "services": dict(PERSONAL_LINE["services"]),
            "recovery": dict(PERSONAL_LINE["recovery"]),
        },
        "execution": dict(PERSONAL_EXECUTION_BOUNDARY),
        "unlock_tracks": unlock_status(),
        "remaining_gates": remaining_gates(),
        "recovery_plan": recovery_plan(),
        "validation": validate(),
        "truth_boundary": (
            "OAP software now prepares and verifies the complete non-sensitive "
            "readiness contract for each remaining personal telecom gate. Real "
            "carrier profiles, network activation, radio transmission and public "
            "number operation still require external authority/evidence and "
            "explicit human-approved activation."
        ),
    }
