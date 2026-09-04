"""Evidence-driven IMT-2030 / 6G War Room for SMI.

This module turns current production connectivity evidence into bounded planning,
readiness and red-team views. It never invents radio performance, controls a
network, provisions subscriber identities, or claims standardized 6G without proof.
"""

from __future__ import annotations

from typing import Any

from .connectivity_runtime import connectivity_runtime_status

IMT_2030_USAGE_SCENARIOS: tuple[dict[str, str], ...] = (
    {
        "id": "ic",
        "name": "Immersive Communication",
        "purpose": "Rich interactive media, XR and multi-sensory communication.",
    },
    {
        "id": "hrllc",
        "name": "Hyper Reliable and Low-Latency Communication",
        "purpose": "Safety- and mission-critical communication with stronger latency and reliability.",
    },
    {
        "id": "mc",
        "name": "Massive Communication",
        "purpose": "Very large populations of devices, sensors and low-power endpoints.",
    },
    {
        "id": "uc",
        "name": "Ubiquitous Connectivity",
        "purpose": "Coverage continuity across local, remote and underserved environments.",
    },
    {
        "id": "aiac",
        "name": "AI and Communication",
        "purpose": "Distributed AI, edge compute, model inference and compute orchestration.",
    },
    {
        "id": "isac",
        "name": "Integrated Sensing and Communication",
        "purpose": "Communication combined with positioning, sensing and environmental awareness.",
    },
)

IMT_2030_CAPABILITIES: tuple[dict[str, str], ...] = (
    {"id": "peak_data_rate", "name": "Peak Data Rate", "evidence": "radio performance telemetry"},
    {"id": "user_data_rate", "name": "User Experienced Data Rate", "evidence": "end-user performance telemetry"},
    {"id": "spectrum_efficiency", "name": "Spectrum Efficiency", "evidence": "radio and spectrum measurement"},
    {"id": "area_traffic_capacity", "name": "Area Traffic Capacity", "evidence": "area-level radio traffic measurement"},
    {"id": "connection_density", "name": "Connection Density", "evidence": "authenticated device-density measurement"},
    {"id": "mobility", "name": "Mobility", "evidence": "mobility and handover measurement"},
    {"id": "latency", "name": "Latency", "evidence": "radio and end-to-end latency telemetry"},
    {"id": "reliability", "name": "Reliability", "evidence": "packet/session reliability telemetry"},
    {"id": "security_resilience", "name": "Security, Privacy and Resilience", "evidence": "security and resilience proof"},
    {"id": "coverage", "name": "Coverage", "evidence": "verified coverage measurement"},
    {"id": "positioning", "name": "Positioning", "evidence": "positioning accuracy telemetry"},
    {"id": "sensing", "name": "Sensing", "evidence": "authorized sensing proof"},
    {"id": "ai_integration", "name": "AI Integration", "evidence": "edge/distributed AI runtime proof"},
    {"id": "sustainability", "name": "Sustainability", "evidence": "energy/resource measurement"},
    {"id": "interoperability", "name": "Interoperability", "evidence": "multi-system interoperability proof"},
)

PRODUCTION_FEATURES: tuple[dict[str, str], ...] = (
    {
        "id": "runtime_observation",
        "name": "Live Connectivity Observation",
        "purpose": "Observe current host connectivity without simulated success or external probe dependency.",
    },
    {
        "id": "network_selection",
        "name": "Network Selection Advisor",
        "purpose": "Recommend whether to keep, degrade or fail over from the currently observed path.",
    },
    {
        "id": "resilience",
        "name": "Resilience Planner",
        "purpose": "Detect single-path dependency and prepare bounded fallback requirements.",
    },
    {
        "id": "edge_ai",
        "name": "Edge AI Coordinator",
        "purpose": "Prefer local/edge intelligence and keep provider authority outside the network control path.",
    },
    {
        "id": "signed_radio_evidence",
        "name": "Signed Radio Evidence",
        "purpose": "Verify fresh local radio evidence before testbed or production-radio claims.",
    },
    {
        "id": "testbed_gate",
        "name": "Pre-standard 6G Testbed Gate",
        "purpose": "Recognize an authorized experimental IMT-2030/6G environment only from verified evidence.",
    },
    {
        "id": "standards_gate",
        "name": "Standardized 6G Production Gate",
        "purpose": "Keep production 6G false until standards and production radio evidence both pass.",
    },
    {
        "id": "privacy",
        "name": "Privacy-Preserving Telemetry",
        "purpose": "Expose readiness state without autonomous subscriber, radio or location control.",
    },
)

RED_TEAM_SCENARIOS: tuple[dict[str, str], ...] = (
    {
        "id": "false_6g_label",
        "risk": "A 5G, Wi-Fi or experimental path is labelled production 6G.",
        "mitigation": "Require signed radio class, production attestation and finalized standards.",
    },
    {
        "id": "stale_evidence",
        "risk": "Old radio evidence survives after topology or service changes.",
        "mitigation": "Reject evidence outside the freshness window and future-clock skew bound.",
    },
    {
        "id": "forged_evidence",
        "risk": "A local process fabricates radio readiness.",
        "mitigation": "Verify HMAC signature and require an identified collector in an authorized environment.",
    },
    {
        "id": "single_path_failure",
        "risk": "One access path fails and takes the service offline.",
        "mitigation": "Treat fallback as mandatory and keep degraded-mode planning visible.",
    },
    {
        "id": "edge_compromise",
        "risk": "An edge AI/provider gains hidden execution or network authority.",
        "mitigation": "Keep providers advisory, egress governed and network execution disabled.",
    },
    {
        "id": "privacy_leak",
        "risk": "Sensing, mobility or subscriber telemetry exposes people unnecessarily.",
        "mitigation": "Minimize telemetry, require authorization and separate intelligence from radio control.",
    },
    {
        "id": "standards_drift",
        "risk": "A pre-standard design is treated as final IMT-2030 behavior.",
        "mitigation": "Version standards evidence and fail closed until the finalized standard is explicitly attested.",
    },
)


