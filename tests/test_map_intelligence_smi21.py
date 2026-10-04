from mission_control import local_map_intelligence, offline_routing


def test_smi_21_map_intelligence_contract_has_exactly_21_truth_gates():
    state = local_map_intelligence.smi_21_state()

    assert state["component"] == "SMI 21 · Map Intelligence"
    assert state["public_product"] == "On Any Postcode Maps"
    assert state["private_brain"] == "Map Intelligence"
    assert state["gate_count"] == 21
    assert len(state["gates"]) == 21
    assert [gate["number"] for gate in state["gates"]] == list(range(1, 22))
    assert state["protocol_complete"] is True
    assert state["truth_mode"] is True
    assert state["readiness_percent"] == round((state["passed_gate_count"] / 21) * 100, 1)
    assert state["green_votes"] + state["purple_votes"] == 21
    assert len(state["seven_star_review"]) == 7
    assert all(gate["signal"] in {"green", "purple"} for gate in state["gates"])


def test_smi_21_does_not_fake_green_for_evidence_dependent_gates():
    state = local_map_intelligence.smi_21_state()
    by_id = {gate["id"]: gate for gate in state["gates"]}

    assert by_id["offline_local"]["passed"] is False
    assert by_id["offline_local"]["layer"] == "evidence"
    assert state["overall_green"] is False
    assert "offline_local" in state["remaining_gate_ids"]
    assert state["truth_rule"] == "Green only when the exact claimed layer has working evidence."


def test_seed_route_preview_points_to_real_runtime_navigation_contract():
    preview = local_map_intelligence.route_proof("Mitcham", "London Bridge")

    assert preview["seed_preview_only"] is True
    assert preview["live_route_geometry"] is False
    assert preview["turn_by_turn_enabled"] is False
    assert preview["runtime_navigation_contract"] == "/map-intelligence/route"
    assert preview["runtime_route_geometry_available"] is True
    assert preview["runtime_turn_by_turn_available"] is True
    assert "seed preview never claims live routing" in preview["next_gate"]


def test_smi_21_endpoint_is_public_safe_and_no_store(client):
    response = client.get("/map-intelligence/smi-21")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    payload = response.get_json()
    assert payload["gate_count"] == 21
    assert payload["protocol_complete"] is True
    assert payload["no_hidden_tracking"] is True
    assert payload["payment_capture"] is False
    assert payload["automatic_dispatch"] is False


def test_smi_21_offline_gate_reads_real_package_evidence(monkeypatch):
    monkeypatch.setattr(
        offline_routing,
        "status",
        lambda: {
            "offline_local_routing_package_proven": True,
            "package_present": True,
        },
    )

    state = local_map_intelligence.smi_21_state()
    by_id = {gate["id"]: gate for gate in state["gates"]}

    assert by_id["offline_local"]["passed"] is True
    assert by_id["offline_local"]["signal"] == "green"
    assert "offline_local" not in state["remaining_gate_ids"]
