from __future__ import annotations

import pytest

from mission_control import isac_spatial_intelligence, technology_intelligence
from oap.isac import ISACSpatialService, SRSFrame, extract_spatial_features


def _frame(device: str, scale: float, *, authorised: bool = True) -> SRSFrame:
    antennas = tuple(
        tuple(
            (scale * (index + 1) * (antenna + 1), scale * (index + 2) * 0.25)
            for index in range(8)
        )
        for antenna in range(4)
    )
    return SRSFrame(
        source="oai-flexric-test",
        device_ref=device,
        cell_ref="oap-cell-1",
        antenna_iq=antennas,
        authorised=authorised,
    )


def test_srs_feature_contract_is_fixed_local_and_finite():
    features = extract_spatial_features(_frame("ue-a", 1.0))
    assert len(features) == 32
    assert all(isinstance(value, float) for value in features)


def test_unauthorised_rf_is_rejected_before_processing():
    service = ISACSpatialService()
    with pytest.raises(PermissionError, match="rf_measurement_not_authorised"):
        service.ingest(_frame("ue-a", 1.0, authorised=False))


def test_calibration_enables_local_positioning_and_matrix_minimisation():
    service = ISACSpatialService()
    for label, x_m, y_m, scale in (
        ("A", 0.0, 0.0, 0.7),
        ("B", 3.0, 0.0, 1.0),
        ("C", 3.0, 3.0, 1.4),
    ):
        service.add_calibration_from_frame(
            _frame(f"cal-{label}", scale),
            label=label,
            x_m=x_m,
            y_m=y_m,
            zone=f"zone-{label}",
        )
    result = service.ingest(_frame("ue-live", 1.05))
    assert service.model.trained is True
    assert result["estimate"].calibrated is True
    assert result["matrix_event"].raw_rf_included is False
    assert result["guardian_rf_passed"] is True
    snapshot = service.snapshot()
    assert snapshot["raw_rf_in_matrix"] is False
    assert snapshot["biometric_identity"] is False
    assert snapshot["covert_person_tracking"] is False


def test_isac_runtime_keeps_physical_claims_fail_closed_without_evidence(monkeypatch):
    monkeypatch.delenv("OAP_ISAC_ADAPTER", raising=False)
    monkeypatch.delenv("OAP_ISAC_RADIO_EVIDENCE", raising=False)
    monkeypatch.delenv("OAP_ISAC_ACCURACY_EVIDENCE", raising=False)
    snapshot = isac_spatial_intelligence.isac_spatial_status()
    assert snapshot["software_ready"] is True
    assert snapshot["live_radio_connected"] is False
    assert snapshot["physical_testbed_ready"] is False
    assert snapshot["accuracy_claim_certified"] is False
    assert snapshot["centimetre_accuracy_claim"] is False
    assert snapshot["sub_metre_accuracy_claim"] is False
    assert snapshot["raw_rf_in_matrix"] is False
    assert snapshot["external_provider_authority"] is False
    assert snapshot["human_authority_final"] is True


def test_technology_intelligence_nests_isac_without_new_world():
    status = technology_intelligence.technology_intelligence_status()
    capability_ids = {item["id"] for item in status["connectivity"]["capabilities"]}
    assert "isac_spatial" in capability_ids
    assert status["isac_software_ready"] is True
    assert status["brain_count"] == 0
    assert status["intelligence_world_count_added"] == 0
    assert status["autonomous_radio_control"] is False


def test_founder_isac_dashboard_exposes_privacy_reduced_state(client):
    response = client.get("/mission/isac-spatial")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "ISAC Spatial Intelligence" in page
    assert "Radio → Edge → Guardian RF → Matrix RF" in page
    assert "No raw RF" in page
    assert "No biometric identity" in page
    assert "centimetre" in page
    assert "SRS / I-Q ingest" in page
