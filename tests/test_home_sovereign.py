from __future__ import annotations


def test_home_keeps_public_sections_without_private_founder_entry(client):
    response = client.get("/")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'id="signal"' in page
    assert 'id="location"' in page
    assert 'id="myworld"' not in page
    assert 'id="sovereign"' not in page
    assert "PUBLIC" in page
    assert "PRIVATE" not in page
    assert 'href="/my-world"' not in page
    assert "Enter My World" not in page
    assert 'href="/mission"' not in page
    assert "Your location hierarchy" in page
    assert "NEON" not in page
    assert "SMI" not in page
    assert 'href="/world-cup"' in page

    sport = client.get("/world-cup").get_data(as_text=True)
    assert 'id="live"' in sport
    assert 'id="teams"' in sport
    assert "🇬🇭 Ghana" in sport


def test_public_home_and_sport_keep_only_public_post_forms(client):
    home = client.get("/").get_data(as_text=True)
    sport = client.get("/world-cup").get_data(as_text=True)

    assert 'method="post" action="/signal"' in home
    for route in ("/room", "/flag"):
        assert f'method="post" action="{route}"' in sport
    assert 'method="post" action="/myworld"' not in home + sport
    assert home.count('name="csrf_token"') == 1
    assert sport.count('name="csrf_token"') == 96


def test_gateway_has_three_validated_mode_links(client):
    page = client.get("/mission").get_data(as_text=True)

    assert 'href="/mission?mode=sovereign"' in page
    assert 'href="/mission?mode=mission"' in page
    assert 'href="/mission?mode=approval"' in page


def test_gateway_shows_seven_oap_intelligence_families(client):
    page = client.get("/mission").get_data(as_text=True)

    for name in (
        "Civic Intelligence",
        "Jungle Book Intelligence",
        "Animal Intelligence",
        "Matrix Intelligence",
        "Civilisation Intelligence",
        "Akan Core Intelligence",
        "Akan Animal Intelligence",
    ):
        assert name in page

    assert "GPT Intelligence" not in page
    assert "Ollama Local Intelligence" not in page
