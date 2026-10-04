"""Personal-use first-party OAP telecom identity contract.

This module models one owner, one OAP Number and one Network Passport for
personal use. It deliberately stores no carrier secrets, eUICC secrets, IMSI,
ICCID, EID, authentication vectors or production activation material.
"""
from __future__ import annotations

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
    "raw_telecom_secrets_exposed": False,
}


def validate() -> dict[str, Any]:
    errors: list[str] = []
    number = str(PERSONAL_LINE["oap_number"])
    passport = PERSONAL_LINE["network_passport"]
    binding = PERSONAL_LINE["device_binding"]
    recovery = PERSONAL_LINE["recovery"]

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
        errors.append("External telecom execution must remain fail-closed")

    return {
        "passed": not errors,
        "errors": errors,
        "single_owner": True,
        "single_primary_line": True,
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
        "validation": validate(),
        "truth_boundary": (
            "This is a first-party personal identity/control contract. It is not "
            "proof of a production carrier eSIM, public telephone number, live "
            "radio service or certified SM-DP+ profile."
        ),
    }
