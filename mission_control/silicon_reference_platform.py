"""Vendor-neutral Generation 1 hardware contract for OAP Silicon.

This module describes the minimum capabilities a dedicated OAP Home Node must
prove before it can be called an OAP Silicon Reference Platform v1 device. It
is intentionally read-only: it does not purchase hardware, flash firmware,
provision keys, alter boot configuration, or grant execution authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .silicon_architecture import (
    HUMAN_AUTHORITY_FINAL,
    INDEPENDENT_HARDWARE_AUTHORITY,
    LOCKED_DESIGN_PRINCIPLES,
    SILICON_MISSION,
    validate_silicon_contract,
)

PLATFORM_NAME = "OAP Silicon Reference Platform v1"
REFERENCE_GENERATION = 1
PLATFORM_STATUS = "SPECIFICATION_READY"
PHYSICAL_DEVICE_BUILT = False
PURCHASE_REQUIRED_BY_SPEC = False
VENDOR_LOCK_IN_ALLOWED = False

# Capability classes deliberately avoid selecting a vendor or product. A real
# bill of materials belongs to a later Human Authority-approved procurement
# decision after requirements, cost, availability and supply-chain evidence
# have been reviewed.
HARDWARE_CAPABILITY_CLASSES: tuple[dict[str, Any], ...] = (
    {
        "id": "compute",
        "name": "General Compute",
        "required": True,
        "requirements": (
            "64_bit_cpu",
            "hardware_virtual_memory",
            "thermal_telemetry",
            "sustained_background_operation",
        ),
    },
    {
        "id": "memory",
        "name": "Memory and Storage",
        "required": True,
        "requirements": (
            "minimum_4_gib_ram",
            "persistent_storage",
            "encrypted_storage_capable",
            "replaceable_or_recoverable_system_image",
        ),
    },
    {
        "id": "trust",
        "name": "Hardware Trust",
        "required": True,
        "requirements": (
            "verified_or_secure_boot_capable",
            "device_unique_key_storage",
            "signed_update_verification",
            "rollback_or_recovery_path",
        ),
    },
    {
        "id": "network",
        "name": "Network",
        "required": True,
        "requirements": (
            "ethernet_or_wifi",
            "encrypted_transport_capable",
            "local_network_operation",
            "outbound_connectivity_control",
        ),
    },
    {
        "id": "acceleration",
        "name": "AI and Media Acceleration",
        "required": False,
        "requirements": (
            "optional_npu_or_gpu",
            "optional_media_acceleration",
            "software_fallback_required",
        ),
    },
    {
        "id": "power",
        "name": "Power and Recovery",
        "required": True,
        "requirements": (
            "clean_shutdown_support",
            "power_loss_recovery",
            "watchdog_capable",
            "temperature_and_power_observability",
        ),
    },
    {
        "id": "io",
        "name": "Local I/O",
        "required": True,
        "requirements": (
            "local_console_or_recovery_access",
            "removable_recovery_media_or_equivalent",
            "usb_or_equivalent_service_interface",
        ),
    },
)

SOFTWARE_BASELINE = (
    "64_bit_linux",
    "python_runtime",
    "postgresql_client",
    "oap_home_node_worker",
    "oap_core",
    "smi_bounded_runtime",
    "guardian_policy",
    "hrm_receipts",
    "signed_update_verification",
)

TRUST_BOOT_SEQUENCE = (
    "Hardware Root",
    "Boot Firmware Verification",
    "Kernel Verification",
    "OAP Runtime Verification",
    "Guardian Policy Load",
    "OAP CORE Start",
    "SMI Bounded Runtime Start",
    "Home Node Heartbeat",
)

UPDATE_SEQUENCE = (
    "Human Authority selects revision",
    "Signature and provenance verified",
    "Compatibility checks pass",
    "Recovery point prepared",
    "Update staged",
    "Human Authority approves activation",
    "Node activates revision",
    "Health and heartbeat verified",
    "HRM records outcome",
)

RECOVERY_REQUIREMENTS = (
    "known_good_image",
    "local_recovery_access",
    "configuration_backup_without_secret_disclosure",
    "rollback_after_failed_activation",
    "fresh_heartbeat_after_recovery",
)

OBSERVABILITY_SIGNALS = (
    "device_identity_state",
    "boot_integrity_state",
    "software_revision",
    "worker_heartbeat_freshness",
    "cpu_load",
    "memory_pressure",
    "storage_health",
    "temperature",
    "power_state",
    "network_state",
    "guardian_state",
    "dead_letter_count",
)

CONSEQUENTIAL_HARDWARE_ACTIONS = (
    "firmware_activation",
    "trust_key_rotation",
    "boot_policy_change",
    "permission_change",
    "production_revision_activation",
    "network_policy_expansion",
    "device_factory_reset",
)

ACCEPTANCE_GATES: tuple[dict[str, Any], ...] = (
    {"id": "architecture", "proof": "canonical_silicon_contract_valid"},
    {"id": "boot", "proof": "verified_boot_chain_evidence"},
    {"id": "identity", "proof": "unique_device_identity_evidence"},
    {"id": "storage", "proof": "encrypted_storage_evidence"},
    {"id": "runtime", "proof": "oap_worker_ready_and_fresh"},
    {"id": "recovery", "proof": "tested_rollback_or_recovery"},
    {"id": "authority", "proof": "human_authority_boundary_verified"},
)


def validate_reference_platform_contract() -> None:
    """Fail closed if Generation 1 drifts outside the OAP Silicon doctrine."""

    validate_silicon_contract()
    if REFERENCE_GENERATION != 1:
        raise ValueError("Reference Platform v1 must remain Generation 1")
    if len(HARDWARE_CAPABILITY_CLASSES) != 7:
        raise ValueError("Reference Platform v1 must retain seven hardware capability classes")
    if len(ACCEPTANCE_GATES) != 7:
        raise ValueError("Reference Platform v1 must retain seven acceptance gates")
    if PHYSICAL_DEVICE_BUILT:
        raise ValueError("The specification must not claim a physical device has been built")
    if PURCHASE_REQUIRED_BY_SPEC:
        raise ValueError("The architecture specification may not force a purchase")
    if VENDOR_LOCK_IN_ALLOWED:
        raise ValueError("The reference platform must remain vendor-neutral")
    if not HUMAN_AUTHORITY_FINAL or INDEPENDENT_HARDWARE_AUTHORITY:
        raise ValueError("Human Authority must remain final over hardware")
    if LOCKED_DESIGN_PRINCIPLES[0] != "Human Authority above software.":
        raise ValueError("Human Authority hierarchy has drifted")


def reference_platform_contract() -> dict[str, Any]:
    """Return the immutable Generation 1 specification contract."""

    validate_reference_platform_contract()
    return {
        "name": PLATFORM_NAME,
        "generation": REFERENCE_GENERATION,
        "status": PLATFORM_STATUS,
        "mission": SILICON_MISSION,
        "physical_device_built": PHYSICAL_DEVICE_BUILT,
        "purchase_required": PURCHASE_REQUIRED_BY_SPEC,
        "vendor_lock_in": VENDOR_LOCK_IN_ALLOWED,
        "hardware_capability_classes": HARDWARE_CAPABILITY_CLASSES,
        "software_baseline": SOFTWARE_BASELINE,
        "trust_boot_sequence": TRUST_BOOT_SEQUENCE,
        "update_sequence": UPDATE_SEQUENCE,
        "recovery_requirements": RECOVERY_REQUIREMENTS,
        "observability_signals": OBSERVABILITY_SIGNALS,
        "consequential_hardware_actions": CONSEQUENTIAL_HARDWARE_ACTIONS,
        "acceptance_gates": ACCEPTANCE_GATES,
        "human_authority_final": HUMAN_AUTHORITY_FINAL,
    }


def assess_candidate(evidence: Mapping[str, bool]) -> dict[str, Any]:
    """Assess vendor-neutral evidence without touching or provisioning hardware."""

    validate_reference_platform_contract()
    results = tuple(
        {
            "gate": gate["id"],
            "proof": gate["proof"],
            "passed": evidence.get(gate["proof"]) is True,
        }
        for gate in ACCEPTANCE_GATES
    )
    passed = all(result["passed"] for result in results)
    return {
        "candidate_ready": passed,
        "gate_count": len(results),
        "passed_count": sum(1 for result in results if result["passed"]),
        "results": results,
        "human_authority_final": True,
        "activation_performed": False,
    }
