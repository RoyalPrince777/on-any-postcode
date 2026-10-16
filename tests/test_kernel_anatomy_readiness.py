from mission_control.kernel_anatomy_readiness import anatomy_readiness
from mission_control.organism import ORGANISM_SYSTEMS


def test_missing_observations_never_imply_healthy_organs():
    result = anatomy_readiness()
    assert result["ready"] is False
    assert result["consequential_execution"] is False
    assert result["architecture_valid"] is True
    assert len(result["organs"]) == len(ORGANISM_SYSTEMS)
    assert all(organ["status"] == "UNKNOWN" for organ in result["organs"])


def test_reported_health_is_not_confused_with_verified_readiness():
    result = anatomy_readiness({
        "living_kernel": {
            "healthy": True,
            "source": "supervisor",
            "timestamp": "2026-10-16T12:00:00Z",
        },
        "unregistered": {"healthy": True},
    })
    heart = next(x for x in result["organs"] if x["id"] == "living_kernel")
    assert heart["status"] == "UNVERIFIED"
    assert heart["evidence_present"] is True
    assert result["ready"] is False
    assert result["unknown_observations"] == ["unregistered"]


def test_malformed_evidence_fails_closed():
    for observation in (
        {"healthy": "true", "source": "probe", "timestamp": "now"},
        {"healthy": True, "source": "", "timestamp": "now"},
        {"healthy": True, "source": "probe"},
    ):
        result = anatomy_readiness({"living_kernel": observation})
        heart = next(x for x in result["organs"] if x["id"] == "living_kernel")
        assert heart["status"] == "UNKNOWN"
        assert result["ready"] is False
