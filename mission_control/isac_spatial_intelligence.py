"""Founder-governed OAP ISAC spatial intelligence runtime.

The runtime is software-ready on ordinary OAP hosts but keeps all physical-radio
claims fail-closed until explicit over-the-air evidence is supplied. OpenAirInterface,
FlexRIC and O-RAN LLC E2SM are treated as replaceable adapters, not OAP authority.
"""

from __future__ import annotations

import os
from typing import Any, Mapping

from oap.isac import ISACSpatialService, SRSFrame

_SERVICE = ISACSpatialService()

SUPPORTED_ADAPTERS = (
    "oai_flexric_llc_e2sm",
    "oai_direct_srs",
    "generic_authorised_srs_json",
)
SUPPORTED_RADIO_PATHS = (
    "usrp",
    "liteon_oran_7_2",
    "benetel_oran_7_2",
)


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().casefold() in {"1", "true", "yes", "on"}


def _configured_adapter() -> str:
    value = os.environ.get("OAP_ISAC_ADAPTER", "").strip().casefold()
    return value if value in SUPPORTED_ADAPTERS else "unconfigured"


def ingest_authorised_payload(payload: Mapping[str, object]) -> dict[str, object]:
    """Ingest one explicitly authorised SRS frame into the local Matrix RF path."""

    frame = SRSFrame.from_payload(payload)
    result = _SERVICE.ingest(frame)
    return {
        "status": "accepted",
        "guardian_rf_passed": result["guardian_rf_passed"],
        "feature_dimension": result["feature_dimension"],
        "change_score": result["change_score"],
        "object_or_environment_change_detected": result[
            "object_or_environment_change_detected"
        ],
        "estimate": {
            "device_ref": result["estimate"].device_ref,
            "x_m": result["estimate"].x_m,
            "y_m": result["estimate"].y_m,
            "z_m": result["estimate"].z_m,
            "zone": result["estimate"].zone,
            "confidence": result["estimate"].confidence,
            "calibrated": result["estimate"].calibrated,
            "model": result["estimate"].model,
            "timestamp": result["estimate"].timestamp,
        },
        "matrix_event": {
            "event_type": result["matrix_event"].event_type,
            "device_ref": result["matrix_event"].device_ref,
            "zone": result["matrix_event"].zone,
            "x_m": result["matrix_event"].x_m,
            "y_m": result["matrix_event"].y_m,
            "z_m": result["matrix_event"].z_m,
            "confidence": result["matrix_event"].confidence,
            "timestamp": result["matrix_event"].timestamp,
            "source": result["matrix_event"].source,
            "source_kind": result["matrix_event"].source_kind,
            "raw_rf_included": False,
        },
    }


def add_authorised_calibration(payload: Mapping[str, object]) -> dict[str, object]:
    """Add one Human-Authority-supplied calibration observation in memory."""

    frame_payload = payload.get("frame")
    if not isinstance(frame_payload, Mapping):
        raise ValueError("calibration_frame_required")
    frame = SRSFrame.from_payload(frame_payload)
    point = _SERVICE.add_calibration_from_frame(
        frame,
        label=str(payload.get("label") or "calibration")[:80],
        x_m=float(payload.get("x_m") or 0.0),
        y_m=float(payload.get("y_m") or 0.0),
        z_m=float(payload.get("z_m") or 0.0),
        zone=str(payload.get("zone") or "")[:80],
    )
    return {
        "status": "calibration_added",
        "label": point.label,
        "zone": point.zone,
        "x_m": point.x_m,
        "y_m": point.y_m,
        "z_m": point.z_m,
        "calibration_points": _SERVICE.model.calibration_count,
        "model_trained": _SERVICE.model.trained,
        "persistent": False,
    }


def isac_spatial_status() -> dict[str, Any]:
    """Return truthful OAP ISAC software/testbed readiness."""

    snapshot = _SERVICE.snapshot()
    adapter = _configured_adapter()
    radio_evidence = _enabled("OAP_ISAC_RADIO_EVIDENCE")
    calibration_evidence = snapshot["model_trained"]
    accuracy_evidence = _enabled("OAP_ISAC_ACCURACY_EVIDENCE")
    return {
        "id": "isac_spatial",
        "name": "OAP ISAC Spatial Intelligence",
        "mode": "production_software_fail_closed_radio",
        "software_ready": True,
        "live_radio_connected": radio_evidence and adapter != "unconfigured",
        "adapter": adapter,
        "supported_adapters": SUPPORTED_ADAPTERS,
        "supported_radio_paths": SUPPORTED_RADIO_PATHS,
        "oai_compatible_ingestion_contract": True,
        "flexric_llc_e2sm_compatible_contract": True,
        "srs_iq_ingestion": True,
        "cir_feature_extraction": True,
        "fixed_feature_dimension": snapshot["feature_dimensions"],
        "local_positioning_model": True,
        "model_trained": calibration_evidence,
        "calibration_points": snapshot["calibration_points"],
        "environment_change_detection": True,
        "occupancy_heatmap": True,
        "collision_risk_analysis": True,
        "matrix_rf_events": True,
        "guardian_rf_minimisation": True,
        "raw_rf_in_matrix": False,
        "raw_rf_local_only": True,
        "biometric_identity": False,
        "covert_person_tracking": False,
        "through_wall_personal_surveillance": False,
        "accuracy_claim_certified": accuracy_evidence and radio_evidence and calibration_evidence,
        "centimetre_accuracy_claim": False,
        "sub_metre_accuracy_claim": False,
        "physical_testbed_ready": radio_evidence and adapter != "unconfigured",
        "radio_evidence_present": radio_evidence,
        "accuracy_evidence_present": accuracy_evidence,
        "dashboard": snapshot,
        "external_provider_authority": False,
        "autonomous_radio_control": False,
        "consequential_execution_authority": False,
        "guardian_required": True,
        "human_authority_final": True,
        "remaining_physical_gates": tuple(
            gate
            for gate, passed in (
                ("configure_oai_or_equivalent_radio_adapter", adapter != "unconfigured"),
                ("connect_authorised_over_the_air_radio_testbed", radio_evidence),
                ("collect_real_calibration_dataset", calibration_evidence),
                ("certify_measured_accuracy", accuracy_evidence),
            )
            if not passed
        ),
    }
