"""Technology Intelligence specialist capability for SMI.

Technology Intelligence is a cross-system capability, not an Intelligence world,
second brain, telecom operator, or execution authority. Connectivity Intelligence
sits beneath it and includes a governed 6G capability model alongside current and
fallback connectivity paths.
"""

from __future__ import annotations

from typing import Any


CONNECTIVITY_CAPABILITIES: tuple[dict[str, Any], ...] = (
    {
        "id": "6g",
        "name": "6G Intelligence",
        "kind": "future_connectivity_intelligence",
        "purpose": (
            "Research and reason about future 6G connectivity, edge intelligence, "
            "integrated sensing, mobility and resilient communications without "
            "claiming a production 6G network."
        ),
        "production_network_ready": False,
    },
    {
        "id": "5g_edge",
        "name": "5G & Edge Intelligence",
        "kind": "current_connectivity_context",
        "purpose": "Coordinate current mobile-network and edge-compute context.",
    },
    {
        "id": "esim",
        "name": "eSIM Intelligence",
        "kind": "subscriber_connectivity_context",
        "purpose": "Understand eSIM capability and field-connectivity requirements.",
    },
    {
        "id": "mesh_local",
        "name": "Mesh & Local Network Intelligence",
        "kind": "local_first_connectivity",
        "purpose": "Prefer resilient local and peer connectivity where appropriate.",
    },
    {
        "id": "satellite",
        "name": "Satellite Connectivity Intelligence",
        "kind": "wide_area_connectivity_context",
        "purpose": "Reason about satellite connectivity as an optional resilient path.",
    },
    {
        "id": "device_to_device",
        "name": "Device-to-Device Intelligence",
        "kind": "direct_connectivity_context",
        "purpose": "Model governed direct device communication and proximity links.",
    },
    {
        "id": "network_resilience",
        "name": "Network Resilience Intelligence",
        "kind": "continuity_and_failover",
        "purpose": "Plan safe degraded modes, failover and recovery for connectivity.",
    },
)


TECHNOLOGY_SECTIONS: tuple[dict[str, str], ...] = (
    {
        "id": "connectivity",
        "name": "Connectivity Intelligence",
        "purpose": "Networks, edge, device links, resilience and future connectivity.",
    },
    {
        "id": "compute",
        "name": "Compute Intelligence",
        "purpose": "Local, edge and governed compute capability awareness.",
    },
    {
        "id": "devices",
        "name": "Device Intelligence",
        "purpose": "Hardware capability, constraints and trusted-device context.",
    },
    {
        "id": "systems",
        "name": "Systems Intelligence",
        "purpose": "Software, runtime and infrastructure interoperability context.",
    },
)


def technology_intelligence_status() -> dict[str, Any]:
    """Return the bounded, read-only Technology Intelligence projection."""

    ids = tuple(item["id"] for item in CONNECTIVITY_CAPABILITIES)
    section_ids = tuple(item["id"] for item in TECHNOLOGY_SECTIONS)
    architecture_passed = (
        len(ids) == len(set(ids))
        and len(section_ids) == len(set(section_ids))
        and "6g" in ids
        and "connectivity" in section_ids
    )
    return {
        "id": "technology",
        "name": "Technology Intelligence",
        "kind": "cross_system_specialist_intelligence",
        "architecture_passed": architecture_passed,
        "brain_count": 0,
        "intelligence_world_count_added": 0,
        "sections": TECHNOLOGY_SECTIONS,
        "connectivity": {
            "id": "connectivity",
            "name": "Connectivity Intelligence",
            "capabilities": CONNECTIVITY_CAPABILITIES,
            "6g": next(item for item in CONNECTIVITY_CAPABILITIES if item["id"] == "6g"),
            "local_first_preference": True,
            "fallback_required": True,
            "privacy_preserving_telemetry": True,
        },
        "6g_architecture_ready": True,
        "6g_production_network_ready": False,
        "telecom_operator_claim": False,
        "autonomous_esim_provisioning": False,
        "autonomous_radio_control": False,
        "network_execution_authority": False,
        "independent_execute": False,
        "independent_approval": False,
        "can_execute": False,
        "human_authority_final": True,
    }
