"""Fail-closed OAP Entertainment contract regression tests.

No media upload, distribution, publication, migration or playback occurs.
"""
from __future__ import annotations

from flask import Flask

from mission_control import entertainment_catalogue, product_core_views

RELEASE_ID = "56dbd4cc-5598-4e57-9443-42001fd9a673"


def _row(**overrides):
    item = {
        "release_id": RELEASE_ID,
        "title": "OAP Original",
        "release_type": "single",
        "state": "PUBLISHED",
        "rights_status": "VERIFIED",
        "track_count": 1,
    }
    item.update(overrides)
    return item


def test_catalogue_reuses_owner_scoped_tune_records_without_leaking_media():
    record = _row(
        media_ref="private://original",
        url="https://unapproved.example/watch",
        owner_identity_id="private-owner",
        rights_proof=True,
        human_approval=True,
    )
    result = entertainment_catalogue.project_catalogue({"releases": [record]})
    assert result["scope"] == "authenticated_owner_tune_releases_only"
    assert result["source_organ"] == "OAP Music"
    assert result["item_count"] == 1
    item = result["items"][0]
    assert item["content_id"] == f"oap:tune:{RELEASE_ID}"
    assert item["title"] == "OAP Original"
    assert item["rights_review_state"] == "VERIFIED"
    assert item["playback_available"] is False
    assert item["playback_url"] is None
    for hidden in ("media_ref", "url", "owner_identity_id", "rights_proof", "human_approval"):
        assert hidden not in item
    assert result["public_catalogue_enabled"] is False
    assert result["other_destination_adapters_connected"] is False


def test_catalogue_rejects_malformed_and_duplicate_rows():
    rows = [
        _row(),
        _row(title="Duplicate ID"),
        _row(release_id="invalid"),
        _row(title=""),
        _row(rights_status="PUBLISH_ANYWAY"),
        _row(release_type=["single"]),
        _row(state={"bad": True}),
        _row(rights_status=["VERIFIED"]),
        _row(track_count=True),
        "not-a-record",
    ]
    result = entertainment_catalogue.project_catalogue({"releases": rows})
    assert result["item_count"] == 1
    assert result["items"][0]["title"] == "OAP Original"
    assert entertainment_catalogue.project_catalogue(None)["items"] == []
    assert entertainment_catalogue.project_catalogue({"releases": "bad"})["items"] == []


def test_rights_gate_cannot_be_opened_by_verified_status_or_caller_flags():
    item = entertainment_catalogue.project_catalogue(
        {"releases": [_row()]}
    )["items"][0]
    asserted = {**item, "rights_proof": True, "human_approval": True,
                "independent_evidence": True, "entitlement": True}
    result = entertainment_catalogue.rights_gate(asserted)
    assert result["allowed"] is False
    assert result["independent_proof_checked"] is False
    assert result["playback_authorised"] is False
    assert "independent_rights_evidence_not_connected" in result["blockers"]
    assert "media_asset_integrity_not_connected" in result["blockers"]
    assert "viewer_entitlement_not_connected" in result["blockers"]
    pending = entertainment_catalogue.rights_gate(
        {"publication_state": "DRAFT", "rights_review_state": "SELF_DECLARED"}
    )
    assert "publication_not_proven" in pending["blockers"]
    assert "rights_review_not_verified" in pending["blockers"]


def test_universal_player_is_one_inert_contract_not_a_streaming_claim():
    player = entertainment_catalogue.universal_player_contract(
        {"content_id": f"oap:tune:{RELEASE_ID}", "stream_url": "https://bad.example"}
    )
    assert player["owner"] == "OAP Player"
    assert player["mode"] == "contract_only"
    assert player["content_id"] == f"oap:tune:{RELEASE_ID}"
    assert len(player["destinations"]) == 5
    assert player["playback_enabled"] is False
    assert player["stream_url"] is None
    assert player["download_url"] is None
    assert player["entitlement_token"] is None
    assert player["publishing_authority_granted"] is False
    assert player["human_authority_final"] is True


def test_existing_media_distribution_suite_reuses_canonical_projection(monkeypatch):
    calls = []
    def owner_tune(identity):
        calls.append(identity)
        return {"organ": "OAP Music", "releases": [_row()], "playlists": []}
    monkeypatch.setattr(product_core_views.product_core_services, "tune_dashboard", owner_tune)
    monkeypatch.setattr(
        product_core_views.product_core_services,
        "commerce_dashboard",
        lambda identity: {"organ": "OAP Commerce Core", "products": [], "orders": []},
    )
    media = product_core_views._media_projection("owner-1")
    distribution = product_core_views._distribution_projection("owner-1")
    suite = product_core_views._distribution_market_media_projection("owner-1")
    for projected in (
        media["entertainment"], distribution["entertainment"],
        suite["entertainment"],
    ):
        assert projected["item_count"] == 1
        assert projected["playback_enabled"] is False
    assert calls == ["owner-1", "owner-1", "owner-1"]


def test_entertainment_route_is_authenticated_read_only():
    app = Flask(__name__)
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    rules = [
        rule for rule in app.url_map.iter_rules()
        if rule.rule == "/mission/organs/entertainment"
    ]
    assert len(rules) == 1
    assert rules[0].methods == {"GET", "HEAD", "OPTIONS"}



