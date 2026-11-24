"""Read-only GitHub Actions failure intake for governed SMI recovery.

No shell, edits, retries, permissions, approvals, or deployment. The response
contains bounded evidence only; errors fail closed. A worker may call this
as part of the existing scheduled health probe, when deployed.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

REPO = "RoyalPrince777/on-any-postcode"
API = f"https://api.github.com/repos/{REPO}"
MAX_JOBS = 100
MAX_LOG_BYTES = 131072


class _SafeLogRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        host = (target.hostname or "").lower()
        # Follow GitHub Actions log redirects only over HTTPS and never
        # forward the API token to a redirected download host.
        if target.scheme != "https" or not (host == "github.com" or host.endswith((".githubusercontent.com", ".githubassets.com", ".blob.core.windows.net"))):
            raise ValueError("github_log_redirect_not_allowlisted")
        return Request(newurl, headers={"User-Agent": "oap-smi-evidence-reader"})


def _fetch_job_log(job_id: int, token: str) -> str:
    request = Request(f"{API}/actions/jobs/{job_id}/logs", headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "oap-smi-evidence-reader",
    })
    with build_opener(_SafeLogRedirect()).open(request, timeout=10) as response:
        raw = response.read(MAX_LOG_BYTES + 1)
    if len(raw) > MAX_LOG_BYTES:
        raise ValueError("github_job_log_too_large")
    return raw.decode("utf-8", errors="replace")


def _safe_log_summary(raw: str) -> tuple[str, ...]:
    # Do not retain arbitrary log lines, credentials, environment dumps, or URLs.
    # Output only controlled error categories for evidence-based diagnosis.
    patterns = (
        ("signing_configuration", r"Missing OAP_HOME_|signing keystore|certificate mismatch"),
        ("source_verification", r"Verify checked-out|grep:|AssertionError|source candidate"),
        ("gradle_compile", r"Compilation failed|Execution failed for task|error: cannot find symbol"),
        ("dependency_resolution", r"Could not resolve|Could not find.*gradle|Plugin .* was not found"),
        ("android_sdk", r"SDK location not found|Failed to find Build Tools|sdkmanager: command not found"),
        # First-party CI is Python/Chromium as well as Android. These categories
        # remain fixed labels: never return or persist arbitrary log text.
        ("python_lint", r"ruff (?:check|format)|(?m:^\s*[A-Z]{1,3}\d{3,4}\b)|(?m:^Found \d+ errors?\b)"),
        ("python_tests", r"(?m:^\s*FAILED tests/)|(?m:^=+\s*\d+ failed\b)|pytest.*(?:failed|error)"),
        ("python_import", r"ModuleNotFoundError|ImportError:|No module named"),
        ("browser_tests", r"playwright.*(?:fail|error)|chromium.*(?:fail|crash)|(?m:^\s*TimeoutError:.*locator)"),
    )
    return tuple(name for name, pattern in patterns if re.search(pattern, raw, flags=re.IGNORECASE))


def inspect_failed_job_logs(evidence: dict[str, Any], *, token: str,
                            fetch_log: Callable[[int, str], str] = _fetch_job_log) -> dict[str, Any]:
    """Classify bounded failed-job logs; never persist raw logs or infer release."""
    base = {"ready": False, "error": None, "log_categories": (),
            "classified": False, "classification": "unknown",
            "read_only": True, "execution_granted": False,
            "approval_granted": False, "human_authority_final": True,
            "consequential_action": False}
    if not token or not token.strip():
        return {**base, "error": "github_read_token_missing"}
    if not isinstance(evidence, dict) or evidence.get("ready") is not True:
        return {**base, "error": "failed_run_evidence_required"}
    jobs = evidence.get("failed_jobs")
    if not isinstance(jobs, (list, tuple)) or not 0 < len(jobs) <= 10:
        return {**base, "error": "failed_job_count_unacceptable"}
    try:
        summaries = []
        for job in jobs:
            job_id = job.get("job_id") if isinstance(job, dict) else None
            if not isinstance(job_id, int) or isinstance(job_id, bool) or job_id <= 0:
                raise ValueError("invalid_job_id")
            log = fetch_log(job_id, token)
            if not isinstance(log, str) or len(log.encode("utf-8")) > MAX_LOG_BYTES:
                raise ValueError("invalid_log")
            summaries.append({"job_id": job_id, "categories": _safe_log_summary(log)})
        # Downloaded logs are evidence, not an identified root cause.
        # Unknown categories must not be represented as verified diagnosis.
        classified = any(row["categories"] for row in summaries)
        return {**base, "ready": True, "log_categories": tuple(summaries),
                "classified": bool(classified),
                "classification": "classified" if classified else "unknown"}
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError):
        return {**base, "error": "github_job_logs_unavailable"}

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
        raise ValueError("github_evidence_not_object")  # noqa: TRY004 - preserve existing fail-closed API
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
        if not isinstance(run.get("repository"), dict) or run["repository"].get("full_name") != REPO:
            return {**result, "error": "repository_identity_mismatch"}
        jobs_data = fetch(f"{API}/actions/runs/{run_id}/jobs?per_page=100", token)
        if not isinstance(jobs_data, dict):
            raise ValueError("jobs_not_object")  # noqa: TRY004 - preserve existing fail-closed API
        jobs = jobs_data.get("jobs")
        count = jobs_data.get("total_count")
        if (not isinstance(count, int) or isinstance(count, bool)
                or not isinstance(jobs, list) or count != len(jobs)
                or count > MAX_JOBS):
            raise ValueError("jobs_unavailable_or_truncated")
        failed = []
        for job in jobs:
            if not isinstance(job, dict):
                raise ValueError("invalid_job")  # noqa: TRY004 - preserve existing fail-closed API
            if job.get("conclusion") != "failure":
                continue
            jid = job.get("id")
            if not isinstance(jid, int) or isinstance(jid, bool) or jid <= 0:
                raise ValueError("invalid_job_id")
            steps = job.get("steps")
            if not isinstance(steps, list):
                raise ValueError("invalid_job_steps")  # noqa: TRY004 - preserve existing fail-closed API
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


def discover_recent_failed_runs(*, token: str, fetch: Fetch = _fetch_json) -> dict[str, Any]:
    """Find recent completed OAP Core failures without requesting a link from Founder.

    Bounded to the existing workflow, first page, and ten entries. This only
    discovers run IDs; subsequent inspection is separately validated.
    """
    result: dict[str, Any] = {
        "kind": "smi_github_failed_run_discovery", "ready": False,
        "run_ids": (), "error": None, "read_only": True,
        "execution_granted": False, "approval_granted": False,
        "human_authority_final": True, "consequential_action": False,
    }
    if not token or not token.strip():
        return {**result, "error": "github_read_token_missing"}
    try:
        response = fetch(
            f"{API}/actions/workflows/oap-home-apk.yml/runs?per_page=10&status=completed",
            token,
        )
        if not isinstance(response, dict):
            raise ValueError("runs_not_object")  # noqa: TRY004 - preserve existing fail-closed API
        runs = response.get("workflow_runs")
        if not isinstance(runs, list) or len(runs) > 10:
            raise ValueError("run_list_unavailable")
        # The API lists newest first. A historical failure must not be
        # reported as the current blocker after a newer successful run.
        latest_conclusion = runs[0].get("conclusion") if runs and isinstance(runs[0], dict) else None
        ids = []
        for run in runs:
            if not isinstance(run, dict):
                raise ValueError("invalid_run")  # noqa: TRY004 - preserve existing fail-closed API
            if run.get("conclusion") != "failure":
                continue
            if not isinstance(run.get("repository"), dict) or run["repository"].get("full_name") != REPO:
                raise ValueError("repository_identity_mismatch")
            rid = run.get("id")
            if not isinstance(rid, int) or isinstance(rid, bool) or rid <= 0:
                raise ValueError("invalid_run_id")
            ids.append(rid)
        return {**result, "ready": True, "run_ids": tuple(dict.fromkeys(ids)),
                "latest_conclusion": latest_conclusion,
                "current_failure": latest_conclusion == "failure"}
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, AttributeError):
        return {**result, "error": "github_discovery_unavailable"}


# Exact-head source/CI evidence for the currently approved SMI privacy mission.
# New mission scopes must be added deliberately, not inferred from a random PR.
MISSION_PR_CHECKS: dict[int, tuple[str, ...]] = {
    1413: ("OAP governed checks", "SMI Chromium recovery proof",
           "OAP runtime image"),
    1411: ("OAP governed checks", "OAP Data first-party no-Meta source proof",
           "OAP runtime image"),
    # Founder-approved OAP World priorities: Link Up and Original Three.
    1234: ("OAP governed checks", "OAP runtime image",
           "OAP Data first-party no-Meta source proof"),
    1318: ("OAP governed checks", "SMI Chromium recovery proof",
           "OAP runtime image"),
    # Founder-approved SMI execution foundations and TDA priority.
    1083: ("OAP governed checks", "OAP runtime image"),
    1417: ("OAP governed checks", "SMI Chromium recovery proof",
           "OAP War Room real Chromium acceptance", "OAP runtime image"),
    1245: ("OAP governed checks",),
    1256: ("OAP governed checks",),
    1257: ("OAP governed checks", "OAP runtime image",
           "OAP real routing container proof"),
    1400: ("OAP governed checks", "OAP runtime image"),
    # Specialist passports remain advisory; one SMI worker owns observation.
    1384: ("OAP governed checks", "SMI agent achievement proof",
           "OAP runtime image"),
}


def inspect_mission_continuity(
    pr_number: int, *, token: str, fetch: Fetch = _fetch_json,
) -> dict[str, Any]:
    """Automatically select the next bounded step from real exact-head CI.

    This is a read-only Mission Keeper signal, not a release or GitHub write.
    The organism worker stores the resulting evidence in its existing receipts.
    """
    result: dict[str, Any] = {
        "kind": "smi_mission_continuity",
        "pr_number": pr_number,
        "ready": False,
        "ci_proven": False,
        "head_sha": None,
        "next_move": "hold_unknown",
        "failed_run_id": None,
        "reason": "evidence_unavailable",
        "read_only": True,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
        "consequential_action": False,
    }
    if not isinstance(pr_number, int) or isinstance(pr_number, bool) or pr_number not in MISSION_PR_CHECKS:
        return {**result, "reason": "mission_pr_not_allowlisted"}
    if not isinstance(token, str) or not token.strip():
        return {**result, "reason": "github_read_token_missing"}
    try:
        pr = fetch(f"{API}/pulls/{pr_number}", token)
        if not isinstance(pr, dict) or pr.get("number") != pr_number:
            raise ValueError("pr_identity_mismatch")
        head, base = pr.get("head"), pr.get("base")
        if not isinstance(head, dict) or not isinstance(base, dict):
            raise TypeError("pr_head_missing")
        head_repo = head.get("repo")
        if (not isinstance(head_repo, dict) or head_repo.get("full_name") != REPO
                or base.get("ref") != "main"):
            raise ValueError("pr_repository_mismatch")
        sha = head.get("sha")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("invalid_head_sha")
        if pr.get("state") != "open":
            return {**result, "ready": True, "head_sha": sha,
                    "next_move": "hold_closed_pr", "reason": "pr_not_open"}
        if pr.get("draft") is not True and pr.get("draft") is not False:
            raise ValueError("draft_state_unknown")
        response = fetch(
            f"{API}/actions/runs?head_sha={sha}&event=pull_request&per_page=100",
            token,
        )
        if not isinstance(response, dict):
            raise TypeError("runs_not_object")
        runs = response.get("workflow_runs")
        count = response.get("total_count")
        if (not isinstance(count, int) or isinstance(count, bool)
                or not isinstance(runs, list) or count != len(runs)
                or count > 100):
            raise ValueError("runs_unavailable_or_truncated")
        latest: dict[str, dict[str, Any]] = {}
        required = MISSION_PR_CHECKS[pr_number]
        for run in runs:
            if not isinstance(run, dict):
                raise TypeError("invalid_run")
            repository = run.get("repository")
            if (not isinstance(repository, dict)
                    or repository.get("full_name") != REPO
                    or run.get("head_sha") != sha
                    or run.get("event") != "pull_request"):
                raise ValueError("run_scope_mismatch")
            name = run.get("name")
            rid = run.get("id")
            if name not in required:
                continue
            if not isinstance(rid, int) or isinstance(rid, bool) or rid <= 0:
                raise ValueError("run_id_invalid")
            if name not in latest or rid > latest[name]["id"]:
                latest[name] = run
        missing = tuple(name for name in required if name not in latest)
        statuses = {name: ("missing" if name in missing else
                           str(latest[name].get("conclusion") or "pending")
                           if latest[name].get("status") == "completed" else
                           "pending") for name in required}
        failed = tuple(name for name in required if statuses[name] == "failure")
        if failed:
            first = failed[0]
            return {**result, "ready": True, "head_sha": sha,
                    "next_move": "inspect_failed_ci",
                    "failed_run_id": latest[first]["id"],
                    "reason": "confirmed_ci_failure",
                    "required_checks": statuses}
        if all(statuses[name] == "success" for name in required):
            return {**result, "ready": True, "ci_proven": True,
                    "head_sha": sha, "next_move": "continue_target_proof",
                    "reason": "exact_head_ci_passed_not_production",
                    "required_checks": statuses}
        return {**result, "ready": True, "head_sha": sha,
                "next_move": "await_exact_head_evidence",
                "reason": "ci_pending_or_unproven",
                "required_checks": statuses}
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError,
            AttributeError, json.JSONDecodeError):
        return result
