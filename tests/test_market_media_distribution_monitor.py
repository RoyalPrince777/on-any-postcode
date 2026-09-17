from mission_control import coherent_automation


def test_market_media_distribution_reads_authenticated_first_party_state(monkeypatch):
    monkeypatch.setattr(
        coherent_automation.web_security,
        "authenticated_identity",
        lambda: "founder-1",
    )
    monkeypatch.setattr(
        coherent_automation.product_core_services,
        "tune_dashboard",
        lambda identity: {
            "organ": "OAP Tune Core",
            "releases": [{"release_id": "release-1"}],
            "playlists": [{"playlist_id": "playlist-1"}],
        },
    )
    monkeypatch.setattr(
        coherent_automation.product_core_services,
        "commerce_dashboard",
        lambda identity: {
            "organ": "OAP Commerce Core",
            "storefront": {"storefront_id": "store-1"},
            "products": [{"product_id": "product-1"}],
            "orders": [{"order_id": "order-1"}],
        },
    )
    monkeypatch.setattr(
        coherent_automation.distribution_intelligence,
        "status",
        lambda: {
            "external_distribution_state": (
                "locked_until_authenticated_adapter_and_receipt"
            ),
            "external_execution_enabled": False,
        },
    )

    evidence = coherent_automation._market_media_distribution_evidence(
        "2026-09-17T15:00:00Z"
    )

    assert evidence["state"] == "authenticated_first_party_read"
    assert evidence["runtime_read_performed"] is True
    assert evidence["storefront_present"] is True
    assert evidence["product_count"] == 1
    assert evidence["order_intent_count"] == 1
    assert evidence["release_count"] == 1
    assert evidence["playlist_count"] == 1
    assert evidence["payment_capture_performed"] is False
    assert evidence["external_fulfilment_performed"] is False
    assert evidence["licensed_audio_delivery"] is False
    assert evidence["external_distribution"] is False
    assert evidence["external_execution_enabled"] is False
    assert evidence["rights_proof_required"] is True
    assert evidence["no_private_payload_projection"] is True
    assert evidence["hidden_tracking"] is False
    assert evidence["human_authority_final"] is True


def test_market_media_distribution_fails_closed_without_auth(monkeypatch):
    def deny():
        raise PermissionError("authentication_required")

    monkeypatch.setattr(
        coherent_automation.web_security,
        "authenticated_identity",
        deny,
    )

    evidence = coherent_automation._market_media_distribution_evidence(
        "2026-09-17T15:00:00Z"
    )

    assert evidence["state"] == "authentication_or_store_required"
    assert evidence["runtime_read_performed"] is False
    assert evidence["product_count"] is None
    assert evidence["release_count"] is None
    assert evidence["payment_capture_performed"] is False
    assert evidence["external_distribution"] is False
    assert evidence["no_private_payload_projection"] is True
    assert evidence["human_authority_final"] is True
