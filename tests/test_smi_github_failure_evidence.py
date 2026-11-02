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
