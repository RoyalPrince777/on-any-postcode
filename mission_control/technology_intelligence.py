"""Technology Intelligence specialist capability for SMI.

Technology Intelligence is a cross-system capability, not an Intelligence world,
second brain, telecom operator, infrastructure operator, or execution authority.
Future-radio and spatial-presence claims remain fail-closed until real hardware and
runtime evidence exists.
"""

from __future__ import annotations

from typing import Any

from .connectivity_runtime import connectivity_runtime_status
from .humanitarian_connectivity import humanitarian_connectivity_status
from .infrastructure_intelligence import infrastructure_intelligence_status
from .international_humanitarian_intelligence import (
    international_humanitarian_intelligence_status,
)
from .isac_spatial_intelligence import isac_spatial_status
from .six_g_war_room import six_g_war_room_status
from .spatial_presence import spatial_presence_status

CONNECTIVITY_CAPABILITIES: tuple[dict[str, Any], ...] = (
    {
        "id": "6g",
        "name": "6G Intelligence",
        "kind": "production_runtime_future_network_intelligence",
        "purpose": "Run real intelligence for IMT-2030/6G research, edge intelligence, integrated sensing, mobility and resilient communications while requiring signed radio evidence before network-readiness claims.",
    },
    {
        "id": "isac_spatial",
        "name": "OAP ISAC Spatial Intelligence",
        "kind": "local_first_integrated_sensing_communication",
        "purpose": "Turn authorised radio measurements into privacy-reduced positioning and environment intelligence while Guardian RF keeps raw signatures out of Matrix.",
    },
    {
        "id": "spatial_presence",
        "name": "OAP Spatial Presence / Face Up Spatial",
        "kind": "volumetric_telepresence_software",
        "purpose": "Coordinate authorised spatial capture, reconstruction, semantic compression, adaptive QoS, Guardian Presence, Nexus transport and XR/light-field/2D rendering with current-network fallback and future-radio evidence gates.",
    },
    {
        "id": "humanitarian_emergency",
        "name": "Humanitarian Connectivity Intelligence",
        "kind": "civilian_emergency_connectivity_child",
        "purpose": "Provide civilian life-safety communications support to International Humanitarian Intelligence.",
    },
    {"id": "5g_edge", "name": "5G & Edge Intelligence", "kind": "current_connectivity_context", "purpose": "Coordinate current mobile-network and edge-compute context."},
    {"id": "esim", "name": "eSIM Intelligence", "kind": "subscriber_connectivity_context", "purpose": "Understand eSIM capability and field-connectivity requirements."},
    {"id": "mesh_local", "name": "Mesh & Local Network Intelligence", "kind": "local_first_connectivity", "purpose": "Prefer resilient local and peer connectivity where appropriate."},
    {"id": "satellite", "name": "Satellite Connectivity Intelligence", "kind": "wide_area_connectivity_context", "purpose": "Reason about satellite connectivity as an optional resilient path."},
    {"id": "device_to_device", "name": "Device-to-Device Intelligence", "kind": "direct_connectivity_context", "purpose": "Model governed direct device communication and proximity links."},
    {"id": "network_resilience", "name": "Network Resilience Intelligence", "kind": "continuity_and_failover", "purpose": "Plan safe degraded modes, failover and recovery for connectivity."},
)

TECHNOLOGY_SECTIONS: tuple[dict[str, str], ...] = (
    {"id": "connectivity", "name": "Connectivity Intelligence", "purpose": "Networks, edge, device links, resilience and future connectivity."},
    {"id": "compute", "name": "Compute Intelligence", "purpose": "Local, edge and governed compute capability awareness."},
    {"id": "devices", "name": "Device Intelligence", "purpose": "Hardware capability, constraints and trusted-device context."},
    {"id": "systems", "name": "Systems Intelligence", "purpose": "Software, runtime and infrastructure interoperability context."},
    {"id": "infrastructure", "name": "Infrastructure Intelligence", "purpose": "First-party infrastructure health, dependency, continuity and recovery intelligence."},
)


