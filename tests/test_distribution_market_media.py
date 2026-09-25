from flask import Flask

from mission_control import product_core_views


def test_distribution_market_media_routes_are_registered():
    app = Flask(__name__)
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    rules = {rule.rule for rule in app.url_map.iter_rules()}

    assert "/mission/organs/media" in rules
    assert "/mission/organs/market" in rules
    assert "/mission/organs/distribution" in rules
    assert "/mission/organs/distribution-market-media" in rules
    assert "/mission/organs/distribution-market-media/dashboard" in rules


def test_media_projection_uses_real_tune_state(monkeypatch):
    monkeypatch.setattr(
        product_core_views.product_core_services,
        "tune_dashboard",
        lambda identity: {
            "organ": "OAP Music",
            "releases": [{"release_id": "release-1", "state": "DRAFT"}],
            "playlists": [{"playlist_id": "playlist-1"}],
        },
    )

    result = product_core_views._media_projection("owner-1")

    assert result["organ"] == "OAP Media"
    assert result["release_count"] == 1
    assert result["playlist_count"] == 1
    assert result["external_distribution"] is False
    assert result["licensed_audio_delivery"] is False


def test_market_projection_uses_real_commerce_state(monkeypatch):
    monkeypatch.setattr(
        product_core_views.product_core_services,
        "commerce_dashboard",
        lambda identity: {
            "organ": "OAP Commerce Core",
            "storefront": {"storefront_id": "store-1"},
            "products": [{"product_id": "product-1"}],
            "orders": [{"order_id": "order-1"}],
        },
    )

    result = product_core_views._market_projection("owner-1")

    assert result["organ"] == "OAP Market"
    assert result["storefront"]["storefront_id"] == "store-1"
    assert len(result["products"]) == 1
    assert len(result["orders"]) == 1
    assert result["payment_capture_performed"] is False
    assert result["external_fulfilment_performed"] is False


def test_distribution_projection_stays_fail_closed(monkeypatch):
    monkeypatch.setattr(
        product_core_views.product_core_services,
        "tune_dashboard",
        lambda identity: {
            "organ": "OAP Music",
            "releases": [{"release_id": "release-1", "rights_status": "PENDING"}],
            "playlists": [],
        },
    )
    monkeypatch.setattr(
        product_core_views.distribution_intelligence,
        "status",
        lambda: {
            "external_distribution_state": (
                "locked_until_authenticated_adapter_and_receipt"
            ),
            "external_execution_enabled": False,
        },
    )

    result = product_core_views._distribution_projection("owner-1")

    assert result["organ"] == "OAP Distribution"
    assert result["release_count"] == 1
    assert result["external_execution_enabled"] is False
    assert result["external_distribution_state"] == (
        "locked_until_authenticated_adapter_and_receipt"
    )
    assert result["rights_proof_required"] is True


def test_music_review_handoff_binds_to_authenticated_owner_release(monkeypatch):
    from uuid import uuid4

    app = Flask(__name__)
    release_id = str(uuid4())
    candidate_id = str(uuid4())
    monkeypatch.setattr(product_core_views, "_write_allowed", lambda: True)
    monkeypatch.setattr(product_core_views, "_identity", lambda **kwargs: "11111111-1111-1111-1111-111111111111")
    monkeypatch.setattr(
        product_core_views.product_core_services,
        "tune_dashboard",
        lambda identity: {
            "organ": "OAP Music",
            "releases": [{
                "release_id": release_id,
                "title": "Owner release",
                "release_type": "single",
                "state": "DRAFT",
                "rights_status": "REVIEW_REQUIRED",
            }],
            "playlists": [],
        },
    )
    payload = {
        "candidate": {
            "candidate_id": candidate_id,
            "title": "Candidate",
            "artist": "Artist",
            "source_kind": "free_music_archive",
            "claimed_licence": "CC_BY",
            "source_page_url": "https://freemusicarchive.org/music/artist/candidate/",
        },
        "release_id": release_id,
    }
    with app.test_request_context("/", method="POST", json=payload):
        response = product_core_views.tune_catalogue_review_handoff()
    body = response.get_json()

    assert response.status_code == 200
    assert body["owner_authenticated"] is True
    assert body["owner_bound_to_music_release"] is True
    assert body["existing_release"]["release_id"] == release_id
    assert body["independent_rights_verified"] is False
    assert body["receipt_persisted"] is False
    assert body["release_created"] is False
    assert body["playback_enabled"] is False


def test_music_review_handoff_rejects_wrong_owner_release(monkeypatch):
    from uuid import uuid4

    app = Flask(__name__)
    release_id = str(uuid4())
    candidate_id = str(uuid4())
    monkeypatch.setattr(product_core_views, "_write_allowed", lambda: True)
    monkeypatch.setattr(product_core_views, "_identity", lambda **kwargs: "11111111-1111-1111-1111-111111111111")
    monkeypatch.setattr(
        product_core_views.product_core_services,
        "tune_dashboard",
        lambda identity: {"organ": "OAP Music", "releases": [], "playlists": []},
    )
    payload = {
        "candidate": {
            "candidate_id": candidate_id,
            "title": "Candidate",
            "artist": "Artist",
            "source_kind": "free_music_archive",
            "claimed_licence": "CC_BY",
            "source_page_url": "https://freemusicarchive.org/music/artist/candidate/",
        },
        "release_id": release_id,
    }
    with app.test_request_context("/", method="POST", json=payload):
        response = product_core_views.tune_catalogue_review_handoff()

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"


def test_music_review_handoff_fails_closed_on_csrf_before_store_read(monkeypatch):
    app = Flask(__name__)
    touched = {"store": False}
    monkeypatch.setattr(product_core_views, "_write_allowed", lambda: False)

    def forbidden_store(identity):
        touched["store"] = True
        raise AssertionError("store must not be read after CSRF failure")

    monkeypatch.setattr(
        product_core_views.product_core_services,
        "tune_dashboard",
        forbidden_store,
    )
    with app.test_request_context("/", method="POST", json={"candidate": {}, "release_id": "x"}):
        response = product_core_views.tune_catalogue_review_handoff()

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"
    assert touched["store"] is False
