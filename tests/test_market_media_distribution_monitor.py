from mission_control import market_media_distribution_monitor


def test_market_media_distribution_monitor_stays_partial_with_schema_and_contract(monkeypatch):
    monkeypatch.setattr(
        market_media_distribution_monitor.product_cores,
        "platform_status",
        lambda: {
            "ready": True,
            "schema_ready": True,
            "legacy_market_preserved": True,
            "blocked_external_actions": (
                "external_music_distribution",
                "payment_capture",
                "external_fulfilment_handoff",
            ),
        },
    )
    monkeypatch.setattr(
        market_media_distribution_monitor.distribution_intelligence,
        "status",
        lambda: {
            "ready": True,
            "rights_proof_required": True,
            "external_distribution_state": "locked_until_authenticated_adapter_and_receipt",
            "publishing_authority_granted": False,
            "payment_authority_granted": False,
            "external_execution_enabled": False,
        },
    )

    market, media, distribution = market_media_distribution_monitor.observations(
        "2026-09-17T15:00:00Z"
    )

    assert market["proof_state"] == "partial_proof"
    assert market["evidence"]["schema_ready"] is True
    assert market["evidence"]["storefront_activity_proven"] is False
    assert market["evidence"]["payment_capture_performed"] is False
    assert market["evidence"]["external_fulfilment_performed"] is False

    assert media["proof_state"] == "partial_proof"
    assert media["evidence"]["release_activity_proven"] is False
    assert media["evidence"]["rights_activity_proven"] is False
    assert media["evidence"]["licensed_audio_delivery"] is False
    assert media["evidence"]["royalty_payout"] is False

    assert distribution["proof_state"] == "partial_proof"
    assert distribution["evidence"]["contract_ready"] is True
    assert distribution["evidence"]["rights_proof_required"] is True
    assert distribution["evidence"]["external_distribution_locked"] is True
    assert distribution["evidence"]["external_execution_enabled"] is False
    assert distribution["evidence"]["external_delivery_receipt_proven"] is False

    for observation in (market, media, distribution):
        assert observation["external_authority"] is False
        assert observation["evidence"]["identity_scoped_data_read"] is False
        assert observation["evidence"]["read_only"] is True


def test_market_media_distribution_monitor_fails_closed_without_evidence(monkeypatch):
    monkeypatch.setattr(
        market_media_distribution_monitor.product_cores,
        "platform_status",
        lambda: {},
    )
    monkeypatch.setattr(
        market_media_distribution_monitor.distribution_intelligence,
        "status",
        lambda: {},
    )

    observations = market_media_distribution_monitor.observations(
        "2026-09-17T15:00:00Z"
    )

    assert len(observations) == 3
    for observation in observations:
        assert observation["source_timestamp"] is None
        assert observation["freshness"] == "unseen"
        assert observation["proof_state"] == "proof_required"
        assert observation["external_authority"] is False
