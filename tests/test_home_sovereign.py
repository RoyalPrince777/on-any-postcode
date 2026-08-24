from __future__ import annotations


def test_home_keeps_public_sections_and_draws_explicit_boundary(client):
    response = client.get("/")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'id="signal"' in page
    assert 'id="live"' in page
    assert 'id="teams"' in page
    assert 'id="myworld"' not in page
    assert 'id="sovereign"' not in page
    assert "PUBLIC" in page
    assert "PRIVATE" in page
    assert 'href="/my-world"' in page
    assert 'href="/mission"' not in page
    assert "Your private OAP space" in page
    assert "NEON" not in page
    assert "SMI" not in page
    assert "🇬🇭 Ghana" in page


def test_home_keeps_only_public_post_forms(client):
    page = client.get("/").get_data(as_text=True)

    for route in ("/signal", "/room", "/flag"):
        assert f'method="post" action="{route}"' in page
    assert 'method="post" action="/myworld"' not in page
    assert page.count('name="csrf_token"') == 97


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
