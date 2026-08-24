from __future__ import annotations

import app as app_module


def test_signal_post_still_works(client, csrf):
    response = client.post(
        "/signal", data={**csrf, "name": "Neo", "body": "Signal"}
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/#signal")
    assert app_module.signal_posts[0] == {"name": "Neo", "body": "Signal"}


def test_room_post_still_works(client, csrf):
    response = client.post(
        "/room",
        data={
            **csrf,
            "room": "Ghana Team Room",
            "name": "Visitor",
            "message": "Hello",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/world-cup#teams")
    assert app_module.team_messages[0]["room"] == "Ghana Team Room"


def test_postcode_room_post_uses_bounded_public_store(client, csrf):
    response = client.post(
        "/postcode-rooms",
        data={
            **csrf,
            "postcode": "sw1a 1aa",
            "name": "Neighbour",
            "message": "Local update",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/the-spot/postcode-rooms?postcode=SW1A+1AA"
    )
    assert app_module.team_messages[0] == {
        "room": "SW1A 1AA Postcode Room",
        "name": "Neighbour",
        "message": "Local update",
    }


def test_flag_post_still_works(client, csrf):
    response = client.post("/flag", data={**csrf, "team": "Ghana"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/world-cup#teams")
    assert app_module.flag_counts["Ghana"] == 1


def test_myworld_post_still_works(client, csrf):
    response = client.post(
        "/myworld",
        data={**csrf, "nickname": "Visitor", "country": "Ghana"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/my-world")
    assert app_module.profiles["11111111-1111-4111-8111-111111111111"] == {
        "nickname": "Visitor",
        "postcode": "",
        "borough": "",
        "county": "",
        "country": "Ghana",
        "continent": "",
    }
