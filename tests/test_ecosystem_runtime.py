from mission_control import ecosystem_runtime, smi_receipt_backend


def test_automatic_internal_ingestion_builds_real_runtime_signals() -> None:
    signals = ecosystem_runtime.collect_internal_signals()

    assert len(signals) == 7
    assert all(signal["source"] == "oap_intelligence_runtime_proof" for signal in signals)
    assert all(signal["truth_state"] == "observed" for signal in signals)
    assert all(signal["confidence"] == 100 for signal in signals)


def test_pressure_scoring_covers_all_nine_dimensions() -> None:
    scores = ecosystem_runtime.auto_pressure_scores(
        (
            {"domain": "movement", "pressure": 80},
            {"domain": "infrastructure", "pressure": 60},
            {"domain": "nature", "pressure": 40},
        )
    )

    assert set(scores) == {
        "demand",
        "infrastructure",
        "movement",
        "trust",
        "economic",
        "environmental",
        "cultural_energy",
        "opportunity_strength",
        "recovery_capacity",
    }
    assert scores["movement"] == 80
    assert scores["infrastructure"] == 60
    assert scores["environmental"] == 40
    assert scores["recovery_capacity"] == 40


def test_extended_matrix_roles_are_active_lenses_not_fake_registered_agents() -> None:
    lenses = ecosystem_runtime.extended_matrix_lenses(
        (
            {"domain": "movement", "pressure": 70, "source": "a", "truth_state": "observed"},
            {"domain": "infrastructure", "pressure": 55, "source": "b", "truth_state": "forecast"},
        )
    )

    assert lenses["classification"] == "extended_matrix_system_lenses_not_registered_agents"
    assert lenses["Tank"]["max_pressure"] == 70
    assert lenses["Dozer"]["recovery_capacity"] == 45
    assert lenses["Agent Smith"]["mixed_truth_states"] is True
    assert lenses["Twinz"]["domain_count"] == 2
    assert lenses["can_emit_matrix_signal"] is False
    assert lenses["agent_registry_changed"] is False


def test_outcome_requires_founder_approval(monkeypatch) -> None:
    called = False

    def _write(*args, **kwargs):
        nonlocal called
        called = True
        return {"ok": True, "durable": True}

    monkeypatch.setattr(smi_receipt_backend, "write_receipt", _write)
    result = ecosystem_runtime.record_outcome(
        analysis_id="ECO-1",
        decision="increase approved capacity",
        outcome="capacity held",
        founder_approved=False,
    )

    assert result["ok"] is False
    assert result["status"] == "blocked_founder_approval_required"
    assert called is False


def test_approved_outcome_writes_learning_receipt(monkeypatch) -> None:
    captured = {}

    def _write(kind, payload):
        captured["kind"] = kind
        captured["payload"] = payload
        return {"ok": True, "durable": True, "receipt_id": "r1"}

    monkeypatch.setattr(smi_receipt_backend, "write_receipt", _write)
    result = ecosystem_runtime.record_outcome(
        analysis_id="ECO-2",
        decision="hold route",
        outcome="pressure reduced",
        evidence=("proof:outcome",),
        founder_approved=True,
    )

    assert captured["kind"] == "ecosystem_outcome_receipt"
    assert captured["payload"]["founder_final"] == "approved"
    assert result["ok"] is True
    assert result["durable_learning_proven"] is True
    assert result["recursive_self_improvement_handoff"] is True
    assert result["execution_granted"] is False


def test_runtime_status_keeps_external_live_sources_truth_gated() -> None:
    current = ecosystem_runtime.status()

    assert current["automatic_internal_ingestion_ready"] is True
    assert current["computed_pressure_scoring_ready"] is True
    assert current["extended_matrix_lenses_ready"] is True
    assert current["external_live_complete"] is False
    assert current["extended_matrix_agents_promoted"] is False
    assert current["human_authority_final"] is True
