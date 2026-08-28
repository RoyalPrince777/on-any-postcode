from html import escape

from mission_control import products


def test_complete_spot_capability_registry_has_no_duplicates():
    validation = products.validate_spot_capabilities()

    assert validation["passed"] is True
    assert validation["errors"] == []
    assert validation["checks"] == {
        "capabilities": 18,
        "duplicate_ids": 0,
        "duplicate_names": 0,
    }
    assert len(products.LOCKED_SPOT_CAPABILITY_IDS) == 18


def test_every_spot_capability_has_a_working_read_only_route(client):
    for capability in products.PUBLIC_SPOT_CAPABILITIES:
        response = client.get(f"/the-spot/{capability['slug']}")
        page = response.get_data(as_text=True)

        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert escape(capability["name"]) in page
        assert capability["purpose"] in page
        assert "Owner:" not in page
        assert "What remains locked" not in page
        assert client.post(f"/the-spot/{capability['slug']}").status_code == 405


def test_unknown_spot_capability_fails_closed(client):
    response = client.get("/the-spot/not-approved")

    assert response.status_code == 404
    assert response.get_json() == {
        "error": {
            "code": "not_found",
            "message": "That Spot experience is unavailable.",
        }
    }


def test_spot_dashboard_lists_every_capability(client):
    page = client.get("/the-spot").get_data(as_text=True)

    assert "Everything in The Spot" in page
    for capability in products.PUBLIC_SPOT_CAPABILITIES:
        assert escape(capability["name"]) in page


def test_signal_and_postcode_room_capabilities_have_live_public_forms(client):
    signal = client.get("/the-spot/signal").get_data(as_text=True)
    rooms = client.get("/the-spot/postcode-rooms").get_data(as_text=True)

    assert 'method="post" action="/signal"' in signal
    assert 'method="post" action="/postcode-rooms"' in rooms


def test_sensitive_spot_functions_are_not_misrepresented_as_live():
    sensitive = {"postcode-rooms", "support", "market", "runner", "identity", "membership"}
    by_id = {item["id"]: item for item in products.SPOT_CAPABILITIES}

    assert all(by_id[item_id]["blocked_by"] for item_id in sensitive)
    assert all("Fully operational" not in item["status"] for item in by_id.values())
