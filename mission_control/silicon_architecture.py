"""Canonical, read-only architecture contract for OAP Silicon.

OAP Silicon is the hardware sovereignty layer beneath the OAP Digital Organism.
This module defines constitutional boundaries and reference-platform structure.
It does not control hardware, provision infrastructure, flash firmware, or grant
execution authority.
"""

from __future__ import annotations

from typing import Any

SILICON_MISSION = "Own the intelligence architecture before owning the transistor."

LOCKED_DESIGN_PRINCIPLES = (
    "Human Authority above software.",
    "Software above hardware execution.",
    "Hardware proves, isolates and enforces — it does not rule.",
)

AUTHORITY_CHAIN = (
    "Human Authority",
    "OAP Software",
    "Guardian Policy",
    "Hardware Execution",
)

SILICON_STACK = (
    "OAP Silicon",
    "OAP Home Node",
    "OAP CORE",
    "NEXUS",
    "Thalamus",
    "SMI Brain",
    "Judgement",
    "Human Authority",
    "Living Kernel",
    "Digital Organs",
    "HRM",
)

SILICON_LAYERS: tuple[dict[str, Any], ...] = (
    {
        "id": "root",
        "name": "OAP Root",
        "responsibility": "Establish device trust before higher layers run.",
        "capabilities": (
            "secure_boot",
            "device_identity",
            "signed_firmware",
            "tamper_evidence",
            "key_storage",
            "rollback_protection",
        ),
    },
    {
        "id": "compute",
        "name": "OAP Compute Fabric",
        "responsibility": "Provide bounded heterogeneous compute for OAP workloads.",
        "capabilities": ("cpu", "gpu", "npu", "dsp", "optional_fpga"),
    },
    {
        "id": "memory",
        "name": "OAP Memory Fabric",
        "responsibility": "Isolate and protect volatile and persistent OAP state.",
        "capabilities": (
            "secure_memory_regions",
            "encrypted_storage",
            "hrm_integrity",
            "context_cache",
            "organ_isolation",
        ),
    },
    {
        "id": "nexus",
        "name": "OAP NEXUS Fabric",
        "responsibility": "Carry typed capability-scoped messages between components.",
        "capabilities": (
            "typed_messages",
            "capability_checks",
            "bounded_interconnect",
        ),
    },
    {
        "id": "sense",
        "name": "OAP Sense Fabric",
        "responsibility": "Expose consented, scoped and auditable sensor access.",
        "capabilities": (
            "camera",
            "microphone",
            "location",
            "motion",
            "environment",
            "network_state",
            "power_telemetry",
        ),
    },
    {
        "id": "network",
        "name": "OAP Network Fabric",
        "responsibility": "Provide encrypted local-first connectivity between nodes.",
        "capabilities": (
            "wifi",
            "ethernet",
            "bluetooth",
            "cellular_later",
            "peer_to_peer",
            "mesh_capability",
        ),
    },
    {
        "id": "guardian",
        "name": "OAP Guardian Fabric",
        "responsibility": "Enforce policy boundaries below application software.",
        "capabilities": (
            "secret_isolation",
            "signed_workload_enforcement",
            "domain_separation",
            "consequence_locks",
            "security_receipts",
        ),
    },
)

EXECUTION_ZONES = (
    "Public Zone",
    "Private Zone",
    "SMI Zone",
    "HRM Zone",
    "Guardian Zone",
    "Device Zone",
    "Recovery Zone",
)

SILICON_GATES = {
    "hardware_trust": (
        "secure_boot",
        "device_identity",
        "integrity",
        "memory_protection",
        "network_trust",
        "sensor_consent",
        "recovery_integrity",
    ),
    "intelligence": (
        "input_validity",
        "model_provenance",
        "context_integrity",
        "confidence",
        "policy",
        "consequence_classification",
        "explainability",
    ),
    "human_authority": (
        "identity",
        "permission",
        "intent",
        "scope",
        "approval",
        "receipt",
        "audit",
    ),
}

BLOCKED_HARDWARE_AUTONOMY = (
    "approve_recommendation",
    "self_promote",
    "self_apply_improvement",
    "deploy",
    "publish_external",
    "payment_capture",
    "money_transfer",
    "royalty_payout",
    "driver_dispatch",
    "permission_change",
    "role_change",
    "production_migration",
    "parcel_carrier_handoff",
    "physical_post_office_activation",
    "esim_activation",
    "carrier_switch",
    "public_precise_tracking",
)

