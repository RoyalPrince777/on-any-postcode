from pathlib import Path

import app as app_module
from mission_control import market_execution_authority as gate


def test_execution_gate_covers_all_locked_market_edges():
    assert gate.CAPABILITIES == {
        "PAYMENT_CAPTURE",
        "MONEY_TRANSFER",
        "EXTERNAL_FULFILMENT",
        "CARRIER_HANDOFF",
        "AUTOMATIC_DISPATCH",
    }


def test_execution_requires_approved_authority_and_clear_stop_recovery():
    assert gate.execution_allowed(
        authority_state="APPROVED",
        stop_state="NONE",
        recovery_state="NONE",
    )
    assert not gate.execution_allowed(
        authority_state="PENDING",
        stop_state="NONE",
        recovery_state="NONE",
    )
    assert not gate.execution_allowed(
        authority_state="APPROVED",
        stop_state="STOPPED",
        recovery_state="NONE",
    )
    assert not gate.execution_allowed(
        authority_state="APPROVED",
        stop_state="NONE",
        recovery_state="REQUIRED",
    )


def test_execution_authority_schema_is_durable_and_evidence_bound():
    sql = "\n".join(gate.SCHEMA_STATEMENTS)
    assert "oap_market_execution_authorities" in sql
    assert "provider_reference" in sql
    assert "evidence_sha256" in sql
    assert "human_approval_reference" in sql
    assert "APPROVED" in sql
    assert "REVOKED" in sql
    assert "EXPIRED" in sql


def test_market_execution_api_exposes_ready_gate_without_fake_execution():
    root = Path(app_module.app.root_path)
    source = (
        root / "mission_control" / "product_core_views.py"
    ).read_text(encoding="utf-8")

    assert '@bp.get("/market/execution-status")' in source
    assert '@bp.post("/market/execution-authorities")' in source
    assert "founder_only=True" in source
    assert '@bp.post("/market/orders/<order_id>/prepare-execution")' in source


def test_gate_does_not_implement_provider_execution_methods():
    methods = set(dir(gate.MarketExecutionAuthorityStore))
    assert {
        "capture_payment",
        "transfer_money",
        "handoff_to_carrier",
        "dispatch_worker",
        "execute_external_fulfilment",
    }.isdisjoint(methods)
