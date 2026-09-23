"""Non-payment boundary tests for the Prince Sovereign Bank contract."""
from mission_control import prince_sovereign_bank as bank


def test_identity_and_units() -> None:
    state = bank.status()
    assert state["name"] == "United States of Africa Royalty Bank"
    assert state["banking_family"] == "Prince Sovereign Bank"
    assert state["currency"]["name"] == "SIKA"
    assert state["currency"]["subunit"] == "SEEDS"
    assert state["currency"]["subunits_per_unit"] == 100
    assert state["existing_oap_bank_rail_preserved"] is True


def test_mind_body_soul_and_first_party_integrations() -> None:
    state = bank.status()
    assert state["first_party_core"] is True
    assert all(state[organ] for organ in ("mind", "body", "soul"))
    assert "double_entry_ledger" in state["body"]
    assert "community_treasury" in state["integrations"]


def test_no_false_claims() -> None:
    state = bank.status()
    assert state["operational_bank"] is False
    assert state["licence_verified"] is False
    assert state["production_tested"] is False
    assert state["regulated_execution_enabled"] is False
    assert state["currency"]["rewards_are_money"] is False
    assert state["currency"]["proposed_currency_is_legal_tender"] is False


def test_all_capabilities_fail_closed_even_with_flags() -> None:
    for capability in (*bank.REGULATED_CAPABILITIES, "unknown"):
        assert not bank.capability_allowed(capability)
        assert not bank.capability_allowed(
            capability,
            authorised=True,
            customer_approved=True,
            production_gate_passed=True,
        )
