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


def test_runtime_bridge_reads_existing_status_without_granting_green(monkeypatch):
    from mission_control import organism_runtime
    from mission_control.kernel_anatomy_readiness import runtime_anatomy_snapshot

    monkeypatch.setattr(
        organism_runtime,
        "runtime_status",
        lambda: {"ready": True, "schema_ready": True, "worker_fresh": True, "error": None},
    )
    result = runtime_anatomy_snapshot()
    heart = next(x for x in result["organs"] if x["id"] == "living_kernel")
    assert result["runtime"]["ready"] is True
    assert heart["status"] == "UNVERIFIED"
    assert result["ready"] is False
    assert result["consequential_execution"] is False


def test_runtime_bridge_fails_closed_on_missing_worker(monkeypatch):
    from mission_control import organism_runtime
    from mission_control.kernel_anatomy_readiness import runtime_anatomy_snapshot

    monkeypatch.setattr(
        organism_runtime,
        "runtime_status",
        lambda: {"ready": False, "schema_ready": True, "worker_fresh": False, "error": None},
    )
    result = runtime_anatomy_snapshot()
    assert result["runtime"]["worker_fresh"] is False
    assert result["runtime"]["ready"] is False
    assert result["ready"] is False


def test_master_vitals_never_invent_unmeasured_health(monkeypatch):
    from mission_control import organism_runtime
    from mission_control.kernel_anatomy_readiness import MASTER_VITALS, master_vitals_snapshot

    monkeypatch.setattr(
        organism_runtime,
        "runtime_status",
        lambda: {"ready": True, "schema_ready": True, "worker_fresh": True, "error": None},
    )
    result = master_vitals_snapshot()
    assert tuple(item["name"] for item in result["vitals"]) == MASTER_VITALS
    assert result["vitals"][0]["status"] == "UNVERIFIED"
    assert all(item["status"] == "UNKNOWN" for item in result["vitals"][1:])
    assert result["ready"] is False


def test_master_vitals_degrade_when_runtime_is_unready(monkeypatch):
    from mission_control import organism_runtime
    from mission_control.kernel_anatomy_readiness import master_vitals_snapshot

    monkeypatch.setattr(
        organism_runtime,
        "runtime_status",
        lambda: {"ready": False, "schema_ready": False, "worker_fresh": False, "error": "runtime_schema_pending"},
    )
    result = master_vitals_snapshot()
    assert result["vitals"][0]["status"] == "DEGRADED"
    assert result["ready"] is False


def test_runtime_probe_exception_degrades_instead_of_raising(monkeypatch):
    from mission_control import organism_runtime
    from mission_control.kernel_anatomy_readiness import master_vitals_snapshot

    def broken_probe():
        raise RuntimeError("database offline")

    monkeypatch.setattr(organism_runtime, "runtime_status", broken_probe)
    result = master_vitals_snapshot()
    assert result["anatomy"]["runtime"]["error"] == "runtime_probe_unavailable"
    assert result["vitals"][0]["status"] == "DEGRADED"
    assert result["ready"] is False
    assert result["consequential_execution"] is False


def test_invalid_runtime_probe_response_fails_closed(monkeypatch):
    from mission_control import organism_runtime
    from mission_control.kernel_anatomy_readiness import runtime_anatomy_snapshot

    monkeypatch.setattr(organism_runtime, "runtime_status", lambda: None)
    result = runtime_anatomy_snapshot()
    assert result["runtime"]["error"] == "runtime_probe_unavailable"
    assert result["ready"] is False


def test_continuity_flags_dead_letters_without_claiming_recovery(monkeypatch):
    from mission_control import organism_runtime
    from mission_control.kernel_anatomy_readiness import continuity_evidence_snapshot

    monkeypatch.setattr(
        organism_runtime, "runtime_status",
        lambda: {"ready": True, "schema_ready": True, "worker_fresh": True,
                 "retry": 0, "dead_letter": 2, "error": None},
    )
    result = continuity_evidence_snapshot()
    assert result["status"] == "DEGRADED"
    assert result["dead_letter_jobs"] == 2
    assert result["recovery_proven"] is False


def test_continuity_rejects_missing_or_boolean_counts(monkeypatch):
    from mission_control import organism_runtime
    from mission_control.kernel_anatomy_readiness import continuity_evidence_snapshot

    monkeypatch.setattr(
        organism_runtime, "runtime_status",
        lambda: {"ready": True, "schema_ready": True, "worker_fresh": True,
                 "retry": True, "dead_letter": None},
    )
    result = continuity_evidence_snapshot()
    assert result["status"] == "UNKNOWN"
    assert result["retry_jobs"] is None
    assert result["recovery_proven"] is False
