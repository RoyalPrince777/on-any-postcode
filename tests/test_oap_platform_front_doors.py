from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_spot_exposes_the_link_booking_shop_and_distribution(anonymous_client):
    response = anonymous_client.get("/the-spot")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    # Validate the canonical destinations, not repeat marketing headings or
    # duplicate cards. More may progressively disclose secondary destinations.
    for route in ("/the-link", "/travel/direct", "/the-spot/market", "/the-spot/distribution"):
        assert f'href="{route}"' in page
    assert 'aria-label="The Spot core order"' in page
    assert 'aria-label="OAP platform front doors"' in page


def test_link_exposes_booking_shop_distribution_without_private_data(anonymous_client):
    response = anonymous_client.get("/the-link")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    for route in ("/linkup", "/travel/direct", "/the-spot/market", "/the-spot/distribution"):
        assert f'href="{route}"' in page
    assert "Private by design" in page
    assert "message_body" not in page
    assert "recipient_id" not in page


def test_platform_front_doors_reuse_governed_product_routes():
    spot = (ROOT / "mission_control" / "templates" / "spot.html").read_text(encoding="utf-8")
    link = (ROOT / "mission_control" / "templates" / "the_link.html").read_text(encoding="utf-8")
    for page in (spot, link):
        assert "travel_supply.public_marketplace" in page
        assert "capability_slug='market'" in page
        assert "capability_slug='distribution'" in page
    assert "the_link_front_door" in spot
    assert "linkup_front_door" in link
