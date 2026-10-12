from pathlib import Path

WORLD = Path(__file__).resolve().parents[1] / "templates" / "world.html"


def test_world_front_door_preserves_identity_and_navigation():
    page = WORLD.read_text(encoding="utf-8")
    assert 'class="worldmark"' in page
    assert "ON ANY POSTCODE" in page
    assert 'href="/the-spot"' in page
    assert 'href="/linkup"' in page
    assert 'href="/my-world"' in page
    assert "prefers-reduced-motion:reduce" in page


def test_direct_address_field_does_not_pretend_ai_search_is_live():
    page = WORLD.read_text(encoding="utf-8")
    assert 'role="search"' in page
    assert 'inputmode="url"' in page
    assert '["http:","https:"]' in page
    assert "SMI Direct answers and cross-world search are not yet enabled here." in page
    assert "AI search is not yet enabled." in page
