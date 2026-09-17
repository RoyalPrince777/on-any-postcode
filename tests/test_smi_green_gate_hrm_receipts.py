from mission_control import smi_proof_gate


def _counts(*, durable_receipts: int, store_present: bool = True):
    return {
        "store_reachable": True,
        "five_section_reviews": 1,
        "signed_approved_receipts": 1,
        "durable_hrm_receipts": durable_receipts,
        "durable_hrm_receipt_store_present": store_present,
        "founder_smi_reviews": 1,
        "oap_event_receipts": 1,
        "rollback_recovery_receipts": 1,
        "error": None,
    }


def test_green_gate_requires_durable_hrm_receipt(monkeypatch):
    monkeypatch.setattr(
        smi_proof_gate,
        "_production_counts",
        lambda: _counts(durable_receipts=0),
    )
    monkeypatch.setattr(
        smi_proof_gate.telemetry,
        "status",
        lambda: {"observability_ready": True},
    )

    snapshot = smi_proof_gate.status()

    assert snapshot["checks"]["durable_hrm_receipt"] is False
    assert snapshot["checks"]["receipt_chain"] is False
    assert snapshot["green"] is False
    assert "durable_hrm_receipt" in snapshot["missing"]
    assert "receipt_chain" in snapshot["missing"]


def test_green_gate_consumes_durable_hrm_receipt(monkeypatch):
    monkeypatch.setattr(
        smi_proof_gate,
        "_production_counts",
        lambda: _counts(durable_receipts=1),
    )
    monkeypatch.setattr(
        smi_proof_gate.telemetry,
        "status",
        lambda: {"observability_ready": True},
    )

    snapshot = smi_proof_gate.status()

    assert snapshot["checks"]["durable_hrm_receipt"] is True
    assert snapshot["checks"]["receipt_chain"] is True
    assert snapshot["green"] is True
    assert snapshot["missing"] == ()
