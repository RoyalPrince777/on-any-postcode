"""OAP-owned inference gateway for Personal SMI.

The gateway owns routing policy. It prefers an OAP-controlled local/Home Node
runtime and degrades to a compatibility engine only while that node is not
reachable. Provider brands are not part of Personal SMI identity or authority.
"""
from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

LOCAL_URL = os.environ.get(
    "OAP_INFERENCE_LOCAL_URL", "http://127.0.0.1:11434/api/chat"
).strip()
LOCAL_MODEL = os.environ.get("OAP_INFERENCE_LOCAL_MODEL", "oap-core:latest").strip()
LOCAL_ENABLED = os.environ.get("OAP_INFERENCE_LOCAL_ENABLED", "1").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}


def _local_messages(
    message: str,
    history: list[dict[str, str]] | None,
    brain: dict | None,
    adaptive_memory: list[str] | None,
    *,
    code_mode: bool,
) -> list[dict[str, str]]:
    system = (
        "You are Personal SMI, the private Founder-facing mode of Sovereign Megaverse "
        "Intelligence inside ON ANY POSTCODE. Be direct and concise. HRM is the memory "
        "organ; Aegis protects; Living Kernel controls authorisation; Human Authority is "
        "final. Never invent live system state. Never expose private Founder context to "
        "public surfaces. Health and wellbeing guidance is informational, evidence-grounded "
        "and non-diagnostic. Security claims must distinguish verified evidence from possibility. "
        "You may recommend and write reviewable code, but never claim an apply, commit, merge, "
        "deploy, payment, dispatch or other protected action occurred unless verified evidence "
        "says it did."
    )
    if code_mode:
        system += (
            " CODE MODE: return concrete production-quality code or a unified diff with focused "
            "tests when enough context exists. Label assumptions and preserve existing OAP organs."
        )
    routing = {
        "task_type": (brain or {}).get("task_type"),
        "signal_level": (brain or {}).get("signal_level"),
        "war_room_triggered": (brain or {}).get("war_room", {}).get("triggered", False),
        "hrm_lessons": [str(item)[:300] for item in (adaptive_memory or [])[-5:]],
    }
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system + "\nRouting context: " + json.dumps(routing, separators=(",", ":"))}
    ]
    for item in (history or [])[-12:]:
        role = str(item.get("role", ""))
        content = str(item.get("content", ""))[:4000]
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": str(message or "")[:12000]})
    return messages


def _call_local(
    message: str,
    history: list[dict[str, str]] | None,
    brain: dict | None,
    adaptive_memory: list[str] | None,
    *,
    code_mode: bool,
) -> str:
    if not LOCAL_ENABLED or not LOCAL_URL or not LOCAL_MODEL:
        raise RuntimeError("local_inference_disabled")
    payload = json.dumps(
        {
            "model": LOCAL_MODEL,
            "messages": _local_messages(
                message, history, brain, adaptive_memory, code_mode=code_mode
            ),
            "stream": False,
            "options": {"temperature": 0.2},
        }
    ).encode()
    req = urlrequest.Request(
        LOCAL_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=2.0) as response:
            body = json.loads(response.read().decode("utf-8", errors="replace"))
    except HTTPError as exc:
        raise RuntimeError(f"local_inference_http_{exc.code}") from exc
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("local_inference_unavailable") from exc
    text = str((body.get("message") or {}).get("content", "")).strip()
    if not text:
        text = str(body.get("response", "")).strip()
    if not text:
        raise RuntimeError("local_inference_empty")
    return text[:12000]


def generate(
    compatibility_engine: Callable[..., str],
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
    """Route Personal SMI generation through the OAP-owned policy boundary."""

    # Keep richer media working until the local runtime is certified for those modalities.
    use_local = not image_data and not (media or {}).get("content_items") and not (media or {}).get("transcript")
    if use_local:
        try:
            text = _call_local(
                message,
                history,
                brain,
                adaptive_memory,
                code_mode=code_mode,
            )
            if on_delta is not None:
                on_delta(text)
            return text
        except RuntimeError:
            pass

    # Compatibility fallback is deliberately below the gateway. It has no identity or
    # authority of its own and can be removed once the Home Node is reachable/certified.
    return compatibility_engine(
        message,
        image_data,
        history,
        brain,
        adaptive_memory,
        media,
        code_mode=code_mode,
        on_delta=on_delta,
    )


def status() -> dict[str, Any]:
    return {
        "gateway": "OAP Inference Gateway",
        "local_first": True,
        "local_enabled": LOCAL_ENABLED,
        "local_url_configured": bool(LOCAL_URL),
        "local_model_configured": bool(LOCAL_MODEL),
        "compatibility_fallback_present": True,
        "human_authority_final": True,
    }
