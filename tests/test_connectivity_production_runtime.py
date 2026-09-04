import hashlib
import hmac
import json

from mission_control.connectivity_runtime import (
    IMT_2030_STANDARD_FINALIZED,
    _radio_attestation_status,
    connectivity_runtime_status,
)


def _signed_document(payload: dict[str, object], secret: str) -> dict[str, object]:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), encoded, hashlib.sha256).hexdigest()
    return {"payload": payload, "signature": signature}


def test_connectivity_runtime_is_production_not_demo():
    status = connectivity_runtime_status()
    assert status["mode"] == "production"
    assert status["demo_mode"] is False
    assert status["simulation_success_allowed"] is False
    assert status["host"]["live_runtime_probe"] is True
    assert status["host"]["external_probe_used"] is False
    assert status["network_execution_authority"] is False
    assert status["human_authority_final"] is True


def test_fresh_signed_prestandard_radio_evidence_can_prove_real_testbed(tmp_path):
    now = 1_788_485_400.0
    secret = "local-test-key"
    payload = {
        "collector_id": "oap-radio-collector-1",
        "observed_at_unix": now - 5,
        "radio_class": "6g-prestandard-testbed",
        "ran_connected": True,
        "core_connected": True,
        "device_connected": True,
        "authorized_radio_environment": True,
        "production_network": False,
    }
    path = tmp_path / "6g-evidence.json"
    path.write_text(json.dumps(_signed_document(payload, secret)), encoding="utf-8")

    evidence = _radio_attestation_status(
        evidence_path=str(path),
        evidence_key=secret,
        now=now,
    )

    assert evidence["signature_valid"] is True
    assert evidence["fresh"] is True
    assert evidence["radio_connected"] is True
    assert evidence["valid"] is True
    assert evidence["testbed_ready"] is True
    assert evidence["production_network_attested"] is False


def test_bad_radio_signature_fails_closed(tmp_path):
    now = 1_788_485_400.0
    payload = {
        "collector_id": "oap-radio-collector-1",
        "observed_at_unix": now,
        "radio_class": "6g-prestandard-testbed",
        "ran_connected": True,
        "core_connected": True,
        "device_connected": True,
        "authorized_radio_environment": True,
        "production_network": False,
    }
    path = tmp_path / "6g-evidence.json"
    path.write_text(
        json.dumps({"payload": payload, "signature": "not-valid"}),
        encoding="utf-8",
    )

    evidence = _radio_attestation_status(
        evidence_path=str(path),
        evidence_key="local-test-key",
        now=now,
    )

    assert evidence["signature_valid"] is False
    assert evidence["valid"] is False
    assert evidence["testbed_ready"] is False


def test_6g_production_network_cannot_be_claimed_before_standard_is_final():
    status = connectivity_runtime_status()
    assert IMT_2030_STANDARD_FINALIZED is False
    assert status["imt_2030_standard_finalized"] is False
    assert status["6g_production_network_ready"] is False
