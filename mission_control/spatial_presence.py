"""OAP Spatial Presence / Face Up Spatial software core.

This module implements the OAP-owned software path for volumetric telepresence across
current networks and future 6G research. It does not claim a deployed 6G network,
certified 7-21 GHz radio hardware, D-band/sub-THz hardware, or a production holographic
display unless real signed evidence is configured.

Permanent boundaries:
- explicit participant consent for capture
- session-scoped spatial representations, not covert biometric identity profiles
- raw camera/depth/LiDAR/RF data remains local where practical
- Matrix receives privacy-reduced presence state only
- no hidden-person tracking or through-wall personal surveillance
- no autonomous radio control
- Human Authority remains final
"""

from __future__ import annotations

import os
import secrets
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

SPATIAL_PRESENCE_REVISION = "2026-09-04-v1"
OAP_EXPERIMENTAL_CMWAVE_GHZ = (7.0, 21.0)
D_BAND_GHZ = (110.0, 170.0)
SUB_THz_GHZ = (90.0, 300.0)
MAX_ACTIVE_SESSIONS = 32

CAPTURE_ADAPTERS: tuple[dict[str, str], ...] = (
    {"id": "multi_view_rgbd", "name": "Multi-view RGB-D Capture", "role": "Fuse authorised multi-camera colour and depth views into geometry."},
    {"id": "lidar_depth", "name": "LiDAR / Depth Capture", "role": "Provide authorised geometry and depth samples for spatial reconstruction."},
    {"id": "monocular_fallback", "name": "Monocular Camera Fallback", "role": "Provide a lower-fidelity fallback when multi-view depth hardware is unavailable."},
    {"id": "isac_environment", "name": "ISAC Environment Context", "role": "Optionally contribute privacy-reduced environment context; never covert identity sensing."},
)

DISPLAY_ADAPTERS: tuple[dict[str, str], ...] = (
    {"id": "xr_headset", "name": "XR Headset / Smart Glasses", "role": "Render stereoscopic session-scoped spatial presence."},
    {"id": "light_field", "name": "Light-field Display", "role": "Render multi-view spatial presence without requiring a wearable."},
    {"id": "volumetric", "name": "Volumetric Display", "role": "Render supported volumetric geometry when compatible hardware exists."},
    {"id": "2d_fallback", "name": "2D Face Up Fallback", "role": "Keep the conversation usable on ordinary displays and weak networks."},
)

TRANSPORT_PATHS: tuple[dict[str, object], ...] = (
    {"id": "local_lan", "name": "Local LAN / Wi-Fi", "operational_today": True, "priority": 10},
    {"id": "fiber_edge", "name": "Fibre + OAP Edge", "operational_today": True, "priority": 9},
    {"id": "5g", "name": "5G / 5G-Advanced", "operational_today": True, "priority": 8},
    {"id": "mesh_d2d", "name": "Mesh / Device-to-Device", "operational_today": True, "priority": 6},
    {"id": "ntn", "name": "NTN / Satellite Fallback", "operational_today": True, "priority": 4},
    {"id": "oap_7_21_research", "name": "OAP 7-21 GHz Experimental Research", "operational_today": False, "priority": 3},
    {"id": "d_band_sub_thz_research", "name": "D-band / sub-THz Extreme-Capacity Research", "operational_today": False, "priority": 2},
)


@dataclass(frozen=True)
class SpatialSession:
    session_id: str
    participant_ref: str
    created_at: str
    display: str
    capture_adapter: str
    transport: str
    quality_profile: str
    semantic_compression: bool
    consent: bool
    raw_media_export: bool = False
    biometric_identity_profile: bool = False
    matrix_precise_location: bool = False


_ACTIVE_SESSIONS: dict[str, SpatialSession] = {}


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().casefold() in {"1", "true", "yes", "on"}