def _feature_matrix(runtime: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    host = runtime["host"]
    radio = runtime["radio_evidence"]
    connected = bool(host["runtime_connectivity_present"])
    signed = bool(radio["valid"])
    testbed = bool(runtime["6g_testbed_ready"])
    production_6g = bool(runtime["6g_production_network_ready"])

    readiness = {
        "runtime_observation": connected,
        "network_selection": connected,
        "resilience": connected,
        "edge_ai": connected,
        "signed_radio_evidence": signed,
        "testbed_gate": testbed,
        "standards_gate": production_6g,
        "privacy": True,
    }
    blockers = {
        "runtime_observation": "current host connectivity is not proven",
        "network_selection": "no current routable host path is proven",
        "resilience": "no current routable host path is proven",
        "edge_ai": "no current routable host path is proven",
        "signed_radio_evidence": str(radio.get("reason") or "radio evidence missing"),
        "testbed_gate": "authorized fresh experimental radio evidence is missing",
        "standards_gate": "final IMT-2030 standard plus production radio evidence is required",
        "privacy": "",
    }
    return tuple(
        {
            **feature,
            "ready": readiness[feature["id"]],
            "blocker": "" if readiness[feature["id"]] else blockers[feature["id"]],
            "can_execute": False,
        }
        for feature in PRODUCTION_FEATURES
    )


def _capability_matrix(runtime: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    radio = runtime["radio_evidence"]
    radio_verified = bool(radio["valid"])
    security_runtime = bool(runtime["production_software_ready"])
    return tuple(
        {
            **capability,
            "architecture_ready": True,
            "runtime_evidence_present": (
                security_runtime
                if capability["id"] == "security_resilience"
                else radio_verified
            ),
            "standards_certified": bool(runtime["6g_production_network_ready"]),
            "truth_boundary": (
                "Runtime evidence does not imply the IMT-2030 target is achieved; "
                "scenario-specific measured proof is still required."
            ),
        }
        for capability in IMT_2030_CAPABILITIES
    )


def _scenario_matrix(runtime: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    connected = bool(runtime["production_software_ready"])
    testbed = bool(runtime["6g_testbed_ready"])
    production_6g = bool(runtime["6g_production_network_ready"])
    return tuple(
        {
            **scenario,
            "production_software_ready": connected,
            "testbed_ready": testbed,
            "standardized_6g_ready": production_6g,
            "state": (
                "standardized_6g"
                if production_6g
                else "verified_testbed"
                if testbed
                else "production_intelligence"
                if connected
                else "blocked"
            ),
            "next_gate": (
                "Collect scenario-specific signed radio measurements and evaluate them "
                "against the applicable IMT-2030 requirements."
            ),
        }
        for scenario in IMT_2030_USAGE_SCENARIOS
    )


def six_g_war_room_status() -> dict[str, Any]:
    """Return a live, read-only 6G War Room evidence package."""

    runtime = connectivity_runtime_status()
    feature_matrix = _feature_matrix(runtime)
    ready_features = sum(1 for feature in feature_matrix if feature["ready"])
    blockers = tuple(feature["blocker"] for feature in feature_matrix if feature["blocker"])
    return {
        "id": "6g_war_room",
        "name": "6G War Room",
        "mode": "production_evidence_review",
        "demo_mode": False,
        "simulation_success_allowed": False,
        "triggered": True,
        "runtime": runtime,
        "feature_matrix": feature_matrix,
        "ready_feature_count": ready_features,
        "feature_count": len(feature_matrix),
        "usage_scenarios": _scenario_matrix(runtime),
        "capabilities": _capability_matrix(runtime),
        "red_team": RED_TEAM_SCENARIOS,
        "blockers": tuple(dict.fromkeys(blockers)),
        "network_selection_recommendation": (
            "Keep the current observed route and require a second independent fallback path."
            if runtime["production_software_ready"]
            else "Do not progress network-dependent work until a routable production path is observed."
        ),
        "build_order": (
            "1. production observation + signed telemetry",
            "2. multi-access/fallback evidence",
            "3. local edge AI and application enablement",
            "4. authorized IMT-2030 testbed evidence",
            "5. scenario-specific radio performance evaluation",
            "6. standardized IMT-2030 production certification when standards finalize",
        ),
        "decision_authority": False,
        "network_execution_authority": False,
        "autonomous_radio_control": False,
        "autonomous_esim_provisioning": False,
        "human_authority_final": True,
        "truth_boundary": (
            "This War Room is live production intelligence. It can verify runtime and testbed "
            "evidence, but it cannot turn a non-6G transport into standardized 6G or invent "
            "missing radio measurements."
        ),
    }
