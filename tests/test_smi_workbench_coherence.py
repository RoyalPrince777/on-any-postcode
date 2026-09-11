from mission_control import smi_workbench


def test_workbench_exposes_coherence_and_distribution(monkeypatch):
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
    payload = smi_workbench.get_workbench_status()
    ids = {item["id"] for item in payload["capabilities"]}
    assert "oap-coherent-automation" in ids
    assert "oap-distribution-intelligence" in ids
    assert "OAP Coherent Automation 21-signal planning" in payload["runtime_gate"]["available"]
    assert "OAP Distribution Intelligence release and rights review" in payload["runtime_gate"]["available"]
