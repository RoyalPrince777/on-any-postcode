from __future__ import annotations


def test_public_market_hides_private_market_controls(client):
    page = client.get("/the-spot/market").get_data(as_text=True)

    assert "Find what you need" in page
    assert 'id="orders"' not in page
    assert 'id="sell"' not in page
    assert "My Orders" not in page
    assert "Sell on OAP" not in page
    assert "My Market" in page


def test_my_market_shows_owner_controls_for_authenticated_user(client):
    page = client.get("/the-spot/market?mine=1").get_data(as_text=True)

    assert "My Market" in page
    assert "Your Market workspace" in page
    assert 'id="orders"' in page
    assert 'id="sell"' in page
    assert "My Orders" in page
    assert "Sell on OAP" in page
    assert "View Public Market" in page


def test_anonymous_mine_query_cannot_expose_private_controls(anonymous_client):
    page = anonymous_client.get("/the-spot/market?mine=1").get_data(as_text=True)

    assert 'id="orders"' not in page
    assert 'id="sell"' not in page
    assert "My Orders" not in page
    assert "Sell on OAP" not in page


def test_sell_and_orders_routes_land_in_my_market(client):
    sell = client.get("/sell", follow_redirects=False)
    orders = client.get("/orders", follow_redirects=False)

    assert sell.status_code == 302
    assert sell.headers["Location"].endswith("/the-spot/market?mine=1#sell")
    assert orders.status_code == 302
    assert orders.headers["Location"].endswith("/the-spot/market?mine=1#orders")


def test_sell_route_requires_authentication(anonymous_client):
    response = anonymous_client.get("/sell", follow_redirects=False)

    assert response.status_code == 302
    assert "/enter-my-world?next=" in response.headers["Location"]