def test_universal_player_rejects_untrusted_content_ids_without_playback():
    valid = f"oap:tune:{RELEASE_ID}"
    for supplied in (
        "https://example.test/media.mp3",
        "oap:tune:bad",
        f"oap:tune:oap:tune:{RELEASE_ID}",
        f"oap:tune:{RELEASE_ID}/other",
        "oap:open-music:" + RELEASE_ID,
        [], {"content_id": valid}, None,
    ):
        result = entertainment_catalogue.universal_player_contract({
            "content_id": supplied,
            "rights_proof": True, "human_approval": True,
            "stream_url": "https://example.test/media.mp3",
        })
        assert result["content_id"] is None
        assert result["playback_enabled"] is False
        assert result["stream_url"] is None
        assert result["rights"]["allowed"] is False
    assert entertainment_catalogue.universal_player_contract(
        {"content_id": valid}
    )["content_id"] == valid



def test_tune_catalogue_intelligence_route_is_private_csrf_and_read_only(monkeypatch):
    from uuid import uuid4

    from mission_control import web_security

    app = Flask(__name__)
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    client = app.test_client()
    path = "/mission/organs/tune/catalogue-intelligence/preview"
    rules = [r for r in app.url_map.iter_rules() if r.rule == path]
    assert len(rules) == 1
    assert rules[0].methods == {"POST", "OPTIONS"}

    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    assert client.post(path, json={"candidates": []}).status_code == 401

    monkeypatch.setattr(web_security, "current_authenticated_user",
                        lambda: {"id": "founder"})
    monkeypatch.setattr(web_security, "private_authority_allowed",
                        lambda user: False)
    assert client.post(path, json={"candidates": []}).status_code == 403

    monkeypatch.setattr(web_security, "private_authority_allowed",
                        lambda user: True)
    monkeypatch.setattr(product_core_views, "_identity",
                        lambda: str(uuid4()))
    monkeypatch.setattr(product_core_views, "_write_allowed", lambda: False)
    assert client.post(path, json={"candidates": []}).status_code == 403

    monkeypatch.setattr(product_core_views, "_write_allowed", lambda: True)
    assert client.post(path, json={"candidates": "not-a-list"}).status_code == 400
    assert client.post(path, json={"candidates": [], "genres": ["unknown"]}).status_code == 400
    assert client.post(path, json={"candidates": [], "genres": ["Afrobeats", "Afrobeats"]}).status_code == 400
    assert client.post(path, json={"candidates": [], "licence_filter": "stream_all"}).status_code == 400
    assert client.post(path, json={"candidates": [], "vocals": "Any"}).status_code == 400
    response = client.post(path, json={"candidates": [{
        "candidate_id": str(uuid4()), "title": "Track",
        "artist": "Artist", "source_kind": "direct_artist",
        "claimed_licence": "DIRECT_PERMISSION",
        "owner_identity_id": str(uuid4()), "rights_verified": True,
        "human_release_approved": True,
        "stream_url": "https://untrusted.example/file.mp3",
    }]})
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    body = response.get_json()
    assert body["organ"] == "OAP Music"
    assert body["review_count"] == 1
    assert body["catalogue_write_performed"] is False
    assert body["audio_retrieval_performed"] is False
    lead = body["review_queue"][0]
    assert lead["playback_enabled"] is False
    assert lead["human_release_approved"] is False
    assert "stream_url" not in lead
    assert "owner_identity_id" not in lead


def test_tune_catalogue_handoff_requires_real_session_owner_release(monkeypatch):
    from uuid import uuid4

    from flask import Flask

    from mission_control import product_core_services, product_core_views, web_security

    app = Flask(__name__)
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    client = app.test_client()
    path = "/mission/organs/tune/catalogue-intelligence/review-handoff"
    owner, own_release, other_release = str(uuid4()), str(uuid4()), str(uuid4())
    candidate = {
        "candidate_id": str(uuid4()), "title": "Review lead",
        "artist": "Independent artist", "source_kind": "direct_artist",
        "claimed_licence": "DIRECT_PERMISSION",
        "rights_verified": True, "playback_enabled": True,
        "owner_identity_id": str(uuid4()),
    }
    payload = {"candidate": candidate, "release_id": own_release}
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    assert client.post(path, json=payload).status_code == 401
    monkeypatch.setattr(web_security, "current_authenticated_user",
                        lambda: {"id": "founder"})
    monkeypatch.setattr(web_security, "private_authority_allowed",
                        lambda user: False)
    assert client.post(path, json=payload).status_code == 403
    monkeypatch.setattr(web_security, "private_authority_allowed",
                        lambda user: True)
    monkeypatch.setattr(product_core_views, "_identity", lambda: owner)
    monkeypatch.setattr(product_core_views, "_write_allowed", lambda: False)
    assert client.post(path, json=payload).status_code == 403
    monkeypatch.setattr(product_core_views, "_write_allowed", lambda: True)
    assert client.post(path, json={"candidate": []}).status_code == 400
    seen = []
    def owned_projection(identity):
        seen.append(identity)
        return {"releases": [{
            "release_id": own_release, "title": "Owner release",
            "state": "DRAFT", "rights_status": "UNVERIFIED",
        }]}
    monkeypatch.setattr(product_core_services, "tune_dashboard",
                        owned_projection)
    assert client.post(path, json={**payload, "release_id": other_release}).status_code == 404
    result = client.post(path, json=payload)
    assert result.status_code == 200
    assert result.headers["Cache-Control"] == "no-store"
    body = result.get_json()
    assert seen == [owner, owner]
    assert body["owner_authenticated"] is True
    assert body["owner_bound_to_music_release"] is True
    assert body["existing_release"]["release_id"] == own_release
    assert body["independent_rights_verified"] is False
    assert body["ready_for_authenticated_handoff"] is False
    assert body["playback_enabled"] is False
    assert body["receipt_persisted"] is False
    assert body["release_created"] is False
    assert "owner_identity_id" not in body
    monkeypatch.setattr(product_core_services, "tune_dashboard",
                        lambda identity: (_ for _ in ()).throw(RuntimeError("DB offline")))
    assert client.post(path, json=payload).status_code == 503
