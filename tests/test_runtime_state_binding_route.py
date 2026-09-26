from mission_control import alignment_views


def test_state_binding_route_is_founder_only_and_no_store(
    client, anonymous_client, monkeypatch
):
    monkeypatch.setattr(
        alignment_views.runtime_state_binding,
        "probe",
        lambda: {"component": "SMI Runtime State Binding Proof", "read_only": True},
    )

    authorised = client.get("/mission/smi/state-binding")
    assert authorised.status_code == 200
    assert authorised.headers["Cache-Control"] == "no-store"
    assert authorised.get_json()["read_only"] is True

    denied = anonymous_client.get("/mission/smi/state-binding")
    assert denied.status_code in {401, 403}
