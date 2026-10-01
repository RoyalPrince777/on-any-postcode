from pathlib import Path

import app as app_module
from mission_control import sika_market_settlement as sika


def _root() -> Path:
    return Path(app_module.app.root_path)


def test_market_payment_route_is_sika_first():
    source = (
        _root() / "mission_control" / "product_core_views.py"
    ).read_text(encoding="utf-8")
    template = (
        _root() / "mission_control" / "templates" / "market.html"
    ).read_text(encoding="utf-8")

    assert "sika_market_settlement.STORE.create_for_order(" in source
    assert '"payment_route": "SIKA"' in source
    assert "customer_approval_reference" in source
    assert "Payment execution is routed through SIKA." in template
    assert "Market routes payment through SIKA settlement." in template
    assert "Payment route · SIKA → approved bank" in template


def test_sika_settlement_schema_reuses_commerce_order_and_payment_intent():
    sql = "\n".join(sika.SCHEMA_STATEMENTS)

    assert "oap_sika_market_settlement_intents" in sql
    assert "REFERENCES oap_commerce_orders(order_id)" in sql
    assert "REFERENCES oap_commerce_payment_intents(intent_id)" in sql
    assert "UNIQUE REFERENCES oap_commerce_orders(order_id)" in sql
    assert "sika_route TEXT NOT NULL DEFAULT 'SIKA'" in sql
    assert "BANK_AUTHORITY_REQUIRED" in sql
    assert "READY_FOR_BANK" in sql


def test_sika_settlement_remains_non_executing_without_bank_adapter():
    methods = set(dir(sika.SikaMarketSettlementStore))
    assert {
        "capture_payment",
        "transfer_money",
        "issue_sika",
        "post_ledger_entry",
        "execute_bank_transfer",
    }.isdisjoint(methods)


def test_sika_settlement_states_require_real_provider_progression():
    assert sika.SETTLEMENT_STATES == {
        "BANK_AUTHORITY_REQUIRED",
        "READY_FOR_BANK",
        "SUBMITTED",
        "SETTLED",
        "FAILED",
        "STOPPED",
        "RECOVERY_REQUIRED",
    }


def test_sika_settlement_truth_flags_are_non_executing():
    source = (
        _root() / "mission_control" / "sika_market_settlement.py"
    ).read_text(encoding="utf-8")

    assert '"sika_issuance_performed": False' in source
    assert '"ledger_posting_performed": False' in source
    assert '"payment_capture_performed": False' in source
    assert '"money_transfer_performed": False' in source
    assert '"provider_execution_required": True' in source
