"""SIKA / OAP OS identity alignment.

One spine:
Managed Identity -> Password -> Device/eSIM slot -> OAP OS -> Digital SoC -> Organism.

This module reports architecture truth only. It does not provision a carrier eSIM,
store passwords, claim physical silicon, or grant device authority.
"""
from __future__ import annotations

from typing import Any

from . import sovereign_digital_soc


def status() -> dict[str, Any]:
    soc = sovereign_digital_soc.digital_soc_contract()
    return {
        "identity": {
            "owner": "Managed Neon Auth",
            "password_stored_by_oap": False,
            "sign_in_path": "/enter-my-world",
            "founder_password_activation_path": "/activate-founder",
            "create_password_scope": "founder_activation_only",
        },
        "device": {
            "esim_slot_defined": True,
            "esim_profile_provisioned": False,
            "esim_is_authentication_factor": False,
            "carrier_profile_required": True,
            "device_identity_separate_from_password": True,
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
