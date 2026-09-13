from mission_control import ecosystem_intelligence


def _signal(
    domain: str,
    summary: str,
    *,
    pressure: int,
    truth_state: str = "observed",
) -> dict[str, object]:
    return {
        "domain": domain,
        "summary": summary,
        "pressure": pressure,
        "confidence": 85,
        "truth_state": truth_state,
        "horizon": "now",
        "place": "South London",
        "source": "bounded_test",
        "evidence": (f"proof:{domain}",),
    }


def test_status_reuses_existing_ecosystem_workspace() -> None:
    result = ecosystem_intelligence.status()

    assert result["workspace"]["id"] == "ecosystem"
    assert result["human_authority"] == "final"
    assert result["execution_granted"] is False
    assert result["self_approval_allowed"] is False
    assert result["full_green"] is False


def test_cross_domain_pressure_routes_to_smi_without_execution() -> None:
    result = ecosystem_intelligence.analyse(
        (
            _signal("nature", "Heavy rain increasing local pressure", pressure=72),
            _signal("movement", "Journey times are degrading", pressure=81),
            _signal("economy", "Delivery fulfilment pressure rising", pressure=68),
        ),
        scope="South London",
        pressure_scores={"movement": 81, "environmental": 72},
    )

    assert result["cross_domain"] is True
    assert result["state"] == "high"
    assert result["war_room_required"] is True
    assert result["human_authority_required"] is True
    assert result["recursive_self_improvement_candidate"] is True
    assert result["matrix_signal"]["sender"] == "Trinity"
    assert result["matrix_signal"]["execution_granted"] is False
    assert result["execution_granted"] is False
    assert result["external_action_taken"] is False


def test_truth_states_remain_distinct() -> None:
    result = ecosystem_intelligence.analyse(
        (
            _signal("place", "Local observation", pressure=25, truth_state="observed"),
            _signal("risk", "Possible downstream issue", pressure=40, truth_state="forecast"),
        )
    )

    assert result["truth_mix"]["observed"] == 1
    assert result["truth_mix"]["forecast"] == 1
    assert result["truth_mix"]["confirmed"] == 0


def test_invalid_domain_fails_closed() -> None:
    signal = _signal("unknown", "Unsupported domain", pressure=50)

    try:
        ecosystem_intelligence.analyse((signal,))
    except ValueError as exc:
        assert "Unsupported ecosystem domain" in str(exc)
    else:
        raise AssertionError("unsupported domain should fail closed")


def test_pressure_score_range_fails_closed() -> None:
    signal = _signal("infrastructure", "Capacity pressure", pressure=40)

    try:
        ecosystem_intelligence.analyse(
            (signal,),
            pressure_scores={"recovery_capacity": 101},
        )
    except ValueError as exc:
        assert "between 0 and 100" in str(exc)
    else:
        raise AssertionError("out-of-range pressure should fail closed")
