from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "templates" / "home.html"


def test_oap_world_reference_ui_contract():
    page = HOME.read_text(encoding="utf-8")
    for marker in (
        "ON ANY POSTCODE",
        "SHOP.",
        "SELL.",
        "LOCAL.",
        "Shop local. Sell local.",
        "Shop",
        "Sell",
        "Orders",
        "Pay",
        "Eats",
        "Map",
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
