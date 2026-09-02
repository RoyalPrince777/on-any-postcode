from mission_control import world_geography


def test_world_is_continent_first_and_world_cup_stays_separate(client):
    page = client.get('/world').get_data(as_text=True)
    assert 'Continent → Country → County / Region → Borough / District → Postcode' in page
    for continent in world_geography.CONTINENTS:
        assert continent['name'] in page
    assert 'World Cup' in page
    assert 'Sport is part of culture, not the map.' in page


def test_country_surface_contains_anthem_culture_sport_humour_and_rooms(client):
    page = client.get('/world/africa').get_data(as_text=True)
    assert 'Ghana' in page
    assert 'God Bless Our Homeland Ghana' in page
    assert 'National anthem' in page
    assert 'Sport' in page
    assert 'Culture' in page
    assert 'Humour &amp; fun' in page
    assert 'Ghana Country Room' in page
    assert 'County / Region' in page
    assert 'Borough / District' in page
    assert 'Postcode' in page


def test_unknown_continent_fails_closed(client):
    response = client.get('/world/atlantis')
    assert response.status_code == 404
    assert response.get_json()['error']['code'] == 'not_found'


def test_hierarchy_room_requires_csrf(client):
    response = client.post('/world/room', data={'level':'continent','place':'Africa','message':'Hello'})
    assert response.status_code == 403


def test_world_cup_route_is_preserved_and_not_false_live(client):
    response = client.get('/world-cup')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'OAP World Cup' in page
    assert '2026 tournament archive' in page
    assert 'live status must come from Sports Intelligence verification' in page
    assert '<h2>Live / Next</h2>' not in page


def test_sports_status_defaults_to_truthful_unobserved_state(client):
    response = client.get('/world/sports/status')
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'
    data = response.get_json()
    assert data['name'] == 'OAP Sports Intelligence'
    assert data['live_claim_allowed'] is False
    assert data['evidence']['verified_sources'] == 0
    assert data['autonomy']['observe'] is True
    assert data['autonomy']['verify'] is True
    assert data['autonomy']['approve'] is False
