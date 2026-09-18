from mission_control import smi_anatomy_runtime


def test_anatomy_runtime_keeps_one_brain_14_regions_and_21_stage_protocol(monkeypatch):
    monkeypatch.setattr(
        smi_anatomy_runtime.smi_receipt_backend,
        "latest_receipts",
        lambda limit=200: {
            "backend": "local_sqlite_receipt_store",
            "durable": False,
            "fallback_used": False,
            "receipts": (),
        },
    )
    status = smi_anatomy_runtime.status()

    assert status["brain_count"] == 1
    assert status["anatomical_region_count"] == 14
    assert status["anatomical_region_target"] == 14
    assert status["adaptive_depths"] == (3, 7, 21)
    assert status["protocol_stages"] == 21
    assert status["mind_body_soul_blocks"] == 3
    assert status["laws_count"] == 21
    assert status["signals_count"] == 21
    assert status["anatomy_complete"] is True
    assert status["protocol_complete"] is True
    assert status["full_runtime_green"] is False
    assert status["execution_granted"] is False
    assert status["approval_granted"] is False
    assert status["human_authority_final"] is True

    assert all(region["evidence_score"] == 3 for region in status["regions"])
    assert all(region["light"] == "🟣" for region in status["regions"])


def test_anatomy_runtime_advances_only_with_matching_runtime_receipts(monkeypatch):
    monkeypatch.setattr(
        smi_anatomy_runtime.smi_receipt_backend,
        "latest_receipts",
        lambda limit=200: {
            "backend": "independent_hrm_postgres",
            "durable": True,
            "fallback_used": False,
            "receipts": (
                {
                    "receipt_kind": "agent_tool_connection_receipt",
                    "brain_part": "prefrontal_cortex",
                },
                {
                    "receipt_kind": "hrm_neon_evidence_receipt",
                    "brain_part": "prefrontal_cortex",
                },
                {
                    "receipt_kind": "war_room_live_proof_receipt",
                    "brain_part": "prefrontal_cortex",
                },
                {
                    "receipt_kind": "matrix_learning_receipt",
                    "brain_part": "prefrontal_cortex",
                },
            ),
        },
    )
    status = smi_anatomy_runtime.status()
    regions = {item["id"]: item for item in status["regions"]}

    assert regions["prefrontal_cortex"]["evidence_score"] == 7
    assert regions["prefrontal_cortex"]["light"] == "🟢"
    assert regions["prefrontal_cortex"]["missing"] == ()
    assert regions["thalamus"]["evidence_score"] == 3
    assert regions["thalamus"]["light"] == "🟣"
    assert status["fully_proven_regions"] == 1
    assert status["full_runtime_green"] is False


def test_anatomy_runtime_endpoint_is_founder_only(client, anonymous_client):
    response = client.get("/mission/smi/brain/anatomy")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["component"] == "SMI 21 Anatomy Runtime Certificate"
    assert response.headers["Cache-Control"] == "no-store"

    anonymous = anonymous_client.get("/mission/smi/brain/anatomy")
    assert anonymous.status_code == 401
    assert anonymous.get_json()["error"]["code"] == "authentication_required"
