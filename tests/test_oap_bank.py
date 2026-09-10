from mission_control import oap_bank, smi_workbench


def test_oap_bank_is_orchestration_only_and_never_claims_regulated_status():
    payload = oap_bank.status()
    policy = payload["bank_policy"]
    governance = payload["governance"]

    assert payload["id"] == "oap-bank"
    assert payload["name"] == "OAP Bank"
    assert payload["surface"].startswith("Founder-only")
    assert policy["external_bank_is_custodian"] is True
    assert policy["oap_holds_customer_funds"] is False
    assert policy["oap_initiates_payments"] is False
    assert policy["oap_executes_transfers"] is False
    assert policy["oap_issues_bank_accounts"] is False
    assert policy["oap_claims_regulated_bank_status"] is False
    assert policy["payment_enabled"] is False
    assert policy["open_banking_live"] is False
    assert governance["human_authority_final"] is True
    assert governance["compliance_before_activation"] is True
    assert governance["public_bank_claim_locked_until_approval"] is True


def test_oap_bank_is_visible_to_private_smi_without_changing_connector_contract(monkeypatch):
    monkeypatch.setattr(
        smi_workbench.smi_chat_runtime,
        "health",
        lambda: {"status": "yellow", "checks": {"database": False, "schema": False}},
    )

    payload = smi_workbench.get_workbench_status()
    bank = next(item for item in payload["capabilities"] if item["id"] == "oap-bank")

    assert [item["id"] for item in payload["connectors"]] == ["render", "github", "neon"]
    assert bank["ready"] is True
    assert bank["bank_policy"]["payment_enabled"] is False
    assert "OAP Bank non-payment orchestration planning" in payload["runtime_gate"]["available"]
