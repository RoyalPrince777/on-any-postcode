from oap.smi import travel_agency


def _clear_supply_env(monkeypatch):
    for suffix in (
        "CONNECTED",
        "SEARCH_CERTIFIED",
        "COMMERCIAL_TERMS_CERTIFIED",
        "BOOKING_CERTIFIED",
    ):
        monkeypatch.delenv(f"OAP_SUPPLY_BOOKING_COM_{suffix}", raising=False)


def test_travel_agency_preserves_smi_boundaries(monkeypatch):
    _clear_supply_env(monkeypatch)
    current = travel_agency.status()

    assert current["intelligence_world"] is False
    assert current["agent"] is False
    assert current["brain"] is False
    assert current["brain_count_added"] == 0
    assert current["capability_registry_ready"] is True
    assert current["supply_adapter_framework_ready"] is True
    assert current["provider_authority"] is False
    assert current["guardian_gate_required"] is True
    assert current["human_authority_final"] is True


def test_travel_agency_keeps_transactions_fail_closed_without_runtime_supply(monkeypatch):
    _clear_supply_env(monkeypatch)
    current = travel_agency.status()

    assert current["live_supply_search_ready"] is False
    assert current["booking_transactions_live"] is False
    assert current["payment_transactions_live"] is False
    assert current["commission_settlement_live"] is False
    assert current["production_booking_claim_allowed"] is False
    assert current["production_payment_claim_allowed"] is False
    assert current["production_commission_claim_allowed"] is False

    gate_states = {gate["id"]: gate["ready"] for gate in current["gates"]}
    assert gate_states["capability_registry"] is True
    assert gate_states["supply_adapter_framework"] is True
    assert gate_states["live_supply_search"] is False
    assert gate_states["booking_execution"] is False
    assert gate_states["payment_execution"] is False
    assert gate_states["commission_settlement"] is False


def test_live_search_certification_does_not_imply_booking(monkeypatch):
    monkeypatch.setenv("OAP_SUPPLY_BOOKING_COM_CONNECTED", "1")
    monkeypatch.setenv("OAP_SUPPLY_BOOKING_COM_SEARCH_CERTIFIED", "1")
    monkeypatch.setenv("OAP_SUPPLY_BOOKING_COM_COMMERCIAL_TERMS_CERTIFIED", "1")
    monkeypatch.setenv("OAP_SUPPLY_BOOKING_COM_BOOKING_CERTIFIED", "1")

    current = travel_agency.status()

    assert current["live_supply_search_ready"] is True
    assert current["booking_transactions_live"] is False
    assert current["payment_transactions_live"] is False
    assert current["commission_settlement_live"] is False
