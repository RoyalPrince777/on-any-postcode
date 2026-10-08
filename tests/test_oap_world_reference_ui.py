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


def test_oap_internet_card_does_not_claim_unimplemented_launch():
    page = WORLD.read_text(encoding="utf-8")
    assert '<strong>🌐 OAP Internet</strong>' in page
    assert 'href="/world/languages"' not in page
    assert 'Web launch from this card is not yet available.' in page
