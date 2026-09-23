"""Bounded OAP Open Cinema candidate connector proof; no licences minted."""
from __future__ import annotations

from uuid import uuid4

from mission_control import open_cinema

GOOD = {
    "candidate_id": str(uuid4()),
    "source": "wikimedia_commons",
    "title": "  Candidate film  ",
    "licence_claim": "CC_BY",
    "reference_url": "https://commons.wikimedia.org/wiki/File:Candidate.webm",
}


def test_candidate_is_private_and_never_grants_rights_from_user_claims():
    item = open_cinema.candidate({**GOOD, "rights_verified": True,
                                  "published": True, "stream_url": "https://evil.test/film"})
    assert item["title"] == "Candidate film"
    assert item["source_reference"] == GOOD["reference_url"]
    assert item["licence_claim"] == "CC_BY"
    assert item["rights_evidence_checked"] is False
    assert item["uk_cleared"] is False
    assert item["ghana_cleared"] is False
    assert item["playback_enabled"] is False
    assert item["stream_url"] is None
    assert "rights_verified" not in item
    assert "published" not in item


def test_reject_unknown_sources_url_tricks_and_invalid_licence():
    for mutation in (
        {"source": "netflix"},
        {"licence_claim": "CC_BY_NC"},
        {"reference_url": "http://commons.wikimedia.org/wiki/File:x"},
        {"reference_url": "https://commons.wikimedia.org.evil.test/wiki/File:x"},
        {"reference_url": "https://evil.test/x"},
        {"reference_url": "https://commons.wikimedia.org@evil.test/wiki/File:x"},
        {"reference_url": "https://commons.wikimedia.org/wiki/File:x?stream=1"},
        {"reference_url": "https://commons.wikimedia.org:abc/wiki/File:x"},
    ):
        assert open_cinema.candidate({**GOOD, **mutation}) is None


def test_only_allowlisted_fields_dedupe_bounded_and_no_execution():
    raw = {**GOOD, "media_bytes": "secret", "signed_contract": "claim"}
    result = open_cinema.preview([raw, raw, {"nonsense": True}])
    assert result["item_count"] == 1
    assert len(result["items"]) == 1
    assert "media_bytes" not in result["items"][0]
    assert "signed_contract" not in result["items"][0]
    for key in ("licences_acquired", "playback_enabled", "public_catalogue_enabled",
                "publication_performed", "media_import_performed",
                "network_requests_performed", "persistence_performed"):
        assert result[key] is False
    assert open_cinema.preview([raw] * 75)["item_count"] == 1


def test_direct_creator_is_lead_not_permission():
    item = open_cinema.candidate({
        "candidate_id": str(uuid4()), "source": "direct_creator",
        "title": "Indie film", "licence_claim": "DIRECT_PERMISSION",
        "reference_url": "https://untrusted.invalid/private",
        "work_origin": "oap_original",
    })
    assert item["source_reference"] is None
    assert item["rights_evidence_checked"] is False
    assert item["collection"] == "oap_originals"
    assert item["creator_ownership_verified"] is False
    assert item["embedded_rights_verified"] is False


def test_scope_rejects_commercial_purchase_and_generic_permissions():
    for mutation in (
        {"source": "direct_creator", "licence_claim": "DIRECT_PERMISSION"},
        {"source": "direct_creator", "licence_claim": "DIRECT_PERMISSION",
         "work_origin": "purchased_commercial"},
        {"source": "direct_creator", "licence_claim": "CC_BY",
         "work_origin": "oap_original"},
        {"source": "wikimedia_commons", "licence_claim": "DIRECT_PERMISSION"},
    ):
        candidate = {**GOOD, **mutation}
        assert open_cinema.candidate(candidate) is None


def test_existing_auth_boundary_on_private_preview(anonymous_client):
    url = "/mission/organs/entertainment/open-cinema/preview"
    assert anonymous_client.post(url, json={"candidates": [GOOD]}).status_code in (401, 403)
    assert anonymous_client.get(url).status_code in (404, 405)


def test_private_preview_no_unauthenticated_write(client):
    url = "/mission/organs/entertainment/open-cinema/preview"
    assert client.post(url, json={"candidates": [GOOD]}).status_code in (401, 403)
    assert client.get(url).status_code in (404, 405)


def test_candidate_preview_has_no_source_fetch_or_media_delivery():
    from pathlib import Path
    source = Path("mission_control/open_cinema.py").read_text()
    for forbidden in ("requests.get(", "urlopen(", "httpx.", "subprocess.", "send_file(",
                      "render_template(", "storage.write(", "media_ref"):
        assert forbidden not in source
