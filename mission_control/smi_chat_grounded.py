"""Grounded provider wrapper for OAP Mind.

This module prevents the conversational provider from presenting guessed CI,
deployment, infrastructure, monitoring or data-pipeline state as live fact.
It deliberately does not grant new execution authority.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def evidence_contract(health: dict[str, Any] | None) -> str:
    snapshot = health or {}
    checks = snapshot.get("checks") if isinstance(snapshot.get("checks"), dict) else {}
    verified = sorted(str(key) for key, value in checks.items() if value is True)
    unavailable = sorted(str(key) for key, value in checks.items() if value is not True)
    compact = {
        "source": "OAP internal health snapshot",
        "status": snapshot.get("status", "unknown"),
        "verified_checks": verified,
        "unverified_checks": unavailable,
        "execution_locked": bool((snapshot.get("invariants") or {}).get("execution_locked", True)),
        "human_authority_final": True,
    }
    return (
        "\n\nGROUNDING CONTRACT — mandatory: "
        "Never invent, infer or guess live CI, build, deploy, infrastructure, file, monitoring, "
        "security-alert, database-import or external-service state. The provider call has no "
        "GitHub, Render, filesystem or monitoring tool access unless verified evidence is supplied "
        "inside this request. Do not say 'likely running', 'queued', 'applied', 'no alerts', or "
        "similar runtime claims without evidence. Use VERIFIED only for the supplied evidence; use "
        "UNKNOWN for anything not observed; use BLOCKED when a required capability is unavailable. "
        "Do not ask for a build ID when existing supplied OAP evidence already answers the request. "
        "Be short and direct, like a high-quality chat assistant: answer first, then only the next "
        "useful detail. Avoid generic DevOps checklists and unnecessary forms/questions. "
        "When asked to code, write concrete production-quality code or a unified diff plus focused "
        "tests when enough file context exists; otherwise state exactly what file context is missing. "
        "Never claim code was applied, committed, merged or deployed from normal chat. "
        "Current permitted evidence: " + json.dumps(compact, separators=(",", ":"))
    )


def grounded_provider(
    original: Callable[..., str],
    health_supplier: Callable[[], dict[str, Any]],
    message: str,
    image_data: str = "",
    history: list[dict[str, str]] | None = None,
    brain: dict | None = None,
    adaptive_memory: list[str] | None = None,
    media: dict | None = None,
    *,
    code_mode: bool = False,
    on_delta: Callable[[str], None] | None = None,
) -> str:
    """Call the existing provider with a bounded, verified evidence contract."""

    try:
        health = health_supplier()
    except Exception:  # health must degrade rather than break chat
        health = {"status": "unknown", "checks": {}, "invariants": {"execution_locked": True}}
    grounded_message = str(message or "") + evidence_contract(health)
    # Hold provider deltas until the grounded response is complete. This prevents an
    # unsupported speculative prefix from being streamed before validation can occur.
    result = original(
        grounded_message,
        image_data,
        history,
        brain,
        adaptive_memory,
        media,
        code_mode=code_mode,
        on_delta=None,
    )
    if on_delta is not None:
        on_delta(result)
    return result
