"""SIKA bank-app / OAP OS alignment.

One bank-app spine:
SIKA app access -> bank-app security -> Device/eSIM slot -> OAP OS -> Digital SoC -> Organism.

This module does not touch Founder authentication, provision a carrier eSIM,
store passwords, claim physical silicon, or grant device authority.
"""
from __future__ import annotations

from typing import Any

from . import (
    sika_authenticated_owner_adapter,
    sika_device_binding_store,
    sovereign_digital_soc,
)


def status() -> dict[str, Any]:
    soc = sovereign_digital_soc.digital_soc_contract()
    return {
        "bank_app_security": {
            "scope": "SIKA bank app only",
            "founder_auth_touched": False,
            "founder_password_linked": False,
            "bank_app_password_software_ready": True,
            "bank_app_password_durable_store_ready": False,
            "device_binding_software_ready": True,
            "durable_device_binding_store_ready": sika_device_binding_store.readiness()["canonical_store_reused"],
            "authenticated_owner_bridge_ready": sika_authenticated_owner_adapter.readiness()["adapter_present"],
            "production_session_route_ready": False,
            "note": "software capability exists; production owner-session route and durable credential store remain missing",
        },
        "device": {
            "esim_slot_defined": True,
            "esim_profile_provisioned": False,
            "esim_is_authentication_factor": False,
            "carrier_profile_required": True,
            "device_identity_separate_from_bank_app_password": True,
        },
        "operating_system": {
            "name": "OAP OS",
            "generation": "Gen0 PWA",
            "online_software_shell": True,
            "native_android_os": False,
            "bootloader_change_required": False,
        },
        "digital_silicon": {
            "name": soc["name"],
            "status": soc["status"],
            "block_count": len(soc["blocks"]),
            "physical_chip_built": soc["physical_chip_built"],
            "rtl_implemented": soc["rtl_implemented"],
            "fpga_loaded": soc["fpga_loaded"],
            "cognitive_authority": soc["cognitive_authority"],
            "final_authority": soc["final_authority"],
        },
        "organism": {
            "single_brain": "SMI",
            "device_zone": True,
            "recovery_zone": True,
            "silicon_is_body_substrate_not_second_brain": True,
            "human_authority_final": True,
        },
        "aligned": True,
        "noise_removed": True,
    }
