"""Read-only GitHub Actions failure intake for governed SMI recovery.

No shell, edits, retries, permissions, approvals, or deployment. The response
contains bounded evidence only; errors fail closed. A worker may call this
after receiving an authorised numeric run ID, but it is not yet scheduled.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO = "RoyalPrince777/on-any-postcode"
API = f"https://api.github.com/repos/{REPO}"
MAX_JOBS = 100
Fetch = Callable[[str, str], dict[str, Any]]


def _fetch_json(url: str, token: str) -> dict[str, Any]:
    if not url.startswith(API + "/"):
        raise ValueError("github_url_not_allowlisted")
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "oap-smi-evidence-reader",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(request, timeout=10) as response:  # nosec: fixed HTTPS API origin
        payload = response.read(262145)
    if len(payload) > 262144:
        raise ValueError("github_evidence_too_large")
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("github_evidence_not_object")
    return data


def inspect_failed_run(run_id: object, *, token: str, fetch: Fetch = _fetch_json) -> dict[str, Any]:
    """Retrieve real failed-job metadata; never infer a fix or release outcome."""
    result: dict[str, Any] = {
        "kind": "smi_github_failure_evidence",
        "ready": False,
        "run_id": None,
        "failed_jobs": (),
        "error": None,
        "read_only": True,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
        "consequential_action": False,
    }
    if isinstance(run_id, bool) or not re.fullmatch(r"[1-9][0-9]{0,18}", str(run_id)):
        return {**result, "error": "invalid_run_id"}
    if not token or not token.strip():
        return {**result, "error": "github_read_token_missing"}
    result["run_id"] = int(run_id)
    try:
        run = fetch(f"{API}/actions/runs/{run_id}", token)
        if not isinstance(run, dict) or run.get("id") != int(run_id):
            raise ValueError("run_identity_mismatch")
        if run.get("status") != "completed" or run.get("conclusion") != "failure":
            return {**result, "error": "run_not_completed_failure"}
        if run.get("repository", {}).get("full_name") != REPO:
            return {**result, "error": "repository_identity_mismatch"}
        jobs_data = fetch(f"{API}/actions/runs/{run_id}/jobs?per_page=100", token)
        jobs = jobs_data.get("jobs")
        if not isinstance(jobs, list) or len(jobs) > MAX_JOBS or int(jobs_data.get("total_count", -1)) > MAX_JOBS:
            raise ValueError("jobs_unavailable_or_truncated")
        failed = []
        for job in jobs:
            if not isinstance(job, dict):
                raise ValueError("invalid_job")
            if job.get("conclusion") != "failure":
                continue
            jid = job.get("id")
            if not isinstance(jid, int) or isinstance(jid, bool) or jid <= 0:
                raise ValueError("invalid_job_id")
            steps = job.get("steps")
            if not isinstance(steps, list):
                raise ValueError("invalid_job_steps")
            failed_steps = tuple(
                {"name": str(s.get("name", ""))[:160], "number": s.get("number")}
                for s in steps if isinstance(s, dict) and s.get("conclusion") == "failure"
            )
            failed.append({"job_id": jid, "name": str(job.get("name", ""))[:160], "failed_steps": failed_steps})
        if not failed:
            return {**result, "error": "failed_job_not_found"}
        return {**result, "ready": True, "failed_jobs": tuple(failed), "error": None}
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, json.JSONDecodeError):
        return {**result, "error": "github_evidence_unavailable"}
