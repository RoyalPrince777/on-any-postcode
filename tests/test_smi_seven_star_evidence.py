"""Seven-star evidence presentation must fail closed and preserve Founder Final."""
from mission_control.smi_deep_dive_protocol import (
    SEVEN_STAR_GATE,
    evaluate_seven_star_gate,
)


def test_missing_evidence_is_unknown_not_green():
    result = evaluate_seven_star_gate()
    assert result["proven"] == 0
    assert result["technical_check_percent"] == 0
    assert len(result["checks"]) == 7
    assert all(check["signal"] == "unknown" for check in result["checks"])
    assert result["production_green"] is False
    assert result["founder_final"] is False


def test_proven_requires_explicit_verified_fresh_source():
    result = evaluate_seven_star_gate({
        "Truth": {"passed": True, "verified": True, "fresh": True, "source": "CI exact-head/123"},
        "Function": {"passed": True, "source": "   "},
        "Security": {"passed": False, "verified": True, "fresh": True, "source": "security-check/123"},
        "Stability": {"passed": "true", "source": "stability-check/123"},
        "Integration": {"passed": True},
    })
    assert result["proven"] == 1
    assert result["technical_check_percent"] == 14
    assert [item["signal"] for item in result["checks"]] == [
        "green", "purple", "red", "purple", "purple", "unknown", "unknown"
    ]


def test_all_seven_technical_checks_do_not_self_approve_release():
    result = evaluate_seven_star_gate({
        name: {"passed": True, "verified": True, "fresh": True, "source": "verified-run/" + name}
        for name in SEVEN_STAR_GATE
    })
    assert result["proven"] == 7
    assert result["technical_check_percent"] == 100
    assert result["technical_gate_passed"] is True
    assert result["production_green"] is False
    assert result["founder_final"] is False
    assert result["physical_acceptance_included"] is False


def test_private_deep_dive_status_exposes_fail_closed_assessment():
    from mission_control.smi_deep_dive_protocol import status

    state = status()
    assessment = state["seven_star_assessment"]
    assert assessment["total"] == 7
    assert assessment["proven"] == 0
    assert [check["name"] for check in assessment["checks"]] == list(SEVEN_STAR_GATE)
    assert assessment["technical_gate_passed"] is False
    assert assessment["production_green"] is False
    assert assessment["founder_final"] is False

def test_unverified_or_stale_pass_claims_never_turn_green():
    result = evaluate_seven_star_gate({
        "Truth": {"passed": True, "source": "unverified-source"},
        "Function": {"passed": True, "verified": True, "fresh": False, "source": "old-run"},
        "Security": {"passed": True, "verified": True, "source": "unconfirmed-freshness"},
        "Stability": {"passed": True, "verified": True, "fresh": True, "source": "  "},
    })
    assert result["proven"] == 0
    assert result["technical_check_percent"] == 0
    assert all(item["signal"] == "purple" for item in result["checks"][:4])
    assert result["technical_gate_passed"] is False


def test_stale_failure_is_pending_not_current_red():
    result = evaluate_seven_star_gate({
        "Truth": {
            "passed": False,
            "verified": True,
            "fresh": False,
            "source": "old-failure",
        },
        "Security": {
            "passed": False,
            "verified": True,
            "fresh": True,
            "source": "current-failure",
        },
    })
    assert result["checks"][0]["signal"] == "purple"
    assert result["checks"][2]["signal"] == "red"
    assert result["proven"] == 0
    assert result["production_green"] is False
