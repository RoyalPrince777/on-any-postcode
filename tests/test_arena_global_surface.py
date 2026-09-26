def test_public_arena_exposes_global_non_financial_stack(anonymous_client):
    response = anonymous_client.get("/arena")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Global Arena" in page
    assert "Postcode" in page
    assert "Borough / Region" in page
    assert "Country" in page
    assert "Continent" in page
    assert "Competition" in page
    assert "Rankings" in page
    assert "Teams" in page
    assert "Tournaments" in page
    assert "Leagues" in page
    assert "Spectator" in page
    assert "Disputes" in page
    assert "prizes, SIKA and payment execution remain disabled" in page
