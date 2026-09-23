"""Open Cinema private collection: only open works and OAP originals."""
from __future__ import annotations

from mission_control import open_cinema


def test_scope_excludes_purchased_commercial_catalogue_and_invented_originals():
    result = open_cinema.private_collection_intake()
    assert result["scope"] == "founder_only_open_and_originals"
    assert result["existing_catalogue_preserved"] is True
    assert result["eligible_collections"] == [
        "open_licensed_and_public_domain", "oap_originals",
    ]
    assert result["purchased_commercial_films_in_scope"] is False
    assert result["purchased_commercial_films"] == []
    assert result["own_originals"] == []
    assert result["original_titles_received"] is False
    assert result["originals_require_embedded_rights_review"] is True
    assert "reported_purchases" not in result
    assert "other_old_films" not in result


def test_open_discovery_is_not_free_to_watch_or_automatic_global_licence():
    result = open_cinema.private_collection_intake()
    assert {item["source"] for item in result["free_catalogue_discovery"]} == {
        "wikimedia_commons", "library_of_congress", "internet_archive",
    }
    assert result["permitted_open_claims_for_review"] == [
        "PUBLIC_DOMAIN", "CC0", "CC_BY", "CC_BY_SA",
    ]
    assert result["free_to_watch_alone_qualifies"] is False
    for item in result["free_catalogue_discovery"]:
        assert item["title_clearance_state"] == "per_title_evidence_required"
        assert item["films_imported"] == 0
        assert item["licences_acquired"] is False
        assert item["playback_enabled"] is False
    assert result["public_catalogue_enabled"] is False
    assert result["playback_enabled"] is False
    assert result["payments_enabled"] is False
    assert result["media_import_performed"] is False


def test_collections_route_rejects_anonymous_user(anonymous_client):
    url = "/mission/organs/entertainment/open-cinema/private-collections"
    response = anonymous_client.get(url)
    assert response.status_code in (401, 403)
    assert response.headers.get("Location", "").find("stream") < 0
    assert anonymous_client.post(url).status_code in (404, 405)
