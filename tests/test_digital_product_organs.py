from __future__ import annotations

from flask import Flask
import pytest

from mission_control import product_core_services, product_core_views


def test_product_organ_blueprint_exposes_first_party_workflows_without_external_edges():
    app = Flask(__name__)
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    rules = {
        rule.rule: set(rule.methods)
        for rule in app.url_map.iter_rules()
        if rule.rule.startswith("/mission/organs")
    }

    assert rules["/mission/organs/status"] >= {"GET"}
    assert rules["/mission/organs/tune"] >= {"GET"}
    assert rules["/mission/organs/tune/releases"] >= {"POST"}
    assert rules["/mission/organs/tune/releases/<release_id>/tracks"] >= {"POST"}
    assert rules["/mission/organs/tune/releases/<release_id>/review"] >= {"POST"}
    assert rules["/mission/organs/tune/playlists"] >= {"POST"}
    assert rules["/mission/organs/tune/playlists/<playlist_id>/tracks"] >= {"POST"}
    assert rules["/mission/organs/commerce"] >= {"GET"}
    assert rules["/mission/organs/commerce/storefront"] >= {"POST"}
    assert rules["/mission/organs/commerce/products"] >= {"POST"}
    assert rules["/mission/organs/commerce/orders"] >= {"POST"}
    assert rules["/mission/organs/post"] >= {"GET"}
    assert rules["/mission/organs/post/requests"] >= {"POST"}
    assert rules["/mission/organs/post/parcels"] >= {"POST"}

    joined = " ".join(rules).casefold()
    for forbidden in (
        "capture-payment",
        "money-transfer",
        "royalty-payout",
        "distribute-external",
        "carrier-handoff",
        "activate-post-office",
    ):
        assert forbidden not in joined


def test_combined_organ_status_is_read_projection(monkeypatch):
    monkeypatch.setattr(
        product_core_services.product_cores,
        "platform_status",
        lambda: {"ready": True, "independent_external_execution": False},
    )
    monkeypatch.setattr(
        product_core_services,
        "tune_dashboard",
        lambda identity: {"organ": "OAP Tune Core", "identity": str(identity)},
    )
    monkeypatch.setattr(
        product_core_services,
        "commerce_dashboard",
        lambda identity: {"organ": "OAP Commerce Core", "identity": str(identity)},
    )
    monkeypatch.setattr(
        product_core_services,
        "post_dashboard",
        lambda identity: {"organ": "OAP Post Core", "identity": str(identity)},
    )

    result = product_core_services.organ_status(
        "00000000-0000-0000-0000-000000000258"
    )

    assert result["platform"]["ready"] is True
    assert result["tune"]["organ"] == "OAP Tune Core"
    assert result["commerce"]["organ"] == "OAP Commerce Core"
    assert result["post"]["organ"] == "OAP Post Core"
    assert result["consequential_action"] is False


def test_playlist_write_rejects_invalid_identity_or_position_before_store_access():
    with pytest.raises(ValueError, match="invalid_owner_identity_id"):
        product_core_services.add_playlist_track(
            owner_identity_id="not-a-uuid",
            playlist_id="00000000-0000-0000-0000-000000000001",
            track_id="00000000-0000-0000-0000-000000000002",
            position=1,
        )

    with pytest.raises(ValueError, match="invalid_playlist_position"):
        product_core_services.add_playlist_track(
            owner_identity_id="00000000-0000-0000-0000-000000000258",
            playlist_id="00000000-0000-0000-0000-000000000001",
            track_id="00000000-0000-0000-0000-000000000002",
            position=0,
        )
