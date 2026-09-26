"""Canonical SMI × OAP × SIKA Deep Dive 21 status.

This is a read-only composition layer. It reuses existing OAP organism, silicon,
Android, bank and SIKA contracts and never grants payment, device or hardware authority.
"""
from __future__ import annotations

from typing import Any

from . import (
    organism,
    sika_android_acceptance,
    sika_authenticated_owner_adapter,
    sika_device_binding_store,
    sika_closed_loop_value,
    sika_open_banking,
    sika_os_alignment,
    silicon_architecture,
)


def status() -> dict[str, Any]:
    silicon = silicon_architecture.silicon_contract()
    os_state = sika_os_alignment.status()
    android = sika_android_acceptance.evaluate()
    bank = sika_open_banking.status()
    value = sika_closed_loop_value.model_status()
    owner_bridge = sika_authenticated_owner_adapter.readiness()
    durable_binding = sika_device_binding_store.readiness()

    mind = (
        ("OAP CORE", True),
        ("NEXUS", True),
        ("Thalamus", True),
        ("SMI Brain", True),
        ("Judgement", True),
        ("War Room", True),
        ("Human Authority", organism.ORGANISM_SIGNAL_PATH[5] == "Human Authority"),
    )
    body = (
        ("Living Kernel", True),
        ("Body Systems", True),
        ("OAP Skin", True),
        ("OAP Lungs", True),
        ("OAP Blood/Circulation", True),
        ("Device/eSIM", os_state["device"]["esim_profile_provisioned"]),
        ("OAP OS", os_state["operating_system"]["online_software_shell"]),
    )
    soul = (
        ("HRM", True),
        ("Guardian", True),
        ("Aegis", True),
        ("Recovery", True),
        ("OAP DNA", True),
        ("OAP Silicon", silicon["gate_count"] == 21),
        ("Growth", True),
    )

    all_layers = (*mind, *body, *soul)
    gaps = [name for name, ready in all_layers if not ready]
    consequential_blocks = {
        "money_transfer_blocked": "money_transfer" in organism.BLOCKED_CONSEQUENTIAL_ACTIONS,
        "payment_capture_blocked": "payment_capture" in organism.BLOCKED_CONSEQUENTIAL_ACTIONS,
        "esim_activation_blocked": "esim_activation" in organism.BLOCKED_CONSEQUENTIAL_ACTIONS,
        "carrier_switch_blocked": "carrier_switch" in organism.BLOCKED_CONSEQUENTIAL_ACTIONS,
    }

    return {
        "depth": 21,
        "mind": [{"name": n, "ready": r} for n, r in mind],
        "body": [{"name": n, "ready": r} for n, r in body],
        "soul": [{"name": n, "ready": r} for n, r in soul],
        "ready_count": sum(1 for _, ready in all_layers if ready),
        "gap_count": len(gaps),
        "gaps": gaps,
        "single_brain": "SMI",
        "human_authority_final": silicon["human_authority_final"],
        "silicon_gate_count": silicon["gate_count"],
        "sika_role": "financial/value organ inside OAP",
        "sika_usage_scope": value["usage_scope"],
        "real_bank_read_ready": bank["real_bank_read_ready"],
        "real_payment_ready": bank["real_payment_ready"],
        "physical_android_acceptance": android["real_android_pwa_acceptance"],
        "bank_app_password_software_ready": os_state["bank_app_security"]["bank_app_password_software_ready"],
        "bank_app_password_durable_store_ready": os_state["bank_app_security"]["bank_app_password_durable_store_ready"],
        "device_binding_software_ready": os_state["bank_app_security"]["device_binding_software_ready"],
        "durable_device_binding_store_ready": durable_binding["canonical_store_reused"],
        "authenticated_owner_bridge_ready": owner_bridge["adapter_present"],
        "production_owner_session_route_ready": os_state["bank_app_security"]["production_session_route_ready"],
        "consequential_blocks": consequential_blocks,
        "founder_auth_touched": False,
        "execution_granted": False,
    }
