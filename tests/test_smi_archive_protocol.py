"""Mission-to-100 protocol locks for SMI Archive."""
from mission_control import smi_archive


def test_mission_to_100_requires_exact_artifact_parity_and_human_final():
    status = smi_archive.status()
    rules = {item["id"]: item["rule"] for item in status["mission_to_100_protocol"]}

    assert status["exact_artifact_parity_required_for_production_green"] is True
    assert status["mandatory_gate_can_be_averaged_away"] is False
    assert "artifact" in rules["exact-artifact-parity"].lower()
    assert "target" in rules["target-runtime-proof"].lower()
    assert "averaged" in rules["no-average-away"].lower()
    assert "recovery" in rules["rollback-before-promotion"].lower()
    assert status["human_authority_final"] is True


def test_mission_to_100_protocol_is_not_a_new_authority_or_brain():
    status = smi_archive.status()

    assert status["new_brain_created"] is False
    assert status["new_memory_engine_created"] is False
    assert status["new_execution_authority_created"] is False
    assert status["history_is_timeline_inside_archive"] is True


def test_archive_exposes_first_party_inference_as_runtime_evidence(monkeypatch):
    monkeypatch.setattr(
        smi_archive.oap_inference_gateway,
        "status",
        lambda probe=False: {
            "first_party_inference_ready": False,
            "local_enabled": True,
            "local_url_configured": True,
            "local_model_configured": True,
            "home_node_bridge": {
                "configured": True,
                "worker_recently_seen": False,
                "durable_worker_fresh": False,
                "worker_ready": False,
                "transport": "outbound_https_poll",
            },
        },
    )

    evidence = smi_archive.status()["runtime_evidence"]["first_party_inference"]
    assert evidence["ready"] is False
    assert evidence["bridge_configured"] is True
    assert evidence["worker_ready"] is False
    assert evidence["worker_recently_seen"] is False
    assert evidence["durable_worker_fresh"] is False
    assert "configuration alone is not proof" in evidence["proof_rule"]
