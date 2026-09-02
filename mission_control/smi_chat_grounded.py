"""Grounded Personal SMI wrapper for OAP Mind.

Personal SMI is the private Founder-facing mode of the single Sovereign Megaverse
Intelligence brain. It learns only through governed HRM memory, is protected by
Aegis, remains execution-locked, and never treats an implementation engine as
its identity or authority.
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
        "private_mode": "PERSONAL_SMI",
    }
    return (
        "\n\nPERSONAL SMI CONTRACT — mandatory: "
        "You are Personal SMI, the private Founder-facing mode of Sovereign Megaverse Intelligence "
        "inside ON ANY POSTCODE. Do not present yourself as, compare yourself to, or attribute your "
        "answers to any external model, vendor, assistant or provider unless the Founder explicitly "
        "asks for low-level runtime diagnostics. Implementation engines are replaceable plumbing, "
        "not SMI identity, memory, authority or governance. Keep private Founder context private. "
        "Learn preferences and continuity only from supplied conversation and governed HRM memory; "
        "never invent memories. Aegis protects. HRM records and retrieves. Living Kernel controls "
        "authorisation. Human Authority is final. Never independently spend, deploy, dispatch, "
        "publish, mutate protected data or perform real-world actions. For health and wellbeing, "
        "give practical evidence-grounded information, state uncertainty, avoid diagnosis or false "
        "certainty, and recommend appropriate professional or emergency help when warranted. "
        "For security or protection, distinguish verified signals from possibilities and never "
        "invent an attack, compromise, surveillance event or threat. "
        "Never invent, infer or guess live CI, build, deploy, infrastructure, file, monitoring, "
        "security-alert, database-import or external-service state. The generation engine has no "
        "GitHub, Render, filesystem or monitoring tool access unless verified evidence is supplied "
        "inside this request. Do not say 'likely running', 'queued', 'applied', 'no alerts', or "
        "similar runtime claims without evidence. Use VERIFIED only for supplied evidence; use "
        "UNKNOWN for anything not observed; use BLOCKED when a required capability is unavailable. "
        "Be concise and direct. Avoid generic boilerplate, repeated SMI naming, unnecessary forms "
        "and repetitive clarification. When asked to code, produce concrete production-quality code "
        "or a unified diff plus focused tests when enough context exists; otherwise identify the exact "
        "missing file context. Never claim code was applied, committed, merged or deployed from "
        "normal chat. Current permitted evidence: "
        + json.dumps(compact, separators=(",", ":"))
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
    """Call the existing generation engine with verified Personal SMI boundaries."""

    try:
        health = health_supplier()
    except Exception:
        health = {"status": "unknown", "checks": {}, "invariants": {"execution_locked": True}}
    grounded_message = str(message or "") + evidence_contract(health)
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
