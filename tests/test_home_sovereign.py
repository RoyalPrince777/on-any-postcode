from __future__ import annotations


def test_home_keeps_existing_sections_and_renders_gateway(client):
    response = client.get("/")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'id="signal"' in page
    assert 'id="live"' in page
    assert 'id="teams"' in page
    assert 'id="myworld"' in page
    assert 'id="sovereign"' in page
    assert "OAP Sovereign Mission Control" in page
    assert 'href="/mission"' in page
    assert "Mission Control database not initialized" in page
    assert "🇬🇭 Ghana" in page


def test_home_keeps_legacy_post_forms(client):
    page = client.get("/").get_data(as_text=True)

    for route in ("/signal", "/room", "/flag", "/myworld"):
        assert f'method="post" action="{route}"' in page


def test_gateway_has_three_validated_mode_links(client):
    page = client.get("/").get_data(as_text=True)

    assert 'href="/mission?mode=sovereign"' in page
    assert 'href="/mission?mode=mission"' in page
    assert 'href="/mission?mode=approval"' in page


def test_gateway_shows_six_intelligence_entries(client):
    page = client.get("/").get_data(as_text=True)

    for name in (
        "GPT Intelligence",
        "Claude Intelligence",
        "Gemini Intelligence",
        "Kimi Intelligence",
        "Grok Intelligence",
        "Edge/Copilot Intelligence",
    ):
        assert name in page
