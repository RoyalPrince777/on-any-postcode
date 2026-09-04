"""Technology Intelligence specialist capability for SMI.

Technology Intelligence is a cross-system capability, not an Intelligence world,
second brain, telecom operator, or execution authority. Connectivity Intelligence
runs as production software with real runtime evidence and keeps 6G network claims
fail-closed until actual signed radio proof and finalized standards exist.
"""

from __future__ import annotations

from typing import Any

from .connectivity_runtime import connectivity_runtime_status
from .humanitarian_connectivity import humanitarian_connectivity_status
from .six_g_war_room import six_g_war_room_status

CONNECTIVITY_CAPABILITIES: tuple[dict[str, Any], ...] = (
    {
        "id": "6g",
        "name": "6G Intelligence",
        "kind": "production_runtime_future_network_intelligence",
        "purpose": (
            "Run real production intelligence for IMT-2030/6G research, edge "
            "intelligence, integrated sensing, mobility and resilient communications "
            "while requiring signed radio evidence before any network-readiness claim."
        ),
    },
    {
        "id": "humanitarian_emergency",
        "name": "International Humanitarian Connectivity Intelligence",
        "kind": "civilian_emergency_connectivity",
        "purpose": (
            "Prioritize civilian life-safety communication, medical needs, public warnings, "
            "family reunification, essential aid and accessible communications during crises."
        ),
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
    """Return production Technology Intelligence status without simulated success."""

    ids = tuple(item["id"] for item in CONNECTIVITY_CAPABILITIES)
    section_ids = tuple(item["id"] for item in TECHNOLOGY_SECTIONS)
    runtime = connectivity_runtime_status()
    war_room = six_g_war_room_status()
    humanitarian = humanitarian_connectivity_status()
    architecture_passed = (
        len(ids) == len(set(ids))
        and len(section_ids) == len(set(section_ids))
        and "6g" in ids
        and "humanitarian_emergency" in ids
        and "connectivity" in section_ids
        and runtime["mode"] == "production"
        and runtime["demo_mode"] is False
        and war_room["mode"] == "production_evidence_review"
        and war_room["demo_mode"] is False
        and humanitarian["mode"] == "civilian_emergency_production"
        and humanitarian["demo_mode"] is False
        and humanitarian["civilian_only"] is True
    )
    six_g = dict(next(item for item in CONNECTIVITY_CAPABILITIES if item["id"] == "6g"))
    six_g.update(
        {
            "runtime_ready": runtime["6g_intelligence_runtime_ready"],
            "testbed_ready": runtime["6g_testbed_ready"],
            "production_network_ready": runtime["6g_production_network_ready"],
            "imt_2030_standard_finalized": runtime["imt_2030_standard_finalized"],
            "war_room": war_room,
            "humanitarian": humanitarian,
        }
    )
    return {
        "id": "technology",
        "name": "Technology Intelligence",
        "kind": "cross_system_specialist_intelligence",
        "architecture_passed": architecture_passed,
        "runtime_mode": runtime["mode"],
        "demo_mode": runtime["demo_mode"],
        "production_software_ready": runtime["production_software_ready"],
        "brain_count": 0,
        "intelligence_world_count_added": 0,
        "sections": TECHNOLOGY_SECTIONS,
        "connectivity": {
            "id": "connectivity",
            "name": "Connectivity Intelligence",
            "capabilities": CONNECTIVITY_CAPABILITIES,
            "6g": six_g,
            "humanitarian": humanitarian,
            "runtime": runtime,
            "war_room": war_room,
            "local_first_preference": True,
            "fallback_required": True,
            "privacy_preserving_telemetry": True,
        },
        "6g_war_room": war_room,
        "international_humanitarian_connectivity": humanitarian,
        "6g_architecture_ready": True,
        "6g_intelligence_runtime_ready": runtime["6g_intelligence_runtime_ready"],
        "6g_testbed_ready": runtime["6g_testbed_ready"],
        "6g_production_network_ready": runtime["6g_production_network_ready"],
        "telecom_operator_claim": False,
        "autonomous_esim_provisioning": False,
        "autonomous_radio_control": False,
        "network_execution_authority": False,
        "independent_execute": False,
        "independent_approval": False,
        "can_execute": False,
        "human_authority_final": True,
        "truth_boundary": (
            "Connectivity Intelligence, its 6G War Room and humanitarian emergency layer are "
            "production software, not demos. Humanitarian mode is civilian-only. A live 6G "
            "network still requires signed radio evidence and finalized IMT-2030 standards."
        ),
    }
