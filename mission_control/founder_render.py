"""Governed read-only Render adapter for the private Founder workspace.

Only the two approved OAP Render services are inspectable. This module never
triggers deploys, changes environment variables, or exposes provider credentials.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from oap.registry import founder_tool_registry

_API_BASE = "https://api.render.com/v1"
_DEFAULT_WORKSPACE_ID = "tea-d8gfop6k1jcs73cuvff0"
_DEFAULT_SERVICES = {
    "world": "srv-d8gfsv0jo6nc73egdlf0",
    "smi": "srv-da6tp615efls73ct81q0",
}
_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+\-/=]+"),
    re.compile(r"(?i)postgres(?:ql)?://[^\s'\"]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"(?i)\b([A-Z0-9_]*(?:TOKEN|PASSWORD|SECRET|API_KEY)[A-Z0-9_]*\s*=\s*)[^\s]+"),
)


@dataclass(frozen=True, slots=True)
class RenderReadResult:
    operation: str
    data: Any


def _redact_text(value: object) -> str:
    text = str(value or "")[:4000]
    for pattern in _SECRET_PATTERNS:
        if "postgres" in pattern.pattern.casefold() or "sk-" in pattern.pattern:
            text = pattern.sub("[REDACTED]", text)
        else:
            text = pattern.sub(r"\1[REDACTED]", text)
    return text


class FounderRenderReadAdapter:
    """Bounded Render reader for the two approved OAP services."""

    def __init__(
        self,
        *,
        token: str | None = None,
        workspace_id: str | None = None,
        timeout_seconds: float = 8.0,
        max_response_bytes: int = 512_000,
    ) -> None:
        self.token = token if token is not None else (
            os.getenv("OAP_RENDER_API_KEY", "") or os.getenv("RENDER_API_KEY", "")
        )
        self.workspace_id = str(
            workspace_id
            if workspace_id is not None
            else os.getenv("OAP_RENDER_WORKSPACE_ID", _DEFAULT_WORKSPACE_ID)
        ).strip()
        self.timeout_seconds = max(1.0, min(float(timeout_seconds), 20.0))
        self.max_response_bytes = max(16_384, min(int(max_response_bytes), 2_000_000))
        self._registry = founder_tool_registry()
        self._services = {
            "world": os.getenv("OAP_RENDER_WORLD_SERVICE_ID", _DEFAULT_SERVICES["world"]).strip(),
            "smi": os.getenv("OAP_RENDER_SMI_SERVICE_ID", _DEFAULT_SERVICES["smi"]).strip(),
        }

    def _authorize(self, ability: str) -> None:
        self._registry.authorize_capability("render", ability, mutation=False)

    def _service_id(self, alias: str) -> str:
        clean = str(alias or "").strip().casefold()
        if clean not in self._services or not self._services[clean]:
            raise PermissionError("Render service is not approved for the Founder workspace")
        return self._services[clean]

    def _request_json(self, path: str, *, query: dict[str, object] | None = None) -> Any:
        if not self.token:
            raise RuntimeError("Render API key is not configured")
        suffix = "?" + urlencode(query, doseq=True) if query else ""
        request = Request(
            _API_BASE + path + suffix,
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
            raise RuntimeError(f"Render read failed with status {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError("Render read endpoint is unavailable") from exc
        if len(raw) > self.max_response_bytes:
            raise RuntimeError("Render response exceeded the governed size limit")
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Render returned an invalid response") from exc

    @staticmethod
    def _service_projection(data: dict[str, Any], *, alias: str) -> dict[str, Any]:
        details = data.get("serviceDetails") if isinstance(data.get("serviceDetails"), dict) else {}
        return {
            "alias": alias,
            "id": data.get("id"),
            "name": data.get("name"),
            "type": data.get("type"),
            "branch": data.get("branch"),
            "auto_deploy": data.get("autoDeploy"),
            "suspended": data.get("suspended"),
            "updated_at": data.get("updatedAt"),
            "runtime": details.get("runtime") or details.get("env"),
            "region": details.get("region"),
            "plan": details.get("plan"),
            "health_check_path": details.get("healthCheckPath"),
            "instances": details.get("numInstances"),
            "url": details.get("url"),
        }

    def services_summary(self) -> RenderReadResult:
        self._authorize("service.read")
        services = []
        for alias in ("world", "smi"):
            service_id = self._service_id(alias)
            data = self._request_json(f"/services/{service_id}")
            if not isinstance(data, dict):
                raise TypeError("Render returned an invalid service response")
            services.append(self._service_projection(data, alias=alias))
        return RenderReadResult("service.read", {"services": services})

    def deploys(self, alias: str, *, limit: int = 5) -> RenderReadResult:
        self._authorize("deploy.read")
        service_id = self._service_id(alias)
        bounded_limit = max(1, min(int(limit), 10))
        data = self._request_json(
            f"/services/{service_id}/deploys",
            query={"limit": bounded_limit},
        )
        if not isinstance(data, list):
            raise TypeError("Render returned an invalid deploy response")
        deploys = []
        for raw_item in data[:bounded_limit]:
            item = raw_item.get("deploy", raw_item) if isinstance(raw_item, dict) else {}
            commit = item.get("commit") if isinstance(item.get("commit"), dict) else {}
            deploys.append(
                {
                    "id": item.get("id"),
                    "status": item.get("status"),
                    "trigger": item.get("trigger"),
                    "created_at": item.get("createdAt"),
                    "started_at": item.get("startedAt"),
                    "finished_at": item.get("finishedAt"),
                    "commit": {
                        "id": commit.get("id"),
                        "message": _redact_text(commit.get("message"))[:500],
                    },
                }
            )
        return RenderReadResult("deploy.read", {"service": alias, "deploys": deploys})

    def logs(self, alias: str, *, limit: int = 20) -> RenderReadResult:
        self._authorize("logs.read")
        service_id = self._service_id(alias)
        bounded_limit = max(1, min(int(limit), 50))
        data = self._request_json(
            "/logs",
            query={
                "ownerId": self.workspace_id,
                "resource": [service_id],
                "limit": bounded_limit,
                "direction": "backward",
            },
        )
        rows = data.get("logs") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise TypeError("Render returned an invalid logs response")
        logs = []
        for item in rows[:bounded_limit]:
            if not isinstance(item, dict):
                continue
            labels = item.get("labels") if isinstance(item.get("labels"), list) else []
            safe_labels = {
                str(label.get("name")): str(label.get("value"))[:120]
                for label in labels
                if isinstance(label, dict)
                and label.get("name") in {"level", "type", "statusCode", "method", "path"}
            }
            logs.append(
                {
                    "timestamp": item.get("timestamp"),
                    "labels": safe_labels,
                    "message": _redact_text(item.get("message")),
                }
            )
        return RenderReadResult("logs.read", {"service": alias, "logs": logs})

    def status(self) -> dict[str, object]:
        return {
            "component": "Founder Render Read Adapter",
            "ready": bool(self.token),
            "configured": bool(self.token),
            "approved_services": ("world", "smi"),
            "read_only": True,
            "independent_deploy": False,
            "credentials_exposed": False,
            "human_authority_final": True,
        }


def status() -> dict[str, object]:
    return FounderRenderReadAdapter().status()
