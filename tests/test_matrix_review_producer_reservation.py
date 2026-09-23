from __future__ import annotations

import pytest

from mission_control import smi_receipt_backend


@pytest.mark.parametrize(
    "brain_part",
    ["matrix", "recursive_self_improvement", "other"],
)
def test_generic_writer_cannot_mint_reserved_matrix_review(
    tmp_path, monkeypatch: pytest.MonkeyPatch, brain_part: str
) -> None:
    path = tmp_path / "must-not-create.sqlite3"
    monkeypatch.setenv("OAP_SMI_RECEIPT_DB_PATH", str(path))
    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "")
    receipt = smi_receipt_backend.write_receipt(
        "war_room_live_proof_receipt",
        {
            "brain_part": brain_part,
            "gate": 6,
            "command": "matrix_review_outcome",
            "safe_payload": {
                "review_mode": "first_party_matrix_review",
                "proposal_id": "RSI-123",
                "signal_id": "MATRIX-SIGNAL-123",
                "evidence_verified": True,
                "reviewed": True,
                "founder_approved": True,
                "guardian_pass": True,
                "green_gate_pass": True,
                "execution_granted": False,
            },
        },
    )
    assert receipt["status"] == "blocked_reserved_matrix_review_producer"
    assert receipt["ok"] is False
    assert receipt["durable"] is False
    assert receipt["receipt_id"] is None
    assert not path.exists()


def test_existing_generic_seven_rule_lens_remains_writable_locally(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OAP_SMI_RECEIPT_DB_PATH", str(tmp_path / "ordinary.sqlite3"))
    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "")
    receipt = smi_receipt_backend.write_receipt(
        "war_room_live_proof_receipt",
        {
            "brain_part": "other",
            "gate": 6,
            "command": "war_room",
            "safe_payload": {"review_mode": "canonical_seven_bounded_rule_lenses"},
        },
    )
    assert receipt["ok"] is True
    assert receipt["read_back_ok"] is True
    assert receipt["durable"] is False
