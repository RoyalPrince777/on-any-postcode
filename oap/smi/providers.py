"""Explicit provider routing; providers advise and never become OAP agents."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Protocol
from urllib import error, request
from urllib.parse import urlparse

from oap.contracts import FocusedSignal, ProviderResult

from .sovereign_controls import SovereignControlPlane


class _NoRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        del req, fp, code, msg, headers, newurl


_LOCAL_ONLY_OPENER = request.build_opener(_NoRedirectHandler())


class ProviderAdapter(Protocol):
    provider_id: str
    sovereign_scope: str

    def analyse(self, signal: FocusedSignal) -> ProviderResult: ...


class OllamaAdapter:
    """Local-loopback Ollama advisor with bounded timeout and output."""

    provider_id = "ollama"
    sovereign_scope = "local"

    def __init__(
        self,
        url: str = "http://127.0.0.1:11434/api/generate",
        model: str = "qwen2.5:1.5b",
        timeout: float = 3.0,
    ) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Ollama URL must use HTTP or HTTPS")
        if parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Ollama advisor is restricted to loopback")
        self.url = url
        self.model = model
        self.timeout = timeout

    def analyse(self, signal: FocusedSignal) -> ProviderResult:
        payload = json.dumps(
            {
                "model": self.model,
                "prompt": (
                    "Analyse this OAP request as an advisor only. Do not execute, "
                    "approve, publish or invent facts.\n\n" + signal.content[:8_000]
                ),
                "stream": False,
            }
        ).encode("utf-8")
        http_request = request.Request(
            self.url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with _LOCAL_ONLY_OPENER.open(
                http_request,
                timeout=self.timeout,
            ) as response:
                final_url = urlparse(response.geturl())
                if final_url.hostname not in {"localhost", "127.0.0.1", "::1"}:
                    raise ValueError("Provider redirected outside loopback")
                body = json.loads(response.read(1_000_000).decode("utf-8"))
        except (OSError, ValueError, error.URLError, json.JSONDecodeError):
            return ProviderResult(
                provider_id=self.provider_id,
                available=False,
                text="",
                error_code="provider_unavailable",
            )
        text = str(body.get("response", ""))[:12_000]
        return ProviderResult(
            provider_id=self.provider_id,
            available=bool(text),
            text=text,
            error_code=None if text else "empty_response",
        )


class ProviderRouter:
    """Route only explicitly assigned providers that pass sovereign egress policy."""

    def __init__(
        self,
        adapters: tuple[ProviderAdapter, ...] = (),
        approved_assignments: Mapping[str, str] | None = None,
        sovereign_controls: SovereignControlPlane | None = None,
    ) -> None:
        adapter_ids = [adapter.provider_id for adapter in adapters]
        if len(adapter_ids) != len(set(adapter_ids)):
            raise ValueError("Duplicate provider adapters")

        provider_scopes: dict[str, str] = {}
        for adapter in adapters:
            scope = str(getattr(adapter, "sovereign_scope", "external")).casefold()
            if scope not in {"local", "external"}:
                raise ValueError("Provider sovereign_scope must be local or external")
            provider_scopes[adapter.provider_id] = scope

        self._adapters = {adapter.provider_id: adapter for adapter in adapters}
        self._provider_scopes = provider_scopes
        self._assignments = {
            task.casefold(): provider_id
            for task, provider_id in (approved_assignments or {}).items()
        }
        self._sovereign_controls = sovereign_controls or SovereignControlPlane()
        unknown = set(self._assignments.values()) - set(self._adapters)
        if unknown:
            raise ValueError("Provider assignment references an unavailable adapter")

    def route(self, signal: FocusedSignal) -> tuple[ProviderResult, ...]:
        provider_id = self._assignments.get(signal.task_type.casefold())
        if provider_id is None:
            return ()

        adapter = self._adapters[provider_id]
        local = self._provider_scopes[provider_id] == "local"
        if not self._sovereign_controls.provider_allowed(provider_id, local=local):
            return (
                ProviderResult(
                    provider_id=provider_id,
                    available=False,
                    text="",
                    error_code="sovereign_provider_blocked",
                ),
            )

        try:
            result = adapter.analyse(signal)
        except Exception:  # noqa: BLE001 - provider adapters are a trust boundary.
            return (
                ProviderResult(
                    provider_id=provider_id,
                    available=False,
                    text="",
                    error_code="provider_failure",
                ),
            )
        if not isinstance(result, ProviderResult):
            return (
                ProviderResult(
                    provider_id=provider_id,
                    available=False,
                    text="",
                    error_code="invalid_provider_result",
                ),
            )
        text = result.text[:12_000] if isinstance(result.text, str) else ""
        error_code = (
            result.error_code[:128]
            if isinstance(result.error_code, str) and result.error_code
            else "provider_unavailable"
        )
        return (
            ProviderResult(
                provider_id=provider_id,
                available=bool(result.available and text),
                text=text,
                error_code=(None if result.available and text else error_code),
            ),
        )

    def status(self) -> dict[str, object]:
        return {
            "component": "Provider Router",
            "ready": True,
            "adapters": tuple(self._adapters),
            "approved_assignments": dict(self._assignments),
            "provider_scopes": dict(self._provider_scopes),
            "external_provider_egress_default": "deny",
            "sovereign_policy_fingerprint": (
                self._sovereign_controls.policy_fingerprint()
            ),
            "authority": False,
        }
