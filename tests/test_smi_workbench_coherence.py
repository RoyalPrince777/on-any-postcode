from mission_control import smi_workbench


def test_workbench_exposes_coherence_distribution_and_a7(monkeypatch):
    monkeypatch.setattr(
        smi_workbench.smi_chat_runtime,
        "health",
        lambda: {
            "status": "green",
            "checks": {
                "database": True,
                "schema": True,
                "chat_route": True,
                "conversation_memory": True,
                "war_room": True,
            },
        },
    )
    monkeypatch.setattr(
        smi_workbench.a7_certification,
        "status",
        lambda: {
            "ready_for_founder_certification": False,
            "certification_granted": False,
            "a7_enabled": False,
            "execution_granted": False,
            "a6_missing": ("independent_proof_runner",),
            "a7_missing": ("external_audit", "legal_compliance"),
            "human_authority_final": True,
            "external_evidence_is_software_verified": False,
        },
    )
    payload = smi_workbench.get_workbench_status()
    ids = {item["id"] for item in payload["capabilities"]}
    assert "oap-coherent-automation" in ids
    assert "oap-distribution-intelligence" in ids
    assert "smi-a7-certification" in ids
    assert "OAP Coherent Automation 21-signal planning" in payload["runtime_gate"]["available"]
    assert "OAP Distribution Intelligence release and rights review" in payload["runtime_gate"]["available"]
    assert "SMI A7 certification readiness and governed evidence gate" in payload["runtime_gate"]["available"]

    a7 = payload["a7"]
    assert a7["level"] == "A7"
    assert a7["ready_for_founder_certification"] is False
    assert a7["certification_granted"] is False
    assert a7["a7_enabled"] is False
    assert a7["execution_granted"] is False
    assert a7["human_authority_final"] is True
    assert a7["external_evidence_is_software_verified"] is False
    assert a7["fail_closed"] is True
    assert "external_audit" in a7["a7_missing"]
    assert "legal_compliance" in a7["a7_missing"]

    capability = next(item for item in payload["capabilities"] if item["id"] == "smi-a7-certification")
    assert capability["state"] == "yellow"
    assert capability["fail_closed"] is True
    assert capability["human_authority_final"] is True
    assert "external_audit" in capability["blocked_reason"]