REFERENCE_GENERATIONS: tuple[dict[str, Any], ...] = (
    {
        "generation": 0,
        "name": "Current Home Node",
        "platform": "Android/Termux on existing silicon",
        "status": "ACTIVE_REFERENCE",
    },
    {
        "generation": 1,
        "name": "Dedicated Home Node",
        "platform": "Off-the-shelf ARM or RISC-V mini computer",
        "status": "PLANNED",
    },
    {
        "generation": 2,
        "name": "OAP Home Node Appliance",
        "platform": "Reference device with secure element and AI accelerator",
        "status": "FUTURE",
    },
    {
        "generation": 3,
        "name": "FPGA Reference",
        "platform": "Programmable OAP trust and acceleration prototype",
        "status": "FUTURE",
    },
    {
        "generation": 4,
        "name": "OAP Compute Module",
        "platform": "OAP reference board and modular hardware specification",
        "status": "FUTURE",
    },
    {
        "generation": 5,
        "name": "OAP Sovereign SoC",
        "platform": "Optional custom RISC-V/ASIC if scale justifies fabrication",
        "status": "FUTURE_OPTION",
    },
)

SOVEREIGN_SOC_BLOCKS = (
    "CPU Cluster",
    "NPU",
    "GPU",
    "Secure Enclave",
    "HRM Integrity Engine",
    "Guardian Policy Engine",
    "NEXUS Interconnect",
    "Media DSP",
    "Network Accelerator",
    "Encrypted Memory Controller",
    "Secure Storage Controller",
    "Sensor Hub",
    "Power and Thermal Controller",
)

INDEPENDENT_HARDWARE_AUTHORITY = False
HUMAN_AUTHORITY_FINAL = True
PHYSICAL_CHIP_REQUIRED_NOW = False


def validate_silicon_contract() -> None:
    """Fail closed if a constitutional silicon invariant is changed."""

    if len(SILICON_LAYERS) != 7:
        raise ValueError("OAP Silicon must retain exactly seven architecture layers")
    if len(EXECUTION_ZONES) != 7:
        raise ValueError("OAP Silicon must retain exactly seven execution zones")
    if set(SILICON_GATES) != {"hardware_trust", "intelligence", "human_authority"}:
        raise ValueError("OAP Silicon must retain the three canonical gate families")
    if any(len(gates) != 7 for gates in SILICON_GATES.values()):
        raise ValueError("Each OAP Silicon gate family must contain exactly seven gates")
    if sum(len(gates) for gates in SILICON_GATES.values()) != 21:
        raise ValueError("OAP Silicon must retain the 7x3 = 21 gate contract")
    if AUTHORITY_CHAIN[0] != "Human Authority":
        raise ValueError("Human Authority must remain above software and hardware")
    if AUTHORITY_CHAIN[-1] != "Hardware Execution":
        raise ValueError("Hardware execution must remain the lowest authority layer")
    if not HUMAN_AUTHORITY_FINAL or INDEPENDENT_HARDWARE_AUTHORITY:
        raise ValueError("Hardware may not become an independent authority")
    if PHYSICAL_CHIP_REQUIRED_NOW:
        raise ValueError("The reference architecture must not require custom silicon now")


def silicon_contract() -> dict[str, Any]:
    """Return the canonical read-only OAP Silicon architecture contract."""

    validate_silicon_contract()
    return {
        "mission": SILICON_MISSION,
        "design_principles": LOCKED_DESIGN_PRINCIPLES,
        "authority_chain": AUTHORITY_CHAIN,
        "stack": SILICON_STACK,
        "layers": SILICON_LAYERS,
        "execution_zones": EXECUTION_ZONES,
        "gates": SILICON_GATES,
        "gate_count": 21,
        "blocked_hardware_autonomy": BLOCKED_HARDWARE_AUTONOMY,
        "reference_generations": REFERENCE_GENERATIONS,
        "future_soc_blocks": SOVEREIGN_SOC_BLOCKS,
        "human_authority_final": HUMAN_AUTHORITY_FINAL,
        "independent_hardware_authority": INDEPENDENT_HARDWARE_AUTHORITY,
        "physical_chip_required_now": PHYSICAL_CHIP_REQUIRED_NOW,
    }
