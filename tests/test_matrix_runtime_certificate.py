from mission_control import matrix_runtime_certificate


def test_matrix_runtime_certificate_keeps_truth_layers_separate(monkeypatch):
    monkeypatch.setattr(
        matrix_runtime_certificate.all_intelligence,
        "status",
        lambda: {
            "worlds": (
                {
                    "id": "matrix",
                    "architecture_ready": True,
                    "routing_ready": True,
                    "registered_agents": 7,
                },
            )
        },
    )
    monkeypatch.setattr(
        matrix_runtime_certificate.matrix_signal_bus,
        "topology",
        lambda: {
            "registered_count": 7,
            "participants": tuple(
                {"status": "registered", "can_emit_signal": True}
                for _ in range(7)
            ),
            "execution_granted": False,
        },
    )
    monkeypatch.setattr(
        matrix_runtime_certificate.intelligence_runtime_proof,
        "status",
        lambda: {
            "worlds": (
                {
                    "id": "matrix",
                    "bounded_runtime_ready": True,
                    "live_external_ready": True,
                    "full_runtime_ready": False,
                    "bounded_evidence": "hosted runtime evidence",
                },
            )
        },
    )
    monkeypatch.setattr(
        matrix_runtime_certificate.smi_receipt_backend,
        "latest_receipts",
        lambda limit=100: {
            "durable": True,
            "receipts": (
                {"receipt_kind": "matrix_learning_receipt"},
            ),
        },
    )
    monkeypatch.setattr(
        matrix_runtime_certificate.smi_proof_gate,
        "public_safe_status",
        lambda: {"green": True},
    )

    status = matrix_runtime_certificate.status()
    assert status["brain_count"] == 1
    assert status["matrix_is_extra_brain"] is False
    assert status["bounded_runtime_ready"] is True
    assert status["live_external_ready"] is True
    assert status["ready_count"] == status["check_count"] == 5
    assert status["missing"] == ()
    assert status["full_runtime_ready"] is False
    assert status["full_runtime_light"] == "🟣"
    assert status["execution_granted"] is False
    assert status["approval_granted"] is False
    assert status["human_authority_final"] is True


def test_matrix_runtime_certificate_names_missing_proof(monkeypatch):
    monkeypatch.setattr(
        matrix_runtime_certificate.all_intelligence,
        "status",
        lambda: {
            "worlds": (
                {
                    "id": "matrix",
                    "architecture_ready": True,
                    "routing_ready": True,
                    "registered_agents": 7,
                },
            )
        },
    )
    monkeypatch.setattr(
        matrix_runtime_certificate.matrix_signal_bus,
        "topology",
        lambda: {
            "registered_count": 7,
            "participants": tuple(
                {"status": "registered", "can_emit_signal": True}
                for _ in range(7)
            ),
            "execution_granted": False,
        },
    )
    monkeypatch.setattr(
        matrix_runtime_certificate.intelligence_runtime_proof,
        "status",
        lambda: {
            "worlds": (
                {
                    "id": "matrix",
                    "bounded_runtime_ready": True,
                    "live_external_ready": False,
                    "full_runtime_ready": False,
                    "bounded_evidence": "bounded only",
                },
            )
        },
    )
    monkeypatch.setattr(
        matrix_runtime_certificate.smi_receipt_backend,
        "latest_receipts",
        lambda limit=100: {"durable": False, "receipts": ()},
    )
    monkeypatch.setattr(
        matrix_runtime_certificate.smi_proof_gate,
        "public_safe_status",
        lambda: {"green": False},
    )

    status = matrix_runtime_certificate.status()
    assert set(status["missing"]) == {
        "matrix_learning",
        "guardian_green_gate",
        "live_external",
    }
    assert status["full_runtime_ready"] is False
    assert status["network_calls_made"] is False


def test_matrix_runtime_endpoint_is_founder_read_only(client):
    response = client.get("/mission/intelligence/matrix")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["component"] == "Matrix Runtime Certificate"
    assert payload["system"] == "Matrix System"
    assert payload["execution_granted"] is False
    assert payload["approval_granted"] is False
    assert response.headers["Cache-Control"] == "no-store"


def test_matrix_runtime_endpoint_rejects_anonymous(anonymous_client):
    response = anonymous_client.get("/mission/intelligence/matrix")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"
