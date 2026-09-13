from html import escape

from mission_control import products


def test_complete_spot_capability_registry_has_no_duplicates():
    validation = products.validate_spot_capabilities()

    assert validation["passed"] is True
    assert validation["errors"] == []
    assert validation["checks"] == {
        "capabilities": 26,
        "duplicate_ids": 0,
        "duplicate_names": 0,
    }
    assert len(products.LOCKED_SPOT_CAPABILITY_IDS) == 26


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


def test_spot_home_is_pulse_first_and_uses_locked_core_order(client):
    page = client.get("/the-spot").get_data(as_text=True)

    assert "📡 Pulse" in page
    assert "See what’s happening around you." in page
    assert 'href="/pulse"' in page
    assert "📣 Drop a Signal" in page

    ordered_labels = (
        "🚩 Flag Vote",
        "🔗 The Link",
        "📰 OAP Chronicle",
        "🌿 Nature",
        "🎪 Activity / Adventure",
        "🧭 Explorer",
        "🌍 World Rooms",
        "🏪 Market",
        "👤 My World",
    )
    positions = [page.index(label) for label in ordered_labels]
    assert positions == sorted(positions)

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


def test_flag_vote_chronicle_and_nature_reuse_real_existing_paths(client):
    flag_vote = client.get("/the-spot/flag-vote").get_data(as_text=True)
    chronicle = client.get("/the-spot/news").get_data(as_text=True)
    nature = client.get("/the-spot/nature").get_data(as_text=True)

    assert "Throw Your Flag Up" in flag_vote
    assert 'method="post" action="/flag"' in flag_vote
    assert "non-binding public support" in flag_vote
    assert "binding vote" in flag_vote

    assert "OAP Chronicle" in chronicle
    assert 'href="/pulse"' in chronicle
    assert 'href="/the-spot/signal"' in chronicle
    assert "does not invent a second newsroom feed" in chronicle

    assert "OAP Nature" in nature
    assert "Earth is our turf" in nature
    assert 'href="/the-spot/maps-weather-travel"' in nature
    assert "wider environmental alerts" in nature


def test_booking_maps_and_movement_are_first_class_spot_front_doors(client):
    page = client.get("/the-spot").get_data(as_text=True)

    assert "Booking · Maps · Movement" in page
    assert "🗺️ Maps" in page
    assert "📅 Booking" in page
    assert "🚶 Movement" in page
    assert 'href="/travel/direct"' in page
    assert "quote, hold and human-confirmed reservation request" in page
    assert "supplier confirmation is required before a booking is called confirmed" in page.lower()
    assert "Payment capture, automatic dispatch and fake-live route claims remain blocked" in page


def test_booking_and_maps_public_front_doors_are_reachable(client):
    maps = client.get("/atlas")
    booking = client.get("/travel/direct")

    assert maps.status_code == 200
    assert booking.status_code == 200
    assert "On Any Place" in maps.get_data(as_text=True)
    assert "OAP Direct" in booking.get_data(as_text=True)


def test_signal_and_world_room_capabilities_have_live_public_forms(client):
    signal = client.get("/the-spot/signal").get_data(as_text=True)
    rooms = client.get("/the-spot/postcode-rooms").get_data(as_text=True)

    assert 'method="post" action="/signal"' in signal
    assert 'method="post" action="/postcode-rooms"' in rooms
    assert "World Rooms" in rooms
    assert "Worldwide Empire layer" in rooms


def test_public_capabilities_do_not_show_a_blanket_password_prompt(client):
    public_only = (
        "flag-vote",
        "signal",
        "news",
        "nature",
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


def test_spot_public_language_uses_empire_not_community():
    public_copy = " ".join(
        f"{item['name']} {item['purpose']}"
        for item in products.PUBLIC_SPOT_CAPABILITIES
    )
    assert "Community Power" not in public_copy
    assert "Community Support" not in public_copy
    assert "community commerce" not in public_copy
    assert "Empire Power" in public_copy
    assert "Empire Support" in public_copy


def test_sensitive_spot_functions_are_not_misrepresented_as_live():
    sensitive = {
        "flag-vote",
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