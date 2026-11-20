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
        "KORADASO Internet",
        "My World",
    ):
        assert marker in page

    for removed in (
        "YOUR LOCAL",
        "MARKETPLACE.",
        "LOCAL SHOP",
        "Quick Actions",
        "HRM",
        "Guardian",
    ):
        assert removed not in page


def test_public_oap_world_exposes_no_founder_entry():
    page = WORLD.read_text(encoding="utf-8")
    assert 'href="/auth"' not in page
    assert "Founder" not in page


def test_oap_browse_and_apps_links_to_existing_koradaso_and_store_without_duplicate_card():
    page = WORLD.read_text(encoding="utf-8")
    assert 'aria-label="Browse and Apps across OAP World"' in page
    assert '<a href="/koradaso" data-oap-browse-koradaso>' in page
    assert '<strong>🌐 KORADASO Internet</strong>' in page
    assert '<a href="/store" data-oap-world-apps>' in page
    assert '<a href="/search" data-oap-world-search>' in page
    assert page.count('href="/koradaso"') == 1
    assert "HTTPS consent required." in page
    assert 'href="/world/languages"' not in page
    assert 'window.confirm' in page
