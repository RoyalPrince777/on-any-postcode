"""GitHub mutation adapter callable only from verified Builder context.

This module does not approve actions, mint receipts, merge pull requests, deploy,
or touch databases. It is a provider boundary for Human-approved Builder work.
"""

from __future__ import annotations

import base64
import json
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from oap.contracts import BuilderContext
from oap.registry import founder_tool_registry

from .founder_github import DEFAULT_REPOSITORY

_API_BASE = "https://api.github.com"
_BRANCH = re.compile(r"^oap-mind/[A-Za-z0-9._/-]{1,80}$")


class FounderGitHubWriteAdapter:
    """Bounded GitHub mutations behind Living Kernel → Builder."""

    def __init__(
        self,
        *,
        repository: str = DEFAULT_REPOSITORY,
        token: str | None = None,
        timeout_seconds: float = 10.0,
        max_response_bytes: int = 512_000,
    ) -> None:
        if repository != DEFAULT_REPOSITORY:
            raise PermissionError("Repository is not approved for Founder writes")
        self.repository = repository
        self.token = token if token is not None else os.getenv("OAP_GITHUB_TOKEN", "")
        if not self.token:
            raise RuntimeError("OAP_GITHUB_TOKEN is required for governed GitHub writes")
        self.timeout_seconds = max(1.0, min(float(timeout_seconds), 20.0))
        self.max_response_bytes = max(16_384, min(int(max_response_bytes), 2_000_000))
        self._registry = founder_tool_registry()

    @staticmethod
    def _require_context(context: BuilderContext) -> None:
        if not isinstance(context, BuilderContext):
            raise PermissionError("Verified Builder context is required")
        if not context.receipt_id or not context.action_digest or context.authority_level != 0:
            raise PermissionError("Human Authority Builder context is incomplete")

    def _authorize(self, ability: str, context: BuilderContext) -> None:
        self._require_context(context)
        self._registry.authorize_capability("github", ability, mutation=True)

    def _request(self, method: str, path: str, *, payload: dict[str, Any] | None = None) -> Any:
        raw_payload = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
            "User-Agent": "OAP-Mind-Founder-Workspace/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        request = Request(_API_BASE + path, data=raw_payload, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_response_bytes + 1)
        except HTTPError as exc:
            raise RuntimeError(f"GitHub governed write failed with status {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError("GitHub governed write endpoint is unavailable") from exc
        if len(raw) > self.max_response_bytes:
            raise RuntimeError("GitHub write response exceeded governed size limit")
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("GitHub returned an invalid write response") from exc

    @staticmethod
    def _validated_branch(branch: object) -> str:
        value = str(branch or "").strip()
        if not _BRANCH.fullmatch(value) or ".." in value.split("/"):
            raise ValueError("Founder branches must use the oap-mind/ prefix")
        return value

    def create_branch(self, payload: dict[str, Any], context: BuilderContext) -> None:
        self._authorize("branch.create", context)
        branch = self._validated_branch(payload.get("branch"))
        base_sha = str(payload.get("base_sha") or "").strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40}", base_sha):
            raise ValueError("A full 40-character base commit SHA is required")
        self._request(
            "POST",
            f"/repos/{self.repository}/git/refs",
            payload={"ref": "refs/heads/" + branch, "sha": base_sha},
        )

    def write_file(self, payload: dict[str, Any], context: BuilderContext) -> None:
        self._authorize("file.write", context)
        branch = self._validated_branch(payload.get("branch"))
        path = str(payload.get("path") or "").strip().lstrip("/")
        message = str(payload.get("message") or "").strip()
        content = payload.get("content")
        current_sha = str(payload.get("sha") or "").strip()
        if not path or ".." in path.split("/"):
            raise ValueError("Repository path is invalid")
        if not message or len(message) > 160:
            raise ValueError("Commit message is required and must be at most 160 characters")
        if not isinstance(content, str) or len(content.encode("utf-8")) > 500_000:
            raise ValueError("UTF-8 file content must be at most 500 KB")
        body: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": branch,
        }
        if current_sha:
            if not re.fullmatch(r"[0-9a-fA-F]{40}", current_sha):
                raise ValueError("Existing file SHA must be 40 hexadecimal characters")
            body["sha"] = current_sha
        encoded = "/".join(quote(part, safe="") for part in path.split("/"))
        self._request("PUT", f"/repos/{self.repository}/contents/{encoded}", payload=body)

    def create_pull_request(self, payload: dict[str, Any], context: BuilderContext) -> None:
        self._authorize("pr.create", context)
        head = self._validated_branch(payload.get("head"))
        base = str(payload.get("base") or "main").strip()
        title = str(payload.get("title") or "").strip()
        body = str(payload.get("body") or "").strip()
        if base != "main":
            raise PermissionError("Founder coding pull requests must target main")
        if not title or len(title) > 160:
            raise ValueError("Pull request title is required and must be at most 160 characters")
        if len(body) > 20_000:
            raise ValueError("Pull request body exceeds governed size limit")
        self._request(
            "POST",
            f"/repos/{self.repository}/pulls",
            payload={"head": head, "base": base, "title": title, "body": body, "draft": False},
        )

    def status(self) -> dict[str, object]:
        return {
            "component": "Founder GitHub Builder Adapter",
            "ready": bool(self.token),
            "repository": self.repository,
            "branch_prefix": "oap-mind/",
            "requires_builder_context": True,
            "requires_human_approval": True,
            "main_direct_write": False,
            "merge_enabled": False,
            "deploy_enabled": False,
            "database_mutation_enabled": False,
            "independent_execute": False,
        }


def register_github_builder_actions(builder) -> None:
    """Register only the approved first-slice GitHub mutations with Builder."""
    adapter = FounderGitHubWriteAdapter()
    builder.register("github.branch.create", adapter.create_branch)
    builder.register("github.file.write", adapter.write_file)
    builder.register("github.pr.create", adapter.create_pull_request)
