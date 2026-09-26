from mission_control import alignment_views


def test_state_binding_route_is_founder_only_and_no_store(client, monkeypatch):
    monkeypatch.setattr(
        alignment_views.runtime_state_binding,
        "probe",
        lambda: {"component": "SMI Runtime State Binding Proof", "read_only": True},
    )
    response = client.get("/smi/state-binding")
    assert response.status_code in {302, 401, 403}
