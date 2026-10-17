def test_spot_promotes_first_class_events_card(client):
    response = client.get("/the-spot")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert '<strong>🎪 Events</strong>' in page
    assert 'href="/events"' in page
    assert "Activity / Adventure" not in page
