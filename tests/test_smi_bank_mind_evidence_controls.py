"""Bank Mind CC must use founder authentication and refuse invented green."""
from pathlib import Path
from mission_control import prince_sovereign_bank as bank

ROOT = Path(__file__).resolve().parents[1]


def test_mind_route_requires_founder_and_no_store() -> None:
    source = (ROOT / "mission_control/bank_mind_control_routes.py").read_text()
    assert "@login_required(api=True, founder_only=True)" in source
    assert '"/mission/smi/bank/mind"' in source
    assert '"Cache-Control"] = "no-store"' in source
    assert '"release_proven": False' in source
    assert '"risk_engine_operationally_verified": False' in source
    assert '"identity_and_permissions_operationally_verified": False' in source


def test_mind_button_fetches_canonical_contract_and_fails_closed() -> None:
    source = (ROOT / "mission_control/static/smi_command_centre.js").read_text()
    assert 'fetch("/mission/smi/bank/mind"' in source
    assert 'credentials:"same-origin",cache:"no-store"' in source
    assert 'value.proof_scope!=="read_only_contract"' in source
    assert 'value.release_proven!==false' in source
    assert 'Mind evidence unavailable · NOT PROVEN' in source
    assert 'if(!bankControls.hidden)refreshBankMind()' in source


def test_bank_contract_does_not_turn_founder_review_into_execution() -> None:
    assert bank.status()["operational_bank"] is False
    assert bank.status()["regulated_execution_enabled"] is False
    assert not bank.capability_allowed(
        "payment_execution",
        authorised=True,
        customer_approved=True,
        production_gate_passed=True,
    )
