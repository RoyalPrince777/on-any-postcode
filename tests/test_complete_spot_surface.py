from html import escape

from mission_control import products


def test_complete_spot_capability_registry_has_no_duplicates():
    validation = products.validate_spot_capabilities()

    assert validation["passed"] is True
    assert validation["errors"] == []
    assert validation["checks"] == {
        "capabilities": 23,
        "duplicate_ids": 0,
        "duplicate_names": 0,
    }
    assert len(products.LOCKED_SPOT_CAPABILITY_IDS) == 23


def test_every_spot_capability_has_a_working_read_only_route(client):
    for capability in products.PUBLIC_SPOT_CAPABILITIES:
        response = client.get(f"/the-spot/{capability['slug']}")
        page = response.get_data(as_text=True)

        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert escape(capability["name"]) in page
        # Pulse, Carnival and World Languages own richer canonical feature templates;
        # generic Spot capabilities render their exact public registry purpose.
        if capability["slug"] not in {"pulse", "carnival", "languages"}:
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


def test_spot_home_is_pulse_first_and_keeps_secondary_features_out_of_the_way(client):
    page = client.get("/the-spot").get_data(as_text=True)

    assert "📡 Pulse" in page
    assert "See what’s happening around you." in page
    assert 'href="/pulse"' in page
    assert "📣 Signal" in page
    assert "🔗 The Link" in page
    assert "🎪 Activity" in page
    assert "🏪 Market" in page
    assert "🧭 Explorer" in page
    assert "🌍 World Rooms" in page
    assert "🎵 OAP Music" in page
    assert "▶️ OAP Player" in page
    assert "📻 OAP Radio" in page
    assert "📦 OAP Distribution" in page
    assert "Streams build attention" in page
    assert "More" in page
    assert "Carnival Intelligence" not in page
    assert "LinkUp" not in page
    assert "group conversation" not in page
    assert "Your local dashboard" not in page
    assert "Open what you need" not in page


def test_signal_and_world_room_capabilities_have_live_public_forms(client):
    signal = client.get("/the-spot/signal").get_data(as_text=True)
    rooms = client.get("/the-spot/postcode-rooms").get_data(as_text=True)

    assert 'method="post" action="/signal"' in signal
    assert 'method="post" action="/postcode-rooms"' in rooms
    assert "World Rooms" in rooms


def test_public_capabilities_do_not_show_a_blanket_password_prompt(client):
    public_only = (
        "signal",
        "postcode-rooms",
        "events",
        "discovery",
        "businesses",
        "creators",
        "community-progress",
        "support",
        "maps-weather-travel",
        "music",
        "player",
        "radio",
        "distribution",
        "movement-delivery",
        "safety",
        "tv-media",
        "membership",
    )
    for slug in public_only:
        page = client.get(f"/the-spot/{slug}").get_data(as_text=True)
        assert "Sign in to personalise this part of OAP" not in page

    pulse = client.get("/pulse").get_data(as_text=True)
    assert "Sign in to personalise this part of OAP" not in pulse

    spot = client.get("/the-spot").get_data(as_text=True)
    assert "Enter My World" not in spot
    assert "Sign-in appears only when a protected action actually needs it" not in spot


def test_sensitive_spot_functions_are_not_misrepresented_as_live():
    sensitive = {
        "postcode-rooms",
        "support",
        "market",
        "music",
        "player",
        "radio",
        "distribution",
        "runner",
        "identity",
        "membership",
    }
    by_id = {item["id"]: item for item in products.SPOT_CAPABILITIES}

    assert all(by_id[item_id]["blocked_by"] for item_id in sensitive)
    assert all("Fully operational" not in item["status"] for item in by_id.values())


def test_oap_media_stack_rejects_stream_money_dependency():
    by_id = {item["id"]: item for item in products.SPOT_CAPABILITIES}

    assert by_id["music"]["owner"] == "OAP Music / Media"
    assert by_id["player"]["name"] == "OAP Player"
    assert "stream-money dependency rejected" in by_id["player"]["status"]
    assert by_id["radio"]["name"] == "OAP Radio"
    assert by_id["distribution"]["owner"] == "OAP Music / Media"
    assert "release engine" in by_id["distribution"]["purpose"]
    assert "External Spotify" in by_id["distribution"]["blocked_by"]
