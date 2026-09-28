from pathlib import Path

import app as app_module
from mission_control import market_transaction_spine


def _root() -> Path:
    return Path(app_module.app.root_path)


def test_market_mission_100_surface_has_real_basket_order_timeline_stop_recovery():
    template = (
        _root() / "mission_control" / "templates" / "market.html"
    ).read_text(encoding="utf-8")

    assert "Your Basket" in template
    assert "Review & Confirm Orders" in template
    assert "My Orders" in template
    assert "Order & Transaction Timeline" in template
    assert "STOP Transaction" in template
    assert "last_good_stage" in template
    assert "/mission/organs/market/orders" in template
    assert "/mission/organs/market/transactions/" in template
    assert "No payment is captured" in template


def test_market_mission_100_api_bridge_is_canonical_and_fail_closed():
    source = (
        _root() / "mission_control" / "product_core_views.py"
    ).read_text(encoding="utf-8")

    assert '@bp.post("/market/orders")' in source
    assert "_store.create_order_intent(" in source
    assert "market_transaction_spine.STORE.create_from_order(" in source
    assert '@bp.get("/market/orders/<order_id>")' in source
    assert '@bp.get("/market/transactions/<transaction_id>")' in source
    assert '@bp.post("/market/transactions/<transaction_id>/stop")' in source
    assert '"payment_capture_performed": False' in source
    assert '"money_transfer_performed": False' in source
    assert '"external_fulfilment_performed": False' in source
    assert '"automatic_dispatch_performed": False' in source


def test_market_recovery_view_never_invents_automatic_recovery(monkeypatch):
    store = market_transaction_spine.MarketTransactionStore()

    monkeypatch.setattr(
        store,
        "read_for_identity",
        lambda **_kwargs: {
            "transaction_id": "11111111-1111-4111-8111-111111111111",
            "state": "RECOVERY_REQUIRED",
            "stop_state": "RECOVERY_REQUIRED",
            "recovery_state": "REQUIRED",
            "last_good_stage": "ORDER_RECORDED",
        },
    )

    result = store.recovery_view(
        transaction_id="11111111-1111-4111-8111-111111111111",
        identity_id="22222222-2222-4222-8222-222222222222",
    )

    assert result["state"] == "RECOVERY_REQUIRED"
    assert result["consequential_action_allowed"] is False
    assert result["next_safe_action"] == "review_evidence"
    assert result["automatic_recovery_performed"] is False
    assert result["human_authority_final"] is True


def test_market_transaction_store_has_owner_scoped_timeline_reads():
    methods = set(dir(market_transaction_spine.MarketTransactionStore))

    assert {"list_for_identity", "events_for_identity", "recovery_view", "stop"} <= methods
    forbidden = {
        "capture_payment",
        "transfer_money",
        "external_fulfilment",
        "handoff_to_carrier",
        "automatic_dispatch",
    }
    assert forbidden.isdisjoint(methods)
