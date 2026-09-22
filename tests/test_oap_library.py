"""OAP Library public/private boundary and working-book proof."""

from pathlib import Path

from mission_control import oap_library

ROOT = Path(__file__).resolve().parents[1]


def test_library_catalog_is_first_party_and_keeps_founder_assets_private():
    validation = oap_library.validate_catalog()

    assert validation["passed"] is True
    assert validation["founder_assets_exposed"] is False
    assert oap_library.LIBRARY_JOURNEY == (
        "Read",
        "Understand",
        "Learn",
        "Create",
        "Preserve",
        "Share",
    )
    assert oap_library.COLLECTIONS[0]["id"] == "food-book"
    assert all(item["route"].startswith("/") for item in oap_library.COLLECTIONS)
    assert all(not item["route"].startswith("//") for item in oap_library.COLLECTIONS)


def test_public_library_opens_without_authentication(anonymous_client):
    response = anonymous_client.get("/library")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Knowledge belongs in your world." in body
    assert "One World. One Library. Unlimited Learning." in body
    assert "Read" in body and "Understand" in body and "Share" in body
    assert "Food Book" in body
    assert "oap_library_brighter_tomorrow.webp" in body
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Content-Security-Policy"].startswith(
        "default-src 'self'"
    )

    home = anonymous_client.get("/").get_data(as_text=True)
    assert 'href="/library"' in home
    assert "Open OAP Library" in home


def test_public_library_search_returns_only_matching_working_collections(
    anonymous_client,
):
    response = anonymous_client.get("/library?q=language")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "World Languages" in body
    assert "Food Book" not in body

    empty = anonymous_client.get("/library?q=not-a-real-oap-collection")
    assert empty.status_code == 200
    assert "No OAP collection matches that search." in empty.get_data(as_text=True)


def test_food_book_remains_inside_authenticated_member_boundary(anonymous_client):
    for path in ("/library/food-book", "/mission/food-book"):
        response = anonymous_client.get(path, follow_redirects=False)
        assert response.status_code in (302, 303, 401, 403)
        assert "Vegetables, nutrients" not in response.get_data(as_text=True)


def test_food_book_member_sign_in_is_live_on_the_public_origin(
    anonymous_client,
    monkeypatch,
):
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")

    protected = anonymous_client.get("/library/food-book", follow_redirects=False)
    assert protected.status_code == 302
    assert protected.headers["Location"].startswith(
        "/library/sign-in?next=/library/food-book"
    )

    sign_in = anonymous_client.get(protected.headers["Location"])
    body = sign_in.get_data(as_text=True)
    assert sign_in.status_code == 200
    assert 'action="/library/auth/sign-in"' in body
    assert 'name="next" value="/library/food-book"' in body
    assert "Sign in for this action" in body
    assert "PRIVATE · FOUNDER" not in body


def test_library_member_sign_in_cannot_be_retargeted_to_founder_control(
    anonymous_client,
    monkeypatch,
):
    monkeypatch.setenv("OAP_SURFACE_ROLE", "public")

    response = anonymous_client.get("/library/sign-in?next=/mission/ollama")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'name="next" value="/library/food-book"' in body
    assert 'action="/library/auth/sign-in"' in body
    assert "PRIVATE · FOUNDER" not in body


def test_signed_in_member_can_use_source_scoped_food_book(client):
    response = client.get("/library/food-book")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert (
        "Vegetables, nutrients &amp; your body" in body
        or "Vegetables, nutrients & your body" in body
    )
    assert 'data-body-area="eyes"' in body
    assert 'data-food="sweet-pepper"' in body
    assert "Food supports the whole body." in body
    assert "does not diagnose illness" in body
    assert "NHS · Why 5 A Day?" in body
    assert "NIH · Vitamin K" in body
    assert response.headers["Cache-Control"] == "no-store"
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_library_artwork_is_the_saved_oap_asset():
    artwork = ROOT / "static" / "oap" / "oap_library_brighter_tomorrow.webp"

    assert artwork.is_file()
    assert artwork.stat().st_size == 182496


def test_private_command_navigation_opens_public_library_without_conflating_assets():
    command_nav = (
        ROOT / "mission_control" / "templates" / "_command_nav.html"
    ).read_text()

    assert "oap_library.library_home" in command_nav
    assert "📚 Library" in command_nav
    assert "Founder Library" not in command_nav
