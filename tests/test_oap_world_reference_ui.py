from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "templates" / "home.html"


def test_oap_world_reference_ui_contract():
    page = HOME.read_text(encoding="utf-8")
    for marker in (
        "ON ANY POSTCODE",
        "YOUR LOCAL",
        "MARKETPLACE.",
        "LOCAL SHOP",
        "Shop",
        "Sell",
        "Orders",
        "Pay",
        "Eats",
        "Map",
        "Local shops",
        "On the shelf",
    ):
        assert marker in page

    for removed in (
        "STRIP OF NOISE",
        "OAP WORLD",
        "Quick Actions",
        "The Link",
        "Media",
        "OAP Store",
        "HRM",
        "Guardian",
        "Settings",
        "WITHOUT LIMITS",
    ):
        assert removed not in page


def test_public_oap_world_exposes_no_founder_entry():
    page = HOME.read_text(encoding="utf-8")
    assert 'href="/auth"' not in page
    assert "Founder" not in page
