"""Prepare exact GitHub ActionPlans for Human Authority review.

These helpers never call GitHub. They only validate and bind an exact mutation
payload into the existing ActionPlan digest/approval model.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from oap.contracts import ActionPlan, action_plan_digest
from oap.registry import founder_tool_registry

_BRANCH = re.compile(r"^oap-mind/[A-Za-z0-9._/-]{1,80}$")
_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


def _request_id(value: object | None) -> str:
    candidate = str(value or "").strip()
    return candidate or "github-" + uuid.uuid4().hex


def _branch(value: object) -> str:
    branch = str(value or "").strip()
    if not _BRANCH.fullmatch(branch) or ".." in branch.split("/"):
        raise ValueError("Founder branches must use the oap-mind/ prefix")
    return branch


def _proposal(plan: ActionPlan) -> dict[str, Any]:
    return {
        "request_id": plan.request_id,
        "action_type": plan.action_type,
        "payload": plan.payload,
        "requires_human_approval": True,
        "action_digest": action_plan_digest(plan),
        "execution_ready": False,
        "next_gate": "Human Authority approval",
        "independent_execute": False,
    }


def propose_branch_create(*, branch: str, base_sha: str, request_id: str | None = None) -> dict[str, Any]:
    founder_tool_registry().authorize_capability("github", "branch.create", mutation=True)
    clean_branch = _branch(branch)
    clean_sha = str(base_sha or "").strip()
    if not _SHA.fullmatch(clean_sha):
        raise ValueError("A full 40-character base commit SHA is required")
    return _proposal(
        ActionPlan(
            request_id=_request_id(request_id),
            action_type="github.branch.create",
            payload={"branch": clean_branch, "base_sha": clean_sha},
            requires_human_approval=True,
        )
    )


def propose_file_write(
    *,
    branch: str,
    path: str,
    content: str,
    message: str,
    sha: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    founder_tool_registry().authorize_capability("github", "file.write", mutation=True)
    clean_branch = _branch(branch)
    clean_path = str(path or "").strip().lstrip("/")
    clean_message = str(message or "").strip()
    if not clean_path or ".." in clean_path.split("/"):
        raise ValueError("Repository path is invalid")
    if not clean_message or len(clean_message) > 160:
        raise ValueError("Commit message is required and must be at most 160 characters")
    if not isinstance(content, str) or len(content.encode("utf-8")) > 500_000:
        raise ValueError("UTF-8 file content must be at most 500 KB")
    clean_sha = str(sha or "").strip()
    if clean_sha and not _SHA.fullmatch(clean_sha):
        raise ValueError("Existing file SHA must be 40 hexadecimal characters")
    payload: dict[str, Any] = {
        "branch": clean_branch,
        "path": clean_path,
        "content": content,
        "message": clean_message,
    }
    if clean_sha:
        payload["sha"] = clean_sha
    return _proposal(
        ActionPlan(
            request_id=_request_id(request_id),
            action_type="github.file.write",
            payload=payload,
            requires_human_approval=True,
        )
    )


def propose_pull_request(
    *,
    head: str,
    title: str,
    body: str = "",
    base: str = "main",
    request_id: str | None = None,
) -> dict[str, Any]:
    founder_tool_registry().authorize_capability("github", "pr.create", mutation=True)
    clean_head = _branch(head)
    clean_base = str(base or "main").strip()
    clean_title = str(title or "").strip()
    clean_body = str(body or "").strip()
    if clean_base != "main":
        raise PermissionError("Founder coding pull requests must target main")
    if not clean_title or len(clean_title) > 160:
        raise ValueError("Pull request title is required and must be at most 160 characters")
    if len(clean_body) > 20_000:
        raise ValueError("Pull request body exceeds governed size limit")
    return _proposal(
        ActionPlan(
            request_id=_request_id(request_id),
            action_type="github.pr.create",
            payload={"head": clean_head, "base": "main", "title": clean_title, "body": clean_body},
            requires_human_approval=True,
        )
    )
