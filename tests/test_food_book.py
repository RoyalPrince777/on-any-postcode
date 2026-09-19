"""The Food Book stays inside SMI's authenticated boundary."""


def test_signed_in_member_can_open_food_book(client):
    response = client.get('/mission/food-book')
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'Vegetables, vitamins &amp; your body' in body or 'Vegetables, vitamins & your body' in body
    assert 'data-area="eyes"' in body
    assert 'Sweet pepper' in body
    assert response.headers['Cache-Control'] == 'no-store'


def test_anonymous_reader_cannot_open_food_book(anonymous_client):
    response = anonymous_client.get('/mission/food-book', follow_redirects=False)
    assert response.status_code in (302, 303, 401, 403)
    assert 'Vegetables, vitamins' not in response.get_data(as_text=True)
