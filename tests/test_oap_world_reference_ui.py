from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "templates" / "home.html"


def test_oap_world_reference_ui_contract():
    page = HOME.read_text(encoding="utf-8")
    for marker in (
        "OAP WORLD",
        "STRIP OF NOISE",
        "Search the world... any postcode...",
        "Map Intelligence",
        "The Spot",
        "The Link",
        "Market",
        "Media",
        "OAP Store",
        "SIKA",
        "HRM",
        "Guardian",
        "Settings",
        "PEOPLE",
        "PLACES",
        "POSSIBILITIES",
        "WITHOUT LIMITS",
        "Live Location",
        "Quick Actions",
        "EXPLORE THE WORLD",
        "Connect People. Power Places. Create Possibilities.",
    ):
        assert marker in page


def test_public_oap_world_exposes_no_founder_entry():
    page = HOME.read_text(encoding="utf-8")
    assert 'href="/auth"' not in page
    assert "Founder" not in page
