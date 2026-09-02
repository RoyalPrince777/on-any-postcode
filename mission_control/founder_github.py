"""Governed read-only GitHub adapter for the private Founder workspace.

The adapter can inspect the approved OAP repository but cannot mutate GitHub.
Write actions remain proposals that must later pass Human Authority, Living Kernel
and Builder before any provider-specific mutation is invoked.
"""

from __future__ import annotations

import base64
import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from oap.registry import founder_tool_registry

DEFAULT_REPOSITORY = "RoyalPrince777/on-any-postcode"
_API_BASE = "https://api.github.com"
_ALLOWED_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_ALLOWED_REF = re.compile(r"^[A-Za-z0-9._/-]+$")


@dataclass(frozen=True, slots=True)
class GitHubReadResult:
    operation: str
    repository: str
    data: Any


class FounderGitHubReadAdapter:
    """Bounded GitHub reader exposed to authenticated OAP Mind sessions."""

    def __init__(
        self,
        *,
        repository: str = DEFAULT_REPOSITORY,
        token: str | None = None,
        timeout_seconds: float = 8.0,
        max_response_bytes: int = 512_000,
    ) -> None:
        if not _ALLOWED_REPOSITORY.fullmatch(repository):
            raise ValueError("Repository must use owner/name form")
        if repository != DEFAULT_REPOSITORY:
            raise PermissionError("Repository is not approved for the Founder workspace")
        self.repository = repository
        self.token = token if token is not None else os.getenv("OAP_GITHUB_TOKEN", "")
        self.timeout_seconds = max(1.0, min(float(timeout_seconds), 20.0))
        self.max_response_bytes = max(16_384, min(int(max_response_bytes), 2_000_000))
        self._registry = founder_tool_registry()

    def _authorize(self, ability: str) -> None:
        self._registry.authorize_capability("github", ability, mutation=False)

    def _request_json(self, path: str, *, query: dict[str, object] | None = None) -> Any:
        suffix = "?" + urlencode(query) if query else ""
        url = _API_BASE + path + suffix
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "OAP-Mind-Founder-Workspace/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_response_bytes + 1)
        except HTTPError as exc:
            raise RuntimeError(f"GitHub read failed with status {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError("GitHub read endpoint is unavailable") from exc
        if len(raw) > self.max_response_bytes:
            raise RuntimeError("GitHub response exceeded the governed size limit")
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("GitHub returned an invalid response") from exc

    def repository_summary(self) -> GitHubReadResult:
        self._authorize("repo.read")
        data = self._request_json(f"/repos/{self.repository}")
        keep = {
            key: data.get(key)
            for key in (
                "full_name",
                "private",
                "default_branch",
                "description",
                "language",
                "archived",
                "disabled",
                "updated_at",
                "pushed_at",
            )
        }
        return GitHubReadResult("repo.read", self.repository, keep)

    def read_file(self, path: str, *, ref: str = "main", max_chars: int = 120_000) -> GitHubReadResult:
        self._authorize("file.read")
        clean_path = str(path or "").strip().lstrip("/")
        if not clean_path or ".." in clean_path.split("/"):
            raise ValueError("Repository path is invalid")
        if not _ALLOWED_REF.fullmatch(ref):
            raise ValueError("Git reference is invalid")
        encoded_path = "/".join(quote(part, safe="") for part in clean_path.split("/"))
        data = self._request_json(
            f"/repos/{self.repository}/contents/{encoded_path}",
            query={"ref": ref},
        )
        if not isinstance(data, dict) or data.get("type") != "file":
            raise LookupError("Requested repository path is not a file")
        content = data.get("content") or ""
        if data.get("encoding") != "base64":
            raise RuntimeError("GitHub file encoding is unsupported")
        try:
            decoded = base64.b64decode(content, validate=False).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise RuntimeError("Repository file is not UTF-8 text") from exc
        limit = max(1_000, min(int(max_chars), 250_000))
        return GitHubReadResult(
            "file.read",
            self.repository,
            {
                "path": clean_path,
                "ref": ref,
                "sha": data.get("sha"),
                "truncated": len(decoded) > limit,
                "content": decoded[:limit],
            },
        )

    def search_code(self, query: str, *, limit: int = 10) -> GitHubReadResult:
        self._authorize("code.search")
        clean_query = " ".join(str(query or "").split())
        if not clean_query:
            raise ValueError("Search query is required")
        limit = max(1, min(int(limit), 20))
        data = self._request_json(
            "/search/code",
            query={"q": f"{clean_query} repo:{self.repository}", "per_page": limit},
        )
        items = []
        for item in (data.get("items") or [])[:limit]:
            items.append(
                {
                    "name": item.get("name"),
                    "path": item.get("path"),
                    "sha": item.get("sha"),
                    "html_url": item.get("html_url"),
                }
            )
        return GitHubReadResult("code.search", self.repository, {"query": clean_query, "items": items})

    def pull_request_diff(self, number: int, *, max_chars: int = 160_000) -> GitHubReadResult:
        self._authorize("diff.read")
        pr_number = int(number)
        if pr_number < 1:
            raise ValueError("Pull request number must be positive")
        path = f"/repos/{self.repository}/pulls/{pr_number}"
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "OAP-Mind-Founder-Workspace/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(_API_BASE + path, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_response_bytes + 1)
        except HTTPError as exc:
            raise RuntimeError(f"GitHub diff read failed with status {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError("GitHub diff endpoint is unavailable") from exc
        if len(raw) > self.max_response_bytes:
            raise RuntimeError("GitHub diff exceeded the governed size limit")
        try:
            diff = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RuntimeError("GitHub diff is not UTF-8 text") from exc
        limit = max(1_000, min(int(max_chars), 250_000))
        return GitHubReadResult(
            "diff.read",
            self.repository,
            {"pull_request": pr_number, "truncated": len(diff) > limit, "diff": diff[:limit]},
        )

    def status(self) -> dict[str, object]:
        return {
            "component": "Founder GitHub Read Adapter",
            "ready": True,
            "repository": self.repository,
            "token_configured": bool(self.token),
            "read_only": True,
            "network": "https_api",
            "independent_write": False,
            "human_authority_final": True,
        }


def status() -> dict[str, object]:
    return FounderGitHubReadAdapter().status()
