"""Governed read-only Neon/Postgres adapter for the private Founder workspace.

Database readiness reuses OAP's cached production probe. Optional Neon management
API inspection is fixed to the approved production project and branch. No SQL,
migrations, branch creation, auth changes, or provider mutations are exposed.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from oap.registry import founder_tool_registry

from . import database, postgres_db

_API_BASE = "https://console.neon.tech/api/v2"
_DEFAULT_PROJECT_ID = "autumn-thunder-02808657"
_DEFAULT_BRANCH_ID = "br-dry-union-a6uh2juo"


@dataclass(frozen=True, slots=True)
class NeonReadResult:
    operation: str
    data: Any


class FounderNeonReadAdapter:
    """Bounded Neon reader for the approved OAP production database."""

    def __init__(
        self,
        *,
        token: str | None = None,
        project_id: str | None = None,
        branch_id: str | None = None,
        timeout_seconds: float = 8.0,
        max_response_bytes: int = 512_000,
    ) -> None:
        self.token = token if token is not None else (
            os.getenv("OAP_NEON_API_KEY", "") or os.getenv("NEON_API_KEY", "")
        )
        self.project_id = str(
            project_id
            if project_id is not None
            else os.getenv("OAP_NEON_PROJECT_ID", _DEFAULT_PROJECT_ID)
        ).strip()
        self.branch_id = str(
            branch_id
            if branch_id is not None
            else os.getenv("OAP_NEON_BRANCH_ID", _DEFAULT_BRANCH_ID)
        ).strip()
        self.timeout_seconds = max(1.0, min(float(timeout_seconds), 20.0))
        self.max_response_bytes = max(16_384, min(int(max_response_bytes), 2_000_000))
        self._registry = founder_tool_registry()

    def _authorize(self, ability: str) -> None:
        self._registry.authorize_capability("postgres", ability, mutation=False)

    def _request_json(self, path: str) -> Any:
        if not self.token:
            raise RuntimeError("Neon management API key is not configured")
        request = Request(
            _API_BASE + path,
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer " + self.token,
                "User-Agent": "OAP-SMI-Founder-Workspace/1.0",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_response_bytes + 1)
        except HTTPError as exc:
            raise RuntimeError(f"Neon read failed with status {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError("Neon management endpoint is unavailable") from exc
        if len(raw) > self.max_response_bytes:
            raise RuntimeError("Neon response exceeded the governed size limit")
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Neon returned an invalid response") from exc

    def database_status(self) -> NeonReadResult:
        self._authorize("schema.read")
        raw = database.db_status()
        is_postgres = raw.get("backend") == "postgresql"
        data = {
            "backend": "postgresql",
            "configured": bool(is_postgres and raw.get("configured")),
            "reachable": bool(is_postgres and raw.get("reachable")),
            "initialized": bool(is_postgres and raw.get("initialized")),
            "pending": list(raw.get("pending") or []) if is_postgres else [],
            "checksum_mismatches": list(raw.get("checksum_mismatches") or []) if is_postgres else [],
            "error": raw.get("error") if is_postgres else "database_url_not_configured",
        }
        return NeonReadResult("schema.read", data)

    def project_summary(self) -> NeonReadResult:
        self._authorize("schema.read")
        data = self._request_json(f"/projects/{self.project_id}")
        project = data.get("project", data) if isinstance(data, dict) else {}
        if not isinstance(project, dict):
            raise RuntimeError("Neon returned an invalid project response")
        owner = project.get("owner") if isinstance(project.get("owner"), dict) else {}
        safe = {
            "id": project.get("id"),
            "name": project.get("name"),
            "region": project.get("region_id"),
            "pg_version": project.get("pg_version"),
            "plan": owner.get("subscription_type"),
            "branch_logical_size_limit_bytes": project.get("branch_logical_size_limit_bytes"),
            "synthetic_storage_size": project.get("synthetic_storage_size"),
            "data_transfer_bytes": project.get("data_transfer_bytes"),
            "compute_time_seconds": project.get("compute_time_seconds"),
            "active_time_seconds": project.get("active_time_seconds"),
            "consumption_period_start": project.get("consumption_period_start"),
            "consumption_period_end": project.get("consumption_period_end"),
            "compute_last_active_at": project.get("compute_last_active_at"),
        }
        return NeonReadResult("schema.read", {"project": safe})

    def branch_summary(self) -> NeonReadResult:
        self._authorize("schema.read")
        data = self._request_json(
            f"/projects/{self.project_id}/branches/{self.branch_id}"
        )
        branch = data.get("branch", data) if isinstance(data, dict) else {}
        if not isinstance(branch, dict):
            raise RuntimeError("Neon returned an invalid branch response")
        safe = {
            "id": branch.get("id"),
            "name": branch.get("name"),
            "default": branch.get("default"),
            "protected": branch.get("protected"),
            "current_state": branch.get("current_state"),
            "parent_id": branch.get("parent_id"),
            "created_at": branch.get("created_at"),
            "updated_at": branch.get("updated_at"),
        }
        return NeonReadResult("schema.read", {"branch": safe})

    def status(self) -> dict[str, object]:
        return {
            "component": "Founder Neon Read Adapter",
            "ready": postgres_db.configured(),
            "database_configured": postgres_db.configured(),
            "management_api_configured": bool(self.token),
            "project_locked": bool(self.project_id),
            "branch_locked": bool(self.branch_id),
            "read_only": True,
            "sql_execution_exposed": False,
            "migration_exposed": False,
            "credentials_exposed": False,
            "human_authority_final": True,
        }


def status() -> dict[str, object]:
    return FounderNeonReadAdapter().status()
