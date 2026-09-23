"""Private catalogue intake: no purchase or free-source claim becomes rights."""
from __future__ import annotations

from mission_control import open_cinema


def test_reported_purchases_are_private_unverified_unplayable():
    result = open_cinema.private_collection_intake()
    assert result["scope"] == "founder_only_private_editorial_intake"
    assert result["existing_catalogue_preserved"] is True
    assert [(item["title"], item["kind"]) for item in result["reported_purchases"]] == [
        ("The Wire", "television_series"),
        ("Friday", "feature_film_1995"),
    ]
    for item in result["reported_purchases"]:
        assert item["purchase_receipt_checked"] is False
        assert item["oap_distribution_licence_verified"] is False
        assert item["territories_licensed"] == []
        assert item["public_catalogue_enabled"] is False
        assert item["playback_enabled"] is False
        assert item["stream_url"] is None
        assert item["download_url"] is None


def test_no_invented_older_titles_or_automatic_free_licences():
    result = open_cinema.private_collection_intake()
    assert result["other_old_film_titles_received"] is False
    assert result["other_old_films"] == []
    assert {item["source"] for item in result["free_catalogue_discovery"]} == set(
        open_cinema.SOURCES
    )
    for item in result["free_catalogue_discovery"]:
        assert item["films_imported"] == 0
        assert item["licences_acquired"] is False
        assert item["playback_enabled"] is False
    assert result["public_catalogue_enabled"] is False
    assert result["payments_enabled"] is False
    assert result["media_import_performed"] is False


def test_collections_route_rejects_anonymous_user(anonymous_client):
    url = "/mission/organs/entertainment/open-cinema/private-collections"
    response = anonymous_client.get(url)
    assert response.status_code in (401, 403)
    assert response.headers.get("Location", "").find("stream") < 0
    assert anonymous_client.post(url).status_code in (404, 405)
