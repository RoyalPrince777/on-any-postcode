from __future__ import annotations

from mission_control import smi_receipt_backend


def test_durable_button_proof_fails_closed_when_backend_is_unconfigured(monkeypatch):
    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "")

    result = smi_receipt_backend.latest_durable_button_proof()

    assert result == {
        "proven": False,
        "reason": "durable_hrm_backend_not_configured",
        "receipt_id": None,
    }


def test_durable_button_proof_fails_closed_when_backend_read_fails(monkeypatch):
    monkeypatch.setattr(
        smi_receipt_backend,
        "_hrm_database_url",
        lambda: "postgresql://example.invalid/oap",
    )

    def unavailable():
        raise RuntimeError("backend unavailable")

    monkeypatch.setattr(smi_receipt_backend, "_connect_postgres", unavailable)

    result = smi_receipt_backend.latest_durable_button_proof()

    assert result == {
        "proven": False,
        "reason": "durable_button_proof_unavailable",
        "receipt_id": None,
    }


def test_require_durable_blocks_when_hrm_backend_is_unconfigured(monkeypatch):
    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "")

    def sqlite_must_not_run(*args, **kwargs):
        raise AssertionError("durable recovery proof must never fall back to SQLite")

    monkeypatch.setattr(smi_receipt_backend, "_write_sqlite", sqlite_must_not_run)

    result = smi_receipt_backend.write_receipt(
        "hrm_neon_evidence_receipt",
        {
            "brain_part": "recovery_test",
            "gate": 21,
            "command": "durable_only",
            "safe_payload": {"probe": True},
        },
        require_durable=True,
    )

    assert result["ok"] is False
    assert result["status"] == "blocked_durable_hrm_unconfigured"
    assert result["receipt_id"] is None
    assert result["read_back_ok"] is False
    assert result["durable"] is False
    assert result["backend"] == "unconfigured"
    assert result["fallback_used"] is False


def test_require_durable_does_not_fall_back_after_postgres_failure(monkeypatch):
    monkeypatch.setattr(
        smi_receipt_backend,
        "_hrm_database_url",
        lambda: "postgresql://example.invalid/oap",
    )

    def postgres_failure(*args, **kwargs):
        raise RuntimeError("commit or readback unavailable")

    def sqlite_must_not_run(*args, **kwargs):
        raise AssertionError("durable recovery proof must never fall back to SQLite")

    monkeypatch.setattr(smi_receipt_backend, "_write_postgres", postgres_failure)
    monkeypatch.setattr(smi_receipt_backend, "_write_sqlite", sqlite_must_not_run)

    result = smi_receipt_backend.write_receipt(
        "hrm_neon_evidence_receipt",
        {
            "brain_part": "recovery_test",
            "gate": 21,
            "command": "durable_only",
            "safe_payload": {"probe": True},
        },
        require_durable=True,
    )

    assert result["ok"] is False
    assert result["status"] == "durable_commit_or_readback_unconfirmed"
    assert result["receipt_id"].startswith("smi-")
    assert result["read_back_ok"] is False
    assert result["durable"] is False
    assert result["backend"] == "independent_hrm_postgres"
    assert result["fallback_used"] is False


def test_lab_recovery_anchor_blocks_when_independent_backend_is_not_proven(monkeypatch):
    monkeypatch.setattr(
        smi_receipt_backend,
        "backend_configuration_status",
        lambda: {
            "durable_backend_configured": True,
            "hrm_host_sha256": "same-host",
            "main_host_sha256": "same-host",
        },
    )

    def write_must_not_run(*args, **kwargs):
        raise AssertionError("unproven recovery backend must not write an anchor")

    monkeypatch.setattr(smi_receipt_backend, "write_receipt", write_must_not_run)

    result = smi_receipt_backend.write_lab_recovery_anchor(
        {"owner_id": "founder", "notebook_id": "recovery-check", "version": 1}
    )

    assert result["ok"] is False
    assert result["status"] == "blocked_independent_hrm_not_proven_separate"
    assert result["receipt_id"] is None
    assert result["read_back_ok"] is False
    assert result["durable"] is False
    assert result["fallback_used"] is False
    assert result["backend"] == "independent_hrm_postgres"
