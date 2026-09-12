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
            "organ": "OAP Tune Core",
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
            "organ": "OAP Tune Core",
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
