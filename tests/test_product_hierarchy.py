from mission_control import products


def test_product_hierarchy_is_unique_and_locked():
    validation = products.validate_product_hierarchy()

    assert validation["passed"] is True
    assert validation["checks"] == {
        "products": 3,
        "duplicate_ids": 0,
        "duplicate_names": 0,
        "duplicate_routes": 0,
    }
    assert [
        (item["name"], item["parent_id"])
        for item in products.PRODUCT_HIERARCHY
    ] == [
        ("The Spot", ""),
        ("The Link", "the_spot"),
        ("LinkUp", "the_link"),
    ]


def test_public_product_pages_are_read_only(client):
    for path, title in (
        ("/mission/spot", "The Spot"),
        ("/mission/the-link", "The Link"),
        ("/mission/linkup", "LinkUp"),
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert title in response.get_data(as_text=True)
        assert client.post(path).status_code == 405


def test_product_front_door_aliases_follow_the_hierarchy(client):
    assert client.get("/the-spot").headers["Location"].endswith("/mission/spot")
    assert client.get("/the-link").headers["Location"].endswith("/mission/the-link")
    assert client.get("/linkup").headers["Location"].endswith("/mission/linkup")
