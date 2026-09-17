from mission_control import coherent_automation, link_monitor, link_realtime, linkup


def test_link_monitor_exposes_protected_runtime_without_fake_live_activity(monkeypatch):
    monkeypatch.setattr(linkup, "validate_link_scope", lambda: {"passed": True, "checks": {}})
    monkeypatch.setattr(
        linkup,
        "PROTECTED_LINK_RUNTIME",
        {
            "authenticated_identity_required": True,
            "csrf_required_for_mutations": True,
            "sender_recipient_scope": True,
            "message_persistence": "Postgres Communications store",
            "rate_limit_enabled": True,
            "guardian_message_screening": True,
            "read_receipts": True,
            "public_message_projection": False,
            "human_authority_final": True,
        },
    )
    monkeypatch.setattr(
        link_realtime,
        "capability_state",
        lambda runtime=None: [
            {"id": "voice", "ready": False, "missing": ["media_store"]},
            {"id": "around_now", "ready": False, "missing": ["presence_store"]},
        ],
    )

    observation = link_monitor.observation("2026-09-17T14:00:00Z")

    assert observation["id"] == "the_link_link_up"
    assert observation["proof_state"] == "partial_proof"
    assert observation["source_timestamp"] is None
    assert observation["evidence"]["protected_runtime_ready"] is True
    assert observation["evidence"]["postgres_message_persistence_declared"] is True
    assert observation["evidence"]["live_message_activity_proven"] is False
    assert observation["evidence"]["delivery_activity_proven"] is False
    assert observation["evidence"]["read_activity_proven"] is False
    assert observation["evidence"]["around_now_live_proven"] is False
    assert observation["evidence"]["live_spot_live_proven"] is False
    assert observation["evidence"]["reads_message_content"] is False
    assert observation["evidence"]["reads_participant_identity"] is False
    assert observation["evidence"]["reads_location"] is False


def test_signal_monitor_includes_link_up_as_fifth_lane(monkeypatch):
    monkeypatch.setattr(
        link_monitor,
        "observation",
        lambda observed_at: {
            "id": "the_link_link_up",
            "name": "The Link / Link Up Evidence",
            "source": "mission_control.linkup + mission_control.link_realtime",
            "source_timestamp": None,
            "observed_at": observed_at,
            "freshness": "runtime_contract_only",
            "freshness_window_seconds": 0,
            "evidence": {"protected_runtime_ready": True},
            "proof_state": "partial_proof",
            "external_authority": False,
        },
    )

    monitor = coherent_automation.operational_monitor()
    observation = monitor["observations"][4]

    assert monitor["observation_count"] == 5
    assert observation["id"] == "the_link_link_up"
    assert observation["signal"]["id"] == "warning"
    assert observation["proof_state"] == "partial_proof"
    assert monitor["execution_allowed"] is False
    assert monitor["human_authority_final"] is True