def _float(value: object, default: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if result >= 0 else default


def _choose_capture_adapter(requested: str) -> str:
    ids = {item["id"] for item in CAPTURE_ADAPTERS}
    clean = str(requested or "multi_view_rgbd").strip().casefold()
    if clean not in ids:
        raise ValueError("unsupported_capture_adapter")
    return clean


def _choose_display(requested: str) -> str:
    ids = {item["id"] for item in DISPLAY_ADAPTERS}
    clean = str(requested or "2d_fallback").strip().casefold()
    if clean not in ids:
        raise ValueError("unsupported_display_adapter")
    return clean


def semantic_compression_plan(*, available_mbps: float, latency_ms: float) -> dict[str, Any]:
    """Return a deterministic privacy-aware level-of-detail plan."""
    bandwidth = max(_float(available_mbps, 0.0), 0.0)
    latency = max(_float(latency_ms, 999.0), 0.0)
    if bandwidth >= 500 and latency <= 30:
        profile, geometry_hz, target_mbps = "spatial_ultra", 60, min(bandwidth * 0.65, 1200.0)
    elif bandwidth >= 100 and latency <= 80:
        profile, geometry_hz, target_mbps = "spatial_high", 30, min(bandwidth * 0.60, 300.0)
    elif bandwidth >= 25 and latency <= 150:
        profile, geometry_hz, target_mbps = "spatial_adaptive", 20, min(bandwidth * 0.55, 80.0)
    else:
        profile, geometry_hz, target_mbps = "face_up_2d_fallback", 0, min(max(bandwidth * 0.45, 0.5), 12.0)
    return {
        "profile": profile,
        "target_mbps": round(target_mbps, 2),
        "geometry_hz": geometry_hz,
        "face_hands_detail": "high" if geometry_hz else "2d_video",
        "body_detail": "medium" if geometry_hz else "2d_video",
        "background": "scene_graph_and_cache" if geometry_hz else "video_background",
        "static_environment_cache": bool(geometry_hz),
        "semantic_compression": True,
        "raw_point_cloud_required_end_to_end": False,
        "raw_biometric_profile_required": False,
    }


def choose_transport(*, available: tuple[str, ...] | list[str] = (), research_radio_evidence: bool = False) -> str:
    supplied = {str(item).strip().casefold() for item in available if str(item).strip()}
    if not supplied:
        supplied = {"local_lan", "fiber_edge", "5g"}
    ordered = sorted(TRANSPORT_PATHS, key=lambda item: int(item["priority"]), reverse=True)
    for item in ordered:
        identifier = str(item["id"])
        if identifier not in supplied:
            continue
        if not bool(item["operational_today"]) and not research_radio_evidence:
            continue
        return identifier
    return "2d_best_effort"


def create_session(payload: Mapping[str, object]) -> dict[str, Any]:
    if not bool(payload.get("consent")):
        raise PermissionError("spatial_capture_consent_required")
    participant_ref = str(payload.get("participant_ref") or "").strip()[:96]
    if not participant_ref:
        raise ValueError("participant_ref_required")
    display = _choose_display(str(payload.get("display") or "2d_fallback"))
    capture_adapter = _choose_capture_adapter(str(payload.get("capture_adapter") or "multi_view_rgbd"))
    bandwidth = _float(payload.get("available_mbps"), 25.0)
    latency = _float(payload.get("latency_ms"), 80.0)
    qos = semantic_compression_plan(available_mbps=bandwidth, latency_ms=latency)
    requested_paths = payload.get("available_transports") or ()
    if isinstance(requested_paths, (str, bytes)):
        requested_paths = (str(requested_paths),)
    if not isinstance(requested_paths, (tuple, list)):
        raise TypeError("available_transports_must_be_list")
    research_evidence = bool(payload.get("research_radio_evidence")) and _truthy_env("OAP_SPATIAL_RADIO_EVIDENCE")
    transport = choose_transport(available=[str(item) for item in requested_paths], research_radio_evidence=research_evidence)
    session = SpatialSession(
        session_id="fsp_" + secrets.token_hex(8),
        participant_ref=participant_ref,
        created_at=datetime.now(UTC).isoformat(),
        display=display,
        capture_adapter=capture_adapter,
        transport=transport,
        quality_profile=str(qos["profile"]),
        semantic_compression=True,
        consent=True,
    )
    _ACTIVE_SESSIONS[session.session_id] = session
    while len(_ACTIVE_SESSIONS) > MAX_ACTIVE_SESSIONS:
        _ACTIVE_SESSIONS.pop(next(iter(_ACTIVE_SESSIONS)), None)
    return {
        "accepted": True,
        "session": asdict(session),
        "qos": qos,
        "guardian_presence_passed": True,
        "raw_media_export": False,
        "raw_point_cloud_export": False,
        "biometric_identity_profile": False,
        "covert_tracking": False,
        "matrix_projection": {
            "event_type": "face_up_spatial_session",
            "session_id": session.session_id,
            "presence": "active",
            "quality_profile": session.quality_profile,
            "transport": session.transport,
            "precise_location": None,
            "raw_media": False,
            "biometric_identity": False,
        },
        "human_authority_final": True,
    }


def end_session(session_id: str) -> dict[str, Any]:
    clean = str(session_id or "").strip()
    existed = _ACTIVE_SESSIONS.pop(clean, None) is not None
    return {"ended": existed, "session_id": clean, "raw_media_persisted": False, "biometric_profile_persisted": False, "human_authority_final": True}


def spatial_presence_status() -> dict[str, Any]:
    capture_evidence = _truthy_env("OAP_SPATIAL_CAPTURE_EVIDENCE")
    display_evidence = _truthy_env("OAP_SPATIAL_DISPLAY_EVIDENCE")
    radio_evidence = _truthy_env("OAP_SPATIAL_RADIO_EVIDENCE")
    six_g_evidence = _truthy_env("OAP_6G_RADIO_EVIDENCE")
    return {
        "id": "spatial_presence",
        "name": "OAP Spatial Presence",
        "experience": "Face Up Spatial",
        "revision": SPATIAL_PRESENCE_REVISION,
        "mode": "software_ready_hardware_evidence_gated",
        "software_ready": True,
        "active_session_count": len(_ACTIVE_SESSIONS),
        "capture_adapters": CAPTURE_ADAPTERS,
        "display_adapters": DISPLAY_ADAPTERS,
        "transport_paths": TRANSPORT_PATHS,
        "pipeline": ("Authorised Spatial Capture", "Matrix Spatial Reconstruction", "OAP Edge Semantic Compression", "Guardian Presence", "Nexus Spatial Transport", "Face Up Spatial Render", "Oasis Presentation"),
        "semantic_compression_ready": True,
        "adaptive_qos_ready": True,
        "digital_twin_mode": "session_scoped_spatial_representation",
        "persistent_biometric_clone": False,
        "matrix_privacy_reduced_projection": True,
        "oap_experimental_cmwave_ghz": OAP_EXPERIMENTAL_CMWAVE_GHZ,
        "oap_7_21_is_internal_research_envelope": True,
        "oap_7_21_claimed_final_6g_standard": False,
        "d_band_ghz": D_BAND_GHZ,
        "sub_thz_research_ghz": SUB_THz_GHZ,
        "capture_hardware_proven": capture_evidence,
        "spatial_display_hardware_proven": display_evidence,
        "oap_7_21_radio_hardware_proven": radio_evidence,
        "live_6g_network_proven": six_g_evidence,
        "photonic_wireless_research_hook": True,
        "photonic_chip_owned_or_deployed_claim": False,
        "d_band_sub_thz_hardware_claim": False,
        "terabit_session_claim": False,
        "sub_millisecond_end_to_end_claim": False,
        "raw_media_export_default": False,
        "raw_point_cloud_export_default": False,
        "biometric_identity_profile": False,
        "hidden_person_tracking": False,
        "through_wall_person_tracking": False,
        "autonomous_radio_control": False,
        "external_provider_authority": False,
        "human_authority_final": True,
        "truth_boundary": "The Face Up Spatial software pipeline is implemented and can degrade to current 2D/5G/Wi-Fi/fibre paths. Actual volumetric capture/display hardware, OAP 7-21 GHz research radios, D-band/sub-THz radios and a live 6G network remain evidence-gated.",
    }
