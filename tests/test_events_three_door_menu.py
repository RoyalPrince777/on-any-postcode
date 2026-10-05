def test_events_three_door_routes_are_reachable(client):
    expected = {
        "/events": "Discover",
        "/events/mine": "Where I’m Going",
        "/events/organise": "Make It Happen",
    }
    for path, marker in expected.items():
        response = client.get(path, follow_redirects=True)
        page = response.get_data(as_text=True)
        assert response.status_code == 200
        assert marker in page
        assert 'href="/events"' in page
        assert 'href="/events/mine"' in page
        assert 'href="/events/organise"' in page


def test_events_menu_hides_unbuilt_dead_actions(client):
    organise = client.get("/events/organise", follow_redirects=True).get_data(as_text=True)
    for dead_route in (
        "/events/organise/new",
        "/events/organise/mine",
        "/events/organise/:event_id/pulse",
        "/events/organise/:event_id/people",
        "/events/organise/:event_id/value",
        "/events/organise/:event_id/incoming",
        "/events/organise/:event_id/flow",
        "/events/organise/:event_id/run-it-back",
        "/events/organise/:event_id/cancel",
    ):
        assert dead_route not in organise