def technology_intelligence_status() -> dict[str, Any]:
    ids = tuple(item["id"] for item in CONNECTIVITY_CAPABILITIES)
    section_ids = tuple(item["id"] for item in TECHNOLOGY_SECTIONS)
    runtime = connectivity_runtime_status()
    war_room = six_g_war_room_status()
    isac = isac_spatial_status()
    presence = spatial_presence_status()
    humanitarian = humanitarian_connectivity_status()
    international_humanitarian = international_humanitarian_intelligence_status()
    infrastructure_ai = infrastructure_intelligence_status()
    architecture_passed = (
        len(ids) == len(set(ids))
        and len(section_ids) == len(set(section_ids))
        and {"6g", "isac_spatial", "spatial_presence", "humanitarian_emergency"}.issubset(ids)
        and "connectivity" in section_ids
        and "infrastructure" in section_ids
        and infrastructure_ai["architecture_ready"] is True
        and infrastructure_ai["brain_count"] == 0
        and infrastructure_ai["intelligence_world_count_added"] == 0
        and infrastructure_ai["first_party_policy"]["external_authority_allowed"] is False
        and runtime["mode"] == "production"
        and runtime["demo_mode"] is False
        and war_room["mode"] == "production_evidence_review"
        and war_room["demo_mode"] is False
        and isac["software_ready"] is True
        and isac["guardian_rf_minimisation"] is True
        and isac["raw_rf_in_matrix"] is False
        and presence["software_ready"] is True
        and presence["matrix_privacy_reduced_projection"] is True
        and presence["biometric_identity_profile"] is False
        and presence["oap_7_21_claimed_final_6g_standard"] is False
        and humanitarian["mode"] == "civilian_emergency_production"
        and humanitarian["demo_mode"] is False
        and humanitarian["civilian_only"] is True
        and international_humanitarian["mode"] == "civilian_humanitarian_production"
        and international_humanitarian["architecture_ready"] is True
    )
    six_g = dict(next(item for item in CONNECTIVITY_CAPABILITIES if item["id"] == "6g"))
    six_g.update(
        {
            "runtime_ready": runtime["6g_intelligence_runtime_ready"],
            "testbed_ready": runtime["6g_testbed_ready"],
            "production_network_ready": runtime["6g_production_network_ready"],
            "imt_2030_standard_finalized": runtime["imt_2030_standard_finalized"],
            "war_room": war_room,
            "isac_spatial": isac,
            "spatial_presence": presence,
            "humanitarian_connectivity": humanitarian,
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
        "infrastructure": infrastructure_ai,
        "connectivity": {
            "id": "connectivity",
            "name": "Connectivity Intelligence",
            "capabilities": CONNECTIVITY_CAPABILITIES,
            "6g": six_g,
            "isac_spatial": isac,
            "spatial_presence": presence,
            "humanitarian": humanitarian,
            "runtime": runtime,
            "war_room": war_room,
            "local_first_preference": True,
            "fallback_required": True,
            "privacy_preserving_telemetry": True,
        },
        "isac_spatial_intelligence": isac,
        "spatial_presence_intelligence": presence,
        "face_up_spatial_software_ready": presence["software_ready"],
        "oap_experimental_cmwave_ghz": presence["oap_experimental_cmwave_ghz"],
        "oap_7_21_claimed_final_6g_standard": False,
        "6g_war_room": war_room,
        "international_humanitarian_intelligence": international_humanitarian,
        "international_humanitarian_connectivity": humanitarian,
        "humanitarian_parent": "International Humanitarian Intelligence",
        "6g_architecture_ready": True,
        "6g_intelligence_runtime_ready": runtime["6g_intelligence_runtime_ready"],
        "6g_testbed_ready": runtime["6g_testbed_ready"],
        "6g_production_network_ready": runtime["6g_production_network_ready"],
        "isac_software_ready": isac["software_ready"],
        "isac_physical_testbed_ready": isac["physical_testbed_ready"],
        "spatial_capture_hardware_proven": presence["capture_hardware_proven"],
        "spatial_display_hardware_proven": presence["spatial_display_hardware_proven"],
        "spatial_7_21_radio_hardware_proven": presence["oap_7_21_radio_hardware_proven"],
        "telecom_operator_claim": False,
        "infrastructure_operator_claim": False,
        "autonomous_esim_provisioning": False,
        "autonomous_radio_control": False,
        "network_execution_authority": False,
        "infrastructure_execution_authority": False,
        "independent_execute": False,
        "independent_approval": False,
        "can_execute": False,
        "human_authority_final": True,
        "truth_boundary": (
            "Technology Intelligence contains OAP-owned advisory software. Face Up Spatial can run "
            "through current network fallbacks, but volumetric hardware, 7-21 GHz research radio, "
            "D-band/sub-THz hardware and live 6G remain evidence-gated. The OAP 7-21 GHz range is an "
            "internal research envelope, not a claim about the final 6G standard."
        ),
    }
