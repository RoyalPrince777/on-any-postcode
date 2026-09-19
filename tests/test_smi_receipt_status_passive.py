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
