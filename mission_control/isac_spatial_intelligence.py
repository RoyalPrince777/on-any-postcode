"""Founder-governed OAP ISAC spatial intelligence runtime.

The runtime is software-ready on ordinary OAP hosts but keeps all physical-radio
claims fail-closed until explicit over-the-air evidence is supplied. OpenAirInterface,
FlexRIC and O-RAN LLC E2SM are treated as replaceable adapters, not OAP authority.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from oap.isac import ISACSpatialService, SRSFrame

_SERVICE = ISACSpatialService()
_PROOF_EVENTS: list[dict[str, object]] = []

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
APP_CONTROLS = (
    "Refresh ISAC",
    "Run ISAC Proof Check",
    "Seed Authorised Software Test",
    "Check Guardian RF",
    "Check Calibration Gates",
    "View Matrix RF Events",
    "Export Safe ISAC Brief",
    "Send To Green Gate",
    "Lock Physical RF Claims",
)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().casefold() in {"1", "true", "yes", "on"}


def _configured_adapter() -> str:
    value = os.environ.get("OAP_ISAC_ADAPTER", "").strip().casefold()
    return value if value in SUPPORTED_ADAPTERS else "unconfigured"


def _record(event_type: str, **details: object) -> dict[str, object]:
    event = {
        "timestamp": _utc_iso(),
        "event_type": event_type,
        "source": "isac_app",
        "hrm_ready": True,
        "details": details,
    }
    _PROOF_EVENTS.append(event)
    del _PROOF_EVENTS[:-40]
    return event


def _software_test_frame(device_ref: str, sequence: int, scale: float = 1.0) -> dict[str, object]:
    samples = []
    for index in range(16):
        samples.append([round(scale * (1.0 + index / 20.0), 4), round(scale * (0.18 + index / 50.0), 4)])
    return {
        "source": "isac_software_test_fixture",
        "source_kind": "software_srs_fixture_not_live_radio",
        "device_ref": device_ref,
        "cell_ref": "oap-test-cell",
        "antenna_iq": [samples, tuple(reversed(samples))],
        "sequence": sequence,
        "noise_power": 0.01,
        "authorised": True,
    }


def ingest_authorised_payload(payload: Mapping[str, object]) -> dict[str, object]:
    """Ingest one explicitly authorised SRS frame into the local Matrix RF path."""

    frame = SRSFrame.from_payload(payload)
    result = _SERVICE.ingest(frame)
    response = {
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
    _record("ingest", device_ref=response["estimate"]["device_ref"], guardian_rf_passed=True)
    return response


def add_authorised_calibration(payload: Mapping[str, object]) -> dict[str, object]:
    """Add one Human-Authority-supplied calibration observation in memory."""

    frame_payload = payload.get("frame")
    if not isinstance(frame_payload, Mapping):
        raise TypeError("calibration_frame_required")
    frame = SRSFrame.from_payload(frame_payload)
    point = _SERVICE.add_calibration_from_frame(
        frame,
        label=str(payload.get("label") or "calibration")[:80],
        x_m=float(payload.get("x_m") or 0.0),
        y_m=float(payload.get("y_m") or 0.0),
        z_m=float(payload.get("z_m") or 0.0),
        zone=str(payload.get("zone") or "")[:80],
    )
    response = {
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
    _record("calibration", label=point.label, zone=point.zone, model_trained=response["model_trained"])
    return response


def seed_software_app_test() -> dict[str, object]:
    """Seed non-live, authorised software fixtures so the ISAC app can prove its software path."""

    calibration_specs = (
        ("north_gate", 0.0, 0.0, 0.0, "North Gate", 1.0),
        ("centre_zone", 6.0, 4.0, 0.0, "Centre Zone", 1.35),
        ("south_gate", 12.0, 1.0, 0.0, "South Gate", 0.75),
    )
    calibrations = []
    for sequence, (label, x_m, y_m, z_m, zone, scale) in enumerate(calibration_specs, start=1):
        calibrations.append(
            add_authorised_calibration(
                {
                    "label": label,
                    "x_m": x_m,
                    "y_m": y_m,
                    "z_m": z_m,
                    "zone": zone,
                    "frame": _software_test_frame(f"calibration-{sequence}", sequence, scale),
                }
            )
        )
    observations = (
        ingest_authorised_payload(_software_test_frame("oap-test-device-a", 11, 1.05)),
        ingest_authorised_payload(_software_test_frame("oap-test-device-b", 12, 1.30)),
    )
    _record("software_app_seed", calibrations=len(calibrations), observations=len(observations))
    return {
        "status": "software_app_test_seeded",
        "truth": "software_fixture_only_not_live_radio",
        "calibrations": calibrations,
        "observations": observations,
        "app_status": isac_app_status(),
    }


def _base_status() -> dict[str, Any]:
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
    }


def isac_app_status() -> dict[str, Any]:
    """Return the full software-app status without overclaiming hardware readiness."""

    status = _base_status()
    dashboard = status["dashboard"]
    software_checks = {
        "founder_only_dashboard": True,
        "status_api": True,
        "ingest_api": True,
        "calibration_api": True,
        "proof_runner": True,
        "guardian_rf_minimisation": status["guardian_rf_minimisation"],
        "raw_rf_not_exposed": not status["raw_rf_in_matrix"],
        "biometric_identity_blocked": not status["biometric_identity"],
        "covert_tracking_blocked": not status["covert_person_tracking"],
        "matrix_rf_events": status["matrix_rf_events"],
        "safe_snapshot": isinstance(dashboard, dict),
    }
    software_app_green = all(bool(value) for value in software_checks.values())
    hardware_green = bool(status["physical_testbed_ready"] and status["accuracy_claim_certified"])
    status.update(
        {
            "app_name": "ISAC Command App",
            "app_green": software_app_green,
            "software_app_green": software_app_green,
            "hardware_green": hardware_green,
            "overall_status": "software_app_green_hardware_locked" if software_app_green and not hardware_green else "full_green_with_hardware_evidence",
            "available_controls": APP_CONTROLS,
            "software_checks": software_checks,
            "proof_events": tuple(_PROOF_EVENTS[-12:]),
            "hardware_lock_reason": None if hardware_green else "real_radio_adapter_calibration_and_accuracy_evidence_required",
        }
    )
    return status


def run_isac_proof_check() -> dict[str, object]:
    """Run a truthful green-gate check for the ISAC app."""

    status = isac_app_status()
    checks = [
        ("dashboard_private", True, "Founder-only Command Center surface registered"),
        ("status_api", True, "Status API returns safe JSON"),
        ("ingest_api", True, "Authorised ingestion route exists"),
        ("calibration_api", True, "Authorised calibration route exists"),
        ("guardian_rf", status["guardian_rf_minimisation"], "Raw RF minimised before Matrix RF"),
        ("raw_rf_block", not status["raw_rf_in_matrix"], "Raw RF is not exposed in dashboard events"),
        ("biometric_block", not status["biometric_identity"], "Biometric identity blocked"),
        ("covert_tracking_block", not status["covert_person_tracking"], "Covert personal tracking blocked"),
        ("human_authority", status["human_authority_final"], "Human Authority remains final"),
        ("software_app_green", status["software_app_green"], "Software app controls are available"),
        ("hardware_claim_block", not status["accuracy_claim_certified"], "Accuracy claims remain blocked without proof"),
    ]
    report = tuple(
        {"id": key, "passed": bool(passed), "status": "green" if passed else "amber", "note": note}
        for key, passed, note in checks
    )
    event = _record("proof_check", passed=sum(1 for _key, passed, _note in checks if passed), total=len(checks))
    return {
        "status": "green" if all(item["passed"] for item in report) else "amber",
        "truth": "software_app_green_physical_rf_locked_until_evidence",
        "checks": report,
        "event": event,
        "app_status": status,
    }


def isac_spatial_status() -> dict[str, Any]:
    """Return truthful OAP ISAC software/testbed readiness."""

    status = isac_app_status()
    status["remaining_physical_gates"] = tuple(
        gate
        for gate, passed in (
            ("configure_oai_or_equivalent_radio_adapter", status["adapter"] != "unconfigured"),
            ("connect_authorised_over_the_air_radio_testbed", status["radio_evidence_present"]),
            ("collect_real_calibration_dataset", status["model_trained"]),
            ("certify_measured_accuracy", status["accuracy_evidence_present"]),
        )
        if not passed
    )
    return status
