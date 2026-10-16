from mission_control import alignment_views


def test_state_binding_route_is_founder_only_and_no_store(client, monkeypatch):
    monkeypatch.setattr(
        alignment_views.runtime_state_binding,
        "probe",
        lambda: {"component": "SMI Runtime State Binding Proof", "read_only": True},
    )

    rule = next(
        rule
        for rule in client.application.url_map.iter_rules()
        if rule.rule == "/mission/smi/state-binding"
    )
    view = client.application.view_functions[rule.endpoint]
    assert getattr(view, "_oap_login_required", False) is True
    assert getattr(view, "_oap_founder_only", False) is True
    assert getattr(view, "_oap_api", False) is True

    authorised = client.get("/mission/smi/state-binding")
    assert authorised.status_code == 200
    assert authorised.headers["Cache-Control"] == "no-store"
    assert authorised.get_json()["read_only"] is True
