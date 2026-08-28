from __future__ import annotations

import json

from mission_control import languages


def test_language_hub_has_seven_continents_and_bounded_local_content():
    validation = languages.validate_language_hub()

    assert validation == {
        "passed": True,
        "errors": [],
        "checks": {
            "continents": 7,
            "starter_lessons": 7,
            "conjugation_drills": 4,
            "south_london_resources": 4,
            "external_runtime_calls": 0,
        },
    }
    assert {item["id"] for item in languages.CONTINENTS} == {
        "africa",
        "asia",
        "europe",
        "north-america",
        "south-america",
        "oceania",
        "antarctica",
    }
    assert all(value is False for value in languages.PUBLIC_BOUNDARY.values())


def test_each_continent_has_one_live_starter_lesson_and_language_catalogue():
    lessons = {item["id"]: item for item in languages.STARTER_LESSONS}

    for continent in languages.CONTINENTS:
        lesson = lessons[continent["featured_lesson_id"]]
        assert lesson["continent_id"] == continent["id"]
        assert len(lesson["phrases"]) == 3
        assert len(continent["languages"]) >= 4


def test_language_hub_validation_fails_closed_for_incomplete_content():
    incomplete_lessons = tuple(
        item for item in languages.STARTER_LESSONS if item["continent_id"] != "asia"
    )
    unsafe_resources = (
        *languages.SOUTH_LONDON_RESOURCES[:-1],
        {
            "borough": "Unknown",
            "name": "Unreviewed directory",
            "purpose": "Unreviewed link",
            "url": "https://example.com/languages",
        },
    )

    incomplete = languages.validate_language_hub(lessons=incomplete_lessons)
    unsafe = languages.validate_language_hub(resources=unsafe_resources)

    assert incomplete["passed"] is False
    assert "Every continent must have exactly one starter lesson" in incomplete["errors"]
    assert unsafe["passed"] is False
    assert any("Unapproved South London resource" in item for item in unsafe["errors"])


def test_language_routes_are_public_read_only_and_consistent(anonymous_client):
    for path in ("/languages", "/world/languages", "/the-spot/languages"):
        response = anonymous_client.get(path)
        page = response.get_data(as_text=True)

        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert "World Languages" in page
        assert "Seven continents" in page
        assert anonymous_client.post(path).status_code == 405


def test_continent_and_lesson_selection_use_only_canonical_values(client):
    oceania = client.get(
        "/world/languages", query_string={"continent": "oceania"}
    ).get_data(as_text=True)
    maori = client.get(
        "/world/languages", query_string={"lesson": "oceania-maori"}
    ).get_data(as_text=True)
    attack = '<script>alert("language")</script>'
    invalid = client.get(
        "/world/languages", query_string={"continent": attack, "lesson": attack}
    ).get_data(as_text=True)

    assert 'data-continent="oceania"' in oceania
    assert "Kia ora" in oceania
    assert "Kei te ako au i te reo Māori" in maori
    assert attack not in invalid
    assert "&lt;script&gt;" not in invalid
    assert 'data-continent="africa"' in invalid
    assert "Medaase" in invalid


def test_conjugation_drill_is_deterministic_and_does_not_accept_free_text(client):
    page = client.get(
        "/world/languages", query_string={"drill": "spanish-aprender"}
    ).get_data(as_text=True)

    assert 'data-drill="spanish-aprender"' in page
    assert "Present indicative" in page
    assert "aprendo" in page
    assert "aprendemos" in page
    assert 'method="post"' not in page.casefold()
    assert "api." not in page.casefold()
    assert "<iframe" not in page.casefold()
    assert "<script" not in page.casefold()


def test_public_projection_contains_no_private_or_message_data():
    serialized = json.dumps(languages.get_public_language_hub()).casefold()

    for private_key in (
        "member_id",
        "email_address",
        "conversation_id",
        "message_body",
        "precise_location",
        "audio_recording",
        "password",
        "token",
    ):
        assert private_key not in serialized
    assert '"phase_two_active": false' in serialized


def test_south_london_links_are_official_and_review_dated():
    projection = languages.get_public_language_hub()

    assert projection["resources_reviewed_on"] == "2026-08-28"
    assert {item["borough"] for item in projection["resources"]} == {
        "Lewisham",
        "Lambeth",
        "Southwark",
        "Croydon",
    }
    assert all(item["url"].startswith("https://") for item in projection["resources"])
