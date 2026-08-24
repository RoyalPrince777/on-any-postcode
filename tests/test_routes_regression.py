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
    assert response.headers["Location"].endswith("/#teams")
    assert app_module.team_messages[0]["room"] == "Ghana Team Room"


def test_flag_post_still_works(client, csrf):
    response = client.post("/flag", data={**csrf, "team": "Ghana"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/#teams")
    assert app_module.flag_counts["Ghana"] == 1


def test_myworld_post_still_works(client, csrf):
    response = client.post(
        "/myworld",
        data={**csrf, "nickname": "Visitor", "country": "Ghana"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/#myworld")
    assert app_module.profiles[0] == {"nickname": "Visitor", "country": "Ghana"}
