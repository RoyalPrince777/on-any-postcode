from __future__ import annotations

import smi_gateway
from mission_control import smi_certification


def test_runtime_certification_proves_safe_seven_stage_contract():
    snapshot = smi_certification.certify()

    assert snapshot["certified"] is True
    assert snapshot["status"] == "green"
    assert snapshot["stage_count"] == 7
    assert snapshot["stages"] == (
        "understand",
        "context",
        "route",
        "evidence",
        "challenge",
        "synthesise",
        "govern",
    )
    assert snapshot["passed"] == snapshot["total"]
    assert all(snapshot["checks"].values())
    assert snapshot["provider_called"] is False
    assert snapshot["hrm_written"] is False
    assert snapshot["founder_session_created"] is False
    assert snapshot["private_reasoning_exposed"] is False
    assert snapshot["decision_authority"] is False
    assert snapshot["execution_authority"] is False
    assert snapshot["human_authority_final"] is True


def test_public_origin_hides_certification_without_signed_gateway(
    anonymous_client, monkeypatch
):
    secret = "g" * 40
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", secret)

    blocked = anonymous_client.get("/api/smi/thinking-certification")
    assert blocked.status_code == 404
    assert blocked.headers["Cache-Control"] == "no-store"

    allowed = anonymous_client.get(
        "/api/smi/thinking-certification",
        headers={"X-OAP-SMI-Gateway": secret},
    )
    assert allowed.status_code == 200
    payload = allowed.get_json()
    assert payload["status"] == "certified"
    assert payload["signal"] == "🟢"
    assert payload["gateway_authorized"] is True
    assert payload["founder_auth_bypassed"] is False
    assert payload["certification"]["passed"] == payload["certification"]["total"]
    assert payload["certification"]["stage_count"] == 7
    assert payload["certification"]["provider_called"] is False
    assert payload["certification"]["hrm_written"] is False
    assert payload["certification"]["founder_session_created"] is False
    assert payload["certification"]["private_reasoning_exposed"] is False
    assert payload["certification"]["human_authority_final"] is True


def test_private_gateway_allows_only_the_named_smi_certification_path():
    assert smi_gateway._allowed("api/smi/thinking-certification") is True
    assert smi_gateway._allowed("api/smi/private-reasoning") is False
    assert smi_gateway._allowed("api/smi/execute") is False
