from mission_control import world_geography


def test_world_is_continent_first_and_world_cup_stays_separate(client):
    page = client.get('/world').get_data(as_text=True)
    assert 'Continent → Country → County / Region → Borough / District → Postcode' in page
    for continent in world_geography.CONTINENTS:
        assert continent['name'] in page
        assert f"{continent['name']} Continent Room" in page
    assert 'World Cup' in page
    assert 'World Cup stays available as sport content' in page


def test_continent_surface_contains_country_anthem_culture_sport_humour_and_rooms(client):
    page = client.get('/world/africa').get_data(as_text=True)
    assert 'Ghana' in page
    assert 'God Bless Our Homeland Ghana' in page
    assert 'National anthem' in page
    assert 'Sport' in page
    assert 'Culture' in page
    assert 'Humour &amp; fun' in page
    assert 'Ghana Country Room' in page


def test_country_page_puts_national_identity_at_country_level(client):
    page = client.get('/world/africa/ghana').get_data(as_text=True)
    assert 'God Bless Our Homeland Ghana' in page
    assert 'National identity' in page
    assert 'World Cup and other national-team competition sit under Sport.' in page
    assert 'County / Region' in page
    assert 'Borough / District' in page
    assert 'Postcode' in page
    assert 'Open Country Room' in page


def test_local_levels_have_correct_content_and_postcode_returns_to_the_spot(client):
    region = client.get('/world/europe/england?level=region&place=Greater%20London').get_data(as_text=True)
    borough = client.get('/world/europe/england?level=borough&place=Mitcham').get_data(as_text=True)
    postcode = client.get('/world/europe/england?level=postcode&place=CR4').get_data(as_text=True)

    assert 'Regional sport' in region
    assert 'Regional culture' in region
    assert 'Local sport' in borough
    assert 'Neighbourhood culture' in borough
    assert 'The Spot' in postcode
    assert 'Postcode Room' in postcode
    assert '/the-spot?postcode=CR4' in postcode


def test_unknown_geography_fails_closed(client):
    response = client.get('/world/atlantis')
    assert response.status_code == 404
    assert response.get_json()['error']['code'] == 'not_found'
    assert client.get('/world/africa/not-a-country').status_code == 404
    assert client.get('/world/africa/ghana?level=planet&place=x').status_code == 400


def test_hierarchy_room_requires_csrf(client):
    response = client.post('/world/room', data={'level':'continent','place':'Africa','message':'Hello'})
    assert response.status_code == 403


def test_hierarchy_room_rejects_unknown_level(client, csrf):
    response = client.post('/world/room', data={'csrf_token':csrf,'level':'planet','place':'Earth','message':'Hello'})
    assert response.status_code == 400
    assert response.get_json()['error']['code'] == 'invalid_room'


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


def test_level_content_keeps_national_and_local_content_in_the_right_places():
    assert 'National anthem' in world_geography.LEVEL_CONTENT['country']
    assert 'National anthem' not in world_geography.LEVEL_CONTENT['postcode']
    assert 'Continental sport' in world_geography.LEVEL_CONTENT['continent']
    assert 'Regional sport' in world_geography.LEVEL_CONTENT['region']
    assert 'Neighbourhood culture' in world_geography.LEVEL_CONTENT['borough']
    assert 'The Spot' in world_geography.LEVEL_CONTENT['postcode']
    assert 'Postcode Room' in world_geography.LEVEL_CONTENT['postcode']
