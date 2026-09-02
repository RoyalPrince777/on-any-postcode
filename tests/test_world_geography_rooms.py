from mission_control import world_geography


def test_world_geography_is_continent_first_and_room_enabled(client):
    page = client.get('/world/africa').get_data(as_text=True)
    assert 'Continent → Country → County / Region → Borough / District → Postcode' in page
    assert 'Africa Room' in page
    assert 'Ghana Country Room' in page
    assert 'National anthem' in page
    assert 'Sport' in page
    assert 'Culture' in page
    assert 'Humour & fun' in page
    assert 'Open County / Region Room' in page
    assert 'Open Borough / District Room' in page
    assert 'Open Postcode Room' in page


def test_world_cup_is_preserved_as_sport_not_geography(client):
    page = client.get('/world-cup').get_data(as_text=True)
    assert 'World Cup stays inside Culture & Sport' in page
    assert 'Continents' in page


def test_country_anthem_metadata_is_title_only_and_bounded():
    assert world_geography.COUNTRY_ANTHEM_TITLES['Ghana'] == 'God Bless Our Homeland Ghana'
    assert world_geography.COUNTRY_ANTHEM_TITLES['Japan'] == 'Kimigayo'
    assert all(len(title) <= 120 for title in world_geography.COUNTRY_ANTHEM_TITLES.values())


def test_all_continents_have_culture_sport_and_fun_highlights():
    assert len(world_geography.CONTINENTS) == 6
    for continent in world_geography.CONTINENTS:
        joined = ' '.join(continent['highlights'])
        assert 'Culture' in joined
        assert any(word in joined for word in ('Sport', 'Football'))
        assert 'Humour' in joined
