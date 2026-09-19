"""Receipt status must never write on GET; proof is explicit and CSRF protected."""
from __future__ import annotations

from flask import Flask

from mission_control import alignment_views


def test_receipt_get_is_passive(monkeypatch):
    app = Flask(__name__)
    writes = []

    monkeypatch.setattr(
        alignment_views.smi_receipt_backend,
        "receipt_backend_status",
        lambda: writes.append("proof") or {"ok": True},
    )
    monkeypatch.setattr(
        alignment_views.smi_receipt_backend,
        "backend_configuration_status",
        lambda: {"durable_backend_configured": True},
    )
    monkeypatch.setattr(
        alignment_views.smi_receipt_backend,
        "latest_receipts",
        lambda limit: {"count": 1, "receipts": []},
    )

    with app.test_request_context("/smi/brain/receipts"):
        response = alignment_views.smi_brain_receipts.__wrapped__()
        payload = response.get_json()
    assert writes == []
    assert payload["status"]["proof_state"] == "not_run_on_read"
    assert payload["status"]["independent_durable_hrm_ready"] is False
    assert payload["status"]["write_read_proof"] is None
    assert response.headers["Cache-Control"] == "no-store"


def test_receipt_post_requires_csrf_and_runs_explicit_proof(monkeypatch):
    app = Flask(__name__)
    writes = []
    monkeypatch.setattr(
        alignment_views.smi_receipt_backend,
        "receipt_backend_status",
        lambda: writes.append("proof") or {"durable": True, "read_back_ok": True},
    )
    monkeypatch.setattr(alignment_views.web_security, "csrf_valid", lambda request: False)

    with app.test_request_context("/smi/brain/receipts/proof", method="POST"):
        denied = alignment_views.smi_brain_receipts_proof.__wrapped__()
    assert denied.status_code == 403
    assert writes == []

    monkeypatch.setattr(alignment_views.web_security, "csrf_valid", lambda request: True)
    with app.test_request_context("/smi/brain/receipts/proof", method="POST"):
        response = alignment_views.smi_brain_receipts_proof.__wrapped__()
    assert response.status_code == 200
    assert response.get_json()["status"]["read_back_ok"] is True
    assert writes == ["proof"]


def test_missing_sqlite_fallback_is_not_created_by_status(monkeypatch, tmp_path):
    from mission_control import smi_receipt_backend

    missing = tmp_path / "receipts.sqlite3"
    for key in (
        "OAP_HRM_DATABASE_URL",
        "OAP_SMI_HRM_DATABASE_URL",
        "OAP_HRM_DATABASE_URL_B64",
        "OAP_SMI_HRM_DATABASE_URL_B64",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OAP_SMI_RECEIPT_DB_PATH", str(missing))

    result = smi_receipt_backend.latest_receipts(5)

    assert result["count"] == 0
    assert result["durable"] is False
    assert not missing.exists()



def test_passive_receipt_host_fingerprint_is_secret_safe(monkeypatch):
    import hashlib

    from mission_control import smi_receipt_backend

    for key in (
        "OAP_HRM_DATABASE_URL",
        "OAP_SMI_HRM_DATABASE_URL",
        "OAP_HRM_DATABASE_URL_B64",
        "OAP_SMI_HRM_DATABASE_URL_B64",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(
        "OAP_HRM_DATABASE_URL",
        "postgresql://private-user:private-password@ep-example.neon.tech/neondb",
    )
    status = smi_receipt_backend.backend_configuration_status()
    assert status["hrm_host_sha256"] == hashlib.sha256(
        b"ep-example.neon.tech"
    ).hexdigest()
    assert status["live_store_identity_proven"] is False
    assert "private-user" not in str(status)
    assert "private-password" not in str(status)
    assert "ep-example.neon.tech" not in str(status)


def test_receipt_host_fingerprint_unconfigured(monkeypatch):
    from mission_control import smi_receipt_backend

    for key in (
        "OAP_HRM_DATABASE_URL",
        "OAP_SMI_HRM_DATABASE_URL",
        "OAP_HRM_DATABASE_URL_B64",
        "OAP_SMI_HRM_DATABASE_URL_B64",
    ):
        monkeypatch.delenv(key, raising=False)
    assert smi_receipt_backend.backend_configuration_status()["hrm_host_sha256"] is None
