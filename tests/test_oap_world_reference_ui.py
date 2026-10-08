from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "templates" / "world.html"


def test_oap_world_reference_ui_contract():
    page = WORLD.read_text(encoding="utf-8")
    for marker in (
        "OAP World",
        "One World. One Front Door. Many systems inside.",
        "The Spot",
        "The Link",
        "Link Up",
        "Chess",
        "Eats",
        "Travel",
        "Pay",
        "OAP Internet",
        "My World",
    ):
        assert marker in page

    for removed in (
        "YOUR LOCAL",
        "MARKETPLACE.",
        "LOCAL SHOP",
        "Quick Actions",
        "OAP Store",
        "HRM",
        "Guardian",
    ):
        assert removed not in page


def test_public_oap_world_exposes_no_founder_entry():
    page = WORLD.read_text(encoding="utf-8")
    assert 'href="/auth"' not in page
    assert "Founder" not in page


def test_oap_internet_card_links_to_real_route():
    page = WORLD.read_text(encoding="utf-8")
    assert 'href="/internet"' in page
    assert 'href="/world/languages"' not in page


def test_oap_internet_entry_is_public_and_has_recovery():
    from app import app
    with app.test_client() as client:
        response = client.get("/internet")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'action="/search"' in html
    assert 'href="/world"' in html
    assert "External websites are not OAP-certified." in html
