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
    assert "Order details" in template
    assert "STOP Transaction" in template
    assert "last_good_stage" not in template
    assert "/mission/organs/market/orders" in template
    assert "/mission/organs/market/transactions/" in template
    assert "No payment is captured" not in template


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


def test_market_checkout_preserves_ambiguous_order_retry_identity():
    """Guard the client contract until browser-level checkout tests can run."""
    template = (
        _root() / "mission_control" / "templates" / "market.html"
    ).read_text(encoding="utf-8")

    assert "item.idempotency_key = 'market-'" in template
    assert "saveBasket(basket);" in template
    assert "const key = item.idempotency_key;" in template
    assert "active.order_attempted = true;" in template
    assert "qty.disabled = checkoutInProgress || Boolean(item.order_attempted);" in template
    assert "row.querySelector('button').disabled = checkoutInProgress || Boolean(item.order_attempted);" in template
    assert "if (found?.order_attempted)" in template
    assert "loadBasket().filter(item => item.order_attempted)" in template
    assert "checkoutButton.disabled = true;" in template
    assert "checkoutButton.disabled = false;" in template
    assert "pending.splice(index, 1);" in template
    assert "Check My Orders before retrying" in template
    assert 'href="{{ request.path }}?mine=1#orders"' in template
    assert "verify an outstanding request before retrying" in template


def test_market_basket_and_retry_state_are_scoped_to_signed_in_identity():
    """The browser must never inherit another account's unscoped basket."""
    from jinja2 import Environment

    template = (
        _root() / "mission_control" / "templates" / "market.html"
    ).read_text(encoding="utf-8")
    key_line = next(
        line for line in template.splitlines() if "const keyName =" in line
    )
    render = Environment(autoescape=True).from_string(key_line).render

    first = render(auth_user={"id": "member-one"})
    second = render(auth_user={"id": "member-two"})
    anonymous = render(auth_user=None)

    assert "'oap-market-basket-v2:'" in first
    assert '"member-one"' in first
    assert '"member-two"' in second
    assert first != second
    assert '""' in anonymous
    assert "oap-market-basket-v1" not in template
    assert "Do not" in template and "unscoped basket" in template


def test_market_checkout_disables_basket_edits_while_in_flight():
    """Static regression contract; does not replace a browser integration test."""
    template = (
        _root() / "mission_control" / "templates" / "market.html"
    ).read_text(encoding="utf-8")

    assert "let checkoutInProgress = false;" in template
    assert "checkoutInProgress = true;" in template
    assert "checkoutInProgress = false;" in template
    assert "qty.disabled = checkoutInProgress || Boolean(item.order_attempted);" in template
    assert "if (checkoutInProgress || !next[index] || next[index].order_attempted) return;" in template
    assert "if (checkoutInProgress) return;" in template
    assert "document.getElementById('market-clear-basket').disabled = true;" in template
    assert "document.getElementById('market-clear-basket').disabled = false;" in template


def test_market_private_search_retains_founder_workspace():
    """Searching or clearing filters must not drop the private Market view."""
    template = (
        _root() / "mission_control" / "templates" / "market.html"
    ).read_text(encoding="utf-8")

    assert '{% if mine_view %}<input type="hidden" name="mine" value="1">{% endif %}' in template
    assert """{{ '?mine=1' if mine_view else '' }}""" in template


def test_market_order_errors_are_text_only_not_html():
    """Server-provided error messages must not enter an HTML parsing sink."""
    template = (
        _root() / "mission_control" / "templates" / "market.html"
    ).read_text(encoding="utf-8")

    assert "notice.textContent = 'Orders unavailable: ' + error.message;" in template
    assert "ordersList.replaceChildren(notice);" in template
    assert "Orders unavailable: ' + error.message + '</div>'" not in template


def test_market_private_workspace_survives_signin_and_product_detail():
    """Private navigation must survive login and opening a product detail."""
    template = (
        _root() / "mission_control" / "templates" / "market.html"
    ).read_text(encoding="utf-8")

    assert "next=(request.path ~ '?mine=1') if request.args.get('mine') == '1' else request.path" in template
    assert "href=\"{{ request.path }}?product={{ product.product_id }}{{ '&mine=1' if mine_view else '' }}\"" in template


def test_market_stop_never_targets_stale_order_details():
    """Client STOP remains disabled until the selected order's details load."""
    template = (
        _root() / "mission_control" / "templates" / "market.html"
    ).read_text(encoding="utf-8")

    assert "let orderDetailRequestId = 0;" in template
    assert "const requestId = ++orderDetailRequestId;" in template
    assert template.count("if (requestId !== orderDetailRequestId) return;") >= 3
    assert "activeTransactionId = null;\n      stopButton.disabled = true;" in template
    assert "activeTransactionId = transactionId;\n        stopButton.disabled" in template
    assert "if (!activeTransactionId || stopButton.disabled) return;" in template
    assert "const transactionId = activeTransactionId;" in template
    assert "Refresh this order before retrying" in template


def test_market_basket_limit_does_not_silently_drop_added_products():
    """The UI must reject the 21st distinct item before the storage cap truncates it."""
    template = (
        _root() / "mission_control" / "templates" / "market.html"
    ).read_text(encoding="utf-8")

    assert "basket.slice(0, 20)" in template
    assert "if (!found && basket.length >= 20)" in template
    assert "Basket limit reached (20 products)." in template
    assert template.index("if (!found && basket.length >= 20)") < template.index("else basket.push({")


def test_market_orders_refresh_ignores_stale_responses():
    """An older network response must not overwrite a newer My Orders refresh."""
    template = (
        _root() / "mission_control" / "templates" / "market.html"
    ).read_text(encoding="utf-8")

    assert "let ordersRequestId = 0;" in template
    assert "const requestId = ++ordersRequestId;" in template
    assert "const data = await jsonFetch('/mission/organs/market/orders');\n        if (requestId !== ordersRequestId) return;" in template
    assert "} catch (error) {\n        if (requestId !== ordersRequestId) return;" in template
