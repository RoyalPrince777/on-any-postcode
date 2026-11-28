"""Boundary checks for SMI GitHub intake integration in the existing worker."""

from pathlib import Path

WORKER = Path("mission_control/organism_worker.py").read_text()


def test_github_intake_reuses_existing_health_probe_no_new_scheduler():
    assert 'smi_github_failure_evidence.discover_recent_failed_runs(' in WORKER
    assert 'smi_github_failure_evidence.inspect_failed_run(' in WORKER
    assert '"RUNTIME_HEALTH_PROBE": _health_probe' in WORKER
    assert '"GITHUB_REPAIR"' not in WORKER


def test_github_intake_requires_dedicated_read_token_and_stays_read_only():
    assert 'os.environ.get("OAP_SMI_GITHUB_READ_TOKEN", "")' in WORKER
    assert 'if github_token:' in WORKER
    assert '"error": "not_configured"' in WORKER
    assert '"github_failure_evidence": github_evidence' in WORKER
    assert '"independent_execution": False' in WORKER
    assert '"human_authority_final": True' in WORKER


def test_worker_continues_smi_mission_without_button_or_new_job(monkeypatch):
    from mission_control import organism_worker

    monkeypatch.setenv("OAP_SMI_GITHUB_READ_TOKEN", "private-token-not-persisted")
    monkeypatch.setattr(
        organism_worker.postgres_db, "postgres_status",
        lambda: {"initialized": False},
    )
    for module in (organism_worker.oap_core_autonomy,
                   organism_worker.smi_runtime_autonomy,
                   organism_worker.organism_autonomy):
        monkeypatch.setattr(
            module, "run_cycle",
            lambda: {"consequential_action": False, "independent_execution": False},
        )
    monkeypatch.setattr(
        organism_worker.smi_github_failure_evidence,
        "discover_recent_failed_runs",
        lambda *, token: {"ready": True, "run_ids": (),
                          "current_failure": False, "read_only": True},
    )
    observed = []

    def inspect(pr_number, *, token):
        assert token == "private-token-not-persisted"
        observed.append(pr_number)
        return {
            "pr_number": pr_number,
            "ready": True,
            "ci_proven": pr_number == 1413,
            "next_move": "continue_target_proof"
            if pr_number == 1413 else "await_exact_head_evidence",
            "consequential_action": False,
            "execution_granted": False,
        }

    monkeypatch.setattr(
        organism_worker.smi_github_failure_evidence,
        "inspect_mission_continuity", inspect,
    )
    result = organism_worker._health_probe(None)
    assert observed == [1413, 1411, 1234, 1318, 1083, 1417, 1245, 1256, 1257, 1400, 1384]
    reviews = result["github_failure_evidence"]["mission_continuity"]
    assert all(row["behaviour_review"]["checks_executed"] is False for row in reviews)
    assert all(row["behaviour_review"]["repair_authorized"] is False for row in reviews)
    assert reviews[0]["behaviour_review"]["truth"] == "CI_VERIFIED"
    assert reviews[0]["specialist_alliance"]["roles"] == ("Trinity", "Octopus", "Tank", "Dozer", "Owl")
    assert reviews[1]["specialist_alliance"]["roles"] == ("Owl", "Oracle")
    assert all(row["specialist_alliance"]["agents_executed"] is False for row in reviews)
    assert reviews[0]["behaviour_review"]["thinking_depth"] == 3
    assert reviews[1]["behaviour_review"]["truth"] == "UNKNOWN"
    assert result["github_failure_evidence"]["captain_next_move"] == "continue_target_proof"
    assert result["github_failure_evidence"]["captain_automatic_observation"] is True
    assert result["github_failure_evidence"]["captain_code_execution"] is False
    assert "private-token-not-persisted" not in str(result)
    assert result["consequential_action"] is False
    assert result["independent_execution"] is False
    assert result["human_authority_final"] is True


def test_failure_diagnosis_requires_classification_and_never_authorizes_repair(monkeypatch):
    from mission_control import organism_worker

    monkeypatch.setenv("OAP_SMI_GITHUB_READ_TOKEN", "test-only-private-token")
    monkeypatch.setattr(
        organism_worker.postgres_db, "postgres_status",
        lambda: {"initialized": False},
    )
    for module in (organism_worker.oap_core_autonomy,
                   organism_worker.smi_runtime_autonomy,
                   organism_worker.organism_autonomy):
        monkeypatch.setattr(
            module, "run_cycle",
            lambda: {"consequential_action": False, "independent_execution": False},
        )
    monkeypatch.setattr(
        organism_worker.smi_github_failure_evidence,
        "discover_recent_failed_runs",
        lambda *, token: {"ready": True, "current_failure": False, "run_ids": ()},
    )
    monkeypatch.setattr(
        organism_worker.smi_github_failure_evidence,
        "inspect_mission_continuity",
        lambda pr_number, *, token: {
            "ready": True, "pr_number": pr_number,
            "next_move": "inspect_failed_ci" if pr_number == 1413 else "await_exact_head_evidence",
            "failed_run_id": 71 if pr_number == 1413 else None,
            "head_sha": "a" * 40,
            "ci_proven": False, "consequential_action": False,
        },
    )
    monkeypatch.setattr(
        organism_worker.smi_github_failure_evidence,
        "inspect_failed_run",
        lambda run_id, *, token, expected_head: {"ready": expected_head == "a" * 40,
                                   "failed_jobs": ({"job_id": 72},)},
    )
    monkeypatch.setattr(
        organism_worker.smi_github_failure_evidence,
        "inspect_failed_job_logs",
        lambda evidence, *, token: {
            "ready": True, "classified": False, "classification": "unknown",
            "log_categories": ({"job_id": 72, "categories": ()},),
        },
    )

    unknown = organism_worker._health_probe(None)
    diagnosis = unknown["github_failure_evidence"]["mission_continuity"][0][
        "automatic_failure_diagnosis"
    ]
    assert unknown["github_failure_evidence"]["captain_next_move"] == "inspect_failed_ci"
    assert diagnosis["log_evidence_retrieved"] is True
    assert diagnosis["category_detected"] is False
    assert diagnosis["verified"] is False
    assert diagnosis["repair_authorized"] is False
    assert unknown["github_failure_evidence"]["mission_continuity"][0][
        "behaviour_review"
    ]["thinking_depth"] == 7
    assert unknown["github_failure_evidence"]["mission_continuity"][0][
        "behaviour_review"
    ]["truth"] == "BLOCKED"
    assert unknown["consequential_action"] is False
    assert "test-only-private-token" not in str(unknown)

    monkeypatch.setattr(
        organism_worker.smi_github_failure_evidence,
        "inspect_failed_job_logs",
        lambda evidence, *, token: {
            "ready": True, "classified": True, "classification": "classified",
            "log_categories": ({"job_id": 72, "categories": ("python_lint",)},),
        },
    )
    classified = organism_worker._health_probe(None)
    diagnosis = classified["github_failure_evidence"]["mission_continuity"][0][
        "automatic_failure_diagnosis"
    ]
    assert diagnosis["category_detected"] is True
    assert diagnosis["verified"] is False  # category is not confirmed root cause
    assert diagnosis["repair_authorized"] is False
    assert "NIRMATA" in diagnosis["next_safe_action"]
