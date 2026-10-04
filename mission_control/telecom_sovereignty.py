"""Canonical first-party OAP telecom sovereignty contract.

Routes A, B and C are one progressive stack:
A = identity/orchestration, B = profile issuance/credential infrastructure,
C = private network/radio. This module is status/control metadata only. It never
issues production credentials, activates eSIMs, changes radio state or claims
external certification.
"""
from __future__ import annotations

from typing import Any

ROUTES: tuple[dict[str, Any], ...] = (
    {
        "id": "A",
        "name": "Identity & Orchestration",
        "owner": "OAP Infrastructure",
        "software_target": True,
        "external_trust_required": False,
        "components": (
            "my_card",
            "oap_number",
            "network_passport",
            "subscriber_registry",
            "device_registry",
            "guardian_policy",
            "sika_entitlement",
            "recovery",
            "hrm_evidence",
            "smi_exceptions",
        ),
    },
    {
        "id": "B",
        "name": "Profile Issuance & Credential Infrastructure",
        "owner": "OAP Infrastructure",
        "software_target": True,
        "external_trust_required": True,
        "components": (
            "subscriber_authority",
            "credential_authority",
            "telecom_vault",
            "hsm_boundary",
            "profile_factory",
            "rsp_core",
            "smdp_plus_candidate",
            "certificate_registry",
            "key_ceremony",
            "profile_recovery",
        ),
    },
    {
        "id": "C",
        "name": "Private Network & Radio",
        "owner": "OAP Infrastructure",
        "software_target": True,
        "external_trust_required": True,
        "components": (
            "private_mobile_core",
            "network_authentication",
            "policy_core",
            "session_core",
            "usage_core",
            "radio_zone_registry",
            "wifi_fabric",
            "public_bridge_boundary",
            "network_reconciliation",
            "network_evidence",
        ),
    },
)

EXTERNAL_GATES: tuple[str, ...] = (
    "gsma_compliance_and_production_pki",
    "sas_sm_accreditation",
    "certified_euicc_interoperability",
    "lawful_spectrum_authority",
    "public_numbering_authority",
    "public_network_interconnect",
)

EXECUTION_BOUNDARY: dict[str, bool] = {
    "production_profile_issuance_enabled": False,
    "production_smdp_plus_claimed": False,
    "radio_transmission_enabled": False,
    "public_number_issuance_enabled": False,
    "carrier_activation_enabled": False,
    "external_certification_claimed": False,
    "human_authority_required": True,
}


def validate() -> dict[str, Any]:
    ids = [route["id"] for route in ROUTES]
    errors: list[str] = []
    if ids != ["A", "B", "C"]:
        errors.append("Telecom sovereignty routes must remain A -> B -> C")
    if len(set(ids)) != 3:
        errors.append("Duplicate telecom sovereignty route")
    if any(
        value
        for key, value in EXECUTION_BOUNDARY.items()
        if key != "human_authority_required"
    ):
        errors.append("External telecom execution must remain fail-closed")
    if not EXECUTION_BOUNDARY["human_authority_required"]:
        errors.append("Human authority must remain required")
    return {
        "passed": not errors,
        "errors": errors,
        "route_count": len(ROUTES),
        "canonical_order": tuple(ids),
    }


def status() -> dict[str, Any]:
    """Return non-sensitive architecture status for Mission Control."""

    return {
        "system": "OAP Telecom Sovereignty",
        "path": "A -> B -> C",
        "single_stack": True,
        "routes": tuple(dict(route) for route in ROUTES),
        "external_gates": EXTERNAL_GATES,
        "execution": dict(EXECUTION_BOUNDARY),
        "validation": validate(),
        "truth_boundary": (
            "OAP can build the first-party software/control stack, but production "
            "carrier-profile trust, certified eUICC interoperability, licensed "
            "radio operation, public numbering and interconnect require their "
            "respective external authorisations or trust anchors."
        ),
    }
