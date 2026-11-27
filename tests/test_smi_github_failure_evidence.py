from mission_control.smi_github_failure_evidence import API, REPO, inspect_failed_run


def _fake(url, token):
    assert token == "read-only"
    if url == f"{API}/actions/runs/157":
        return {"id": 157, "status": "completed", "conclusion": "failure",
                "repository": {"full_name": REPO}}
    if url == f"{API}/actions/runs/157/jobs?per_page=100":
        return {"total_count": 2, "jobs": [
            {"id": 4, "name": "compile", "conclusion": "failure",
             "steps": [{"name": "Check source", "number": 2, "conclusion": "failure"}]},
            {"id": 5, "name": "build", "conclusion": "success", "steps": []},
        ]}
    raise AssertionError(url)


def test_failed_run_returns_bounded_evidence_without_authority():
    result = inspect_failed_run(157, token="read-only", fetch=_fake)
    assert result["ready"] is True
    assert result["failed_jobs"] == ({
        "job_id": 4, "name": "compile",
        "failed_steps": ({"name": "Check source", "number": 2},),
    },)
    assert result["execution_granted"] is False
    assert result["approval_granted"] is False
    assert result["consequential_action"] is False


def test_missing_token_and_invalid_run_fail_closed():
    assert inspect_failed_run(157, token="")["error"] == "github_read_token_missing"
    assert inspect_failed_run("../157", token="read-only")["error"] == "invalid_run_id"
    assert inspect_failed_run(True, token="read-only")["error"] == "invalid_run_id"


def test_wrong_run_and_truncated_jobs_fail_closed():
    assert inspect_failed_run(157, token="read-only", fetch=lambda u, t: {"id": 158})["ready"] is False

    def truncated(url, token):
        if url.endswith("/jobs?per_page=100"):
            return {"total_count": 101, "jobs": []}
        return {"id": 157, "status": "completed", "conclusion": "failure",
                "repository": {"full_name": REPO}}

    result = inspect_failed_run(157, token="read-only", fetch=truncated)
    assert result["error"] == "github_evidence_unavailable"
    assert result["ready"] is False


def test_nonfailed_run_must_not_be_claimed_as_repaired():
    def green(url, token):
        return {"id": 157, "status": "completed", "conclusion": "success",
                "repository": {"full_name": REPO}}
    result = inspect_failed_run(157, token="read-only", fetch=green)
    assert result["ready"] is False
    assert result["error"] == "run_not_completed_failure"


def test_discovery_finds_failed_runs_without_user_link():
    from mission_control.smi_github_failure_evidence import discover_recent_failed_runs

    def fetch(url, token):
        assert "/actions/workflows/oap-home-apk.yml/runs?" in url
        assert token == "read-only"
        return {"workflow_runs": [
            {"id": 157, "conclusion": "failure", "repository": {"full_name": REPO}},
            {"id": 156, "conclusion": "failure", "repository": {"full_name": REPO}},
            {"id": 155, "conclusion": "success", "repository": {"full_name": REPO}},
        ]}
    result = discover_recent_failed_runs(token="read-only", fetch=fetch)
    assert result["ready"] is True
    assert result["run_ids"] == (157, 156)
    assert result["execution_granted"] is False


def test_discovery_rejects_wrong_repository():
    from mission_control.smi_github_failure_evidence import discover_recent_failed_runs
    result = discover_recent_failed_runs(token="read-only", fetch=lambda u, t: {
        "workflow_runs": [{"id": 157, "conclusion": "failure",
                           "repository": {"full_name": "attacker/other"}}],
    })
    assert result["ready"] is False
    assert result["error"] == "github_discovery_unavailable"


def test_newer_success_does_not_reactivate_old_failure():
    from mission_control.smi_github_failure_evidence import discover_recent_failed_runs

    def fetch(url, token):
        return {"workflow_runs": [
            {"id": 160, "conclusion": "success", "repository": {"full_name": REPO}},
            {"id": 157, "conclusion": "failure", "repository": {"full_name": REPO}},
        ]}

    evidence = discover_recent_failed_runs(token="read-only", fetch=fetch)
    assert evidence["ready"] is True
    assert evidence["run_ids"] == (157,)
    assert evidence["latest_conclusion"] == "success"
    assert evidence["current_failure"] is False


def test_latest_failed_run_is_actionable_without_repair_authority():
    from mission_control.smi_github_failure_evidence import discover_recent_failed_runs

    evidence = discover_recent_failed_runs(token="read-only", fetch=lambda url, token: {
        "workflow_runs": [{"id": 157, "conclusion": "failure",
                           "repository": {"full_name": REPO}}],
    })
    assert evidence["current_failure"] is True
    assert evidence["execution_granted"] is False


def test_malformed_or_partial_job_pages_fail_closed():
    def fake_response(jobs_result):
        def fetch(url, token):
            if url.endswith("/jobs?per_page=100"):
                return jobs_result
            return {"id": 157, "status": "completed", "conclusion": "failure",
                    "repository": {"full_name": REPO}}
        return fetch

    for payload in (
        None, {"total_count": 2, "jobs": []},
        {"total_count": "1", "jobs": [{}]},
        {"total_count": True, "jobs": [{}]},
        {"total_count": 1, "jobs": "not-a-list"},
    ):
        result = inspect_failed_run(157, token="read-only", fetch=fake_response(payload))
        assert result["ready"] is False
        assert result["error"] == "github_evidence_unavailable"


def test_invalid_discovery_response_fails_closed():
    from mission_control.smi_github_failure_evidence import discover_recent_failed_runs
    result = discover_recent_failed_runs(token="read-only", fetch=lambda u, t: None)
    assert result["ready"] is False
    assert result["error"] == "github_discovery_unavailable"


def test_log_classification_is_bounded_and_never_returns_secrets():
    from mission_control.smi_github_failure_evidence import inspect_failed_job_logs
    evidence = {"ready": True, "failed_jobs": ({"job_id": 123},)}
    secret = "SECRET_TOKEN_SHOULD_NOT_LEAK"
    result = inspect_failed_job_logs(
        evidence, token="read-only",
        fetch_log=lambda job_id, token: (
            f"Missing OAP_HOME_KEYSTORE_B64: {secret}\\n"
            "Execution failed for task ':compileDebugJavaWithJavac'"
        ),
    )
    assert result["ready"] is True
    assert "signing_configuration" in result["log_categories"][0]["categories"]
    assert secret not in str(result)
    assert result["execution_granted"] is False


def test_logs_fail_closed_without_prior_job_proof():
    from mission_control.smi_github_failure_evidence import inspect_failed_job_logs
    assert inspect_failed_job_logs({}, token="read-only")["ready"] is False
    assert inspect_failed_job_logs({"ready": True, "failed_jobs": ()}, token="read-only")["ready"] is False
