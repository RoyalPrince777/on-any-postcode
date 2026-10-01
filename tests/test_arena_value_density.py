def test_arena_value_density_quickstarts(client):
    response = client.get("/arena")
    assert response.status_code == 200
    text = response.get_data(as_text=True)

    assert "Choose the result" in text
    assert "one tap to the game" in text
    assert 'href="/arena/connect4"' in text
    assert 'href="/arena/connect4/room"' in text
    assert 'href="/arena/oware"' in text
    assert 'href="/arena/iq"' in text


def test_arena_value_density_keeps_truth_boundary(client):
    text = client.get("/arena").get_data(as_text=True)
    assert "No fake urgency" in text
    assert "no hidden paywall" in text
    assert "no inflated claims" in text
