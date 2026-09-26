from __future__ import annotations

from pathlib import Path

import pytest
from flask import Flask

from mission_control import certification, product_core_services, product_core_views


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



def test_commerce_core_merchant_guard_requires_certification(monkeypatch):
    monkeypatch.setattr(
        certification,
        "identity_status",
        lambda _identity_id: {"merchant": False},
    )

    with pytest.raises(PermissionError, match="certified_merchant_required"):
        product_core_views._require_certified_merchant(
            "00000000-0000-0000-0000-000000000258"
        )


def test_commerce_core_merchant_guard_fails_closed_when_store_unavailable(
    monkeypatch,
):
    def unavailable(_identity_id):
        raise certification.CertificationUnavailable(
            "certification_read_unavailable"
        )

    monkeypatch.setattr(certification, "identity_status", unavailable)

    with pytest.raises(RuntimeError, match="merchant_certification_unavailable"):
        product_core_views._require_certified_merchant(
            "00000000-0000-0000-0000-000000000258"
        )


def test_commerce_core_seller_writes_call_certified_merchant_guard():
    source = (
        Path(product_core_views.__file__).read_text(
            encoding="utf-8"
        )
    )

    storefront = source.split('def create_storefront():', 1)[1].split(
        'def create_product():', 1
    )[0]
    product = source.split('def create_product():', 1)[1].split(
        'def create_order():', 1
    )[0]

    assert "_require_certified_merchant(_identity(sync=True))" in storefront
    assert "_require_certified_merchant(_identity(sync=True))" in product
