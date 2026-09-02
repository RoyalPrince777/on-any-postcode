"""OAP-owned inference gateway for Personal SMI.

The gateway owns routing policy. It prefers an OAP-controlled local/Home Node
runtime and degrades to a compatibility engine only while that node is not
certified. Provider brands are not part of Personal SMI identity or authority.
"""
from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from typing import Any
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit

LOCAL_URL = os.environ.get(
    "OAP_INFERENCE_LOCAL_URL", "http://127.0.0.1:11434/api/chat"
).strip()
LOCAL_MODEL = os.environ.get("OAP_INFERENCE_LOCAL_MODEL", "oap-core:latest").strip()
LOCAL_ENABLED = os.environ.get("OAP_INFERENCE_LOCAL_ENABLED", "1").strip().lower() not in {
    "0", "false", "no", "off"
}
FALLBACK_ENABLED = os.environ.get("OAP_INFERENCE_COMPATIBILITY_FALLBACK", "1").strip().lower() not in {
    "0", "false", "no", "off"
}
_PROBE_TTL_SECONDS = 30.0
_probe_cache: tuple[float, dict[str, Any]] | None = None


def _local_messages(message: str, history: list[dict[str, str]] | None, brain: dict | None,
                    adaptive_memory: list[str] | None, *, code_mode: bool) -> list[dict[str, str]]:
    system = (
        "You are Personal SMI, the private Founder-facing mode of Sovereign Megaverse "
        "Intelligence inside ON ANY POSTCODE. Be direct and concise. HRM is the memory "
        "organ; Aegis protects; Living Kernel controls authorisation; Human Authority is "
        "final. Never invent live system state. Never expose private Founder context to "
        "public surfaces. Health and wellbeing guidance is informational, evidence-grounded "
        "and non-diagnostic. Security claims must distinguish verified evidence from possibility. "
        "You may recommend and write reviewable code, but never claim an apply, commit, merge, "
        "deploy, payment, dispatch or other protected action occurred unless verified evidence says it did."
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
    messages: list[dict[str, str]] = [{
        "role": "system",
        "content": system + "\nRouting context: " + json.dumps(routing, separators=(",", ":")),
    }]
    for item in (history or [])[-12:]:
        role = str(item.get("role", ""))
        content = str(item.get("content", ""))[:4000]
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": str(message or "")[:12000]})
    return messages


def _call_local(message: str, history: list[dict[str, str]] | None, brain: dict | None,
                adaptive_memory: list[str] | None, *, code_mode: bool) -> str:
    if not LOCAL_ENABLED or not LOCAL_URL or not LOCAL_MODEL:
        raise RuntimeError("local_inference_disabled")
    payload = json.dumps({
        "model": LOCAL_MODEL,
        "messages": _local_messages(message, history, brain, adaptive_memory, code_mode=code_mode),
        "stream": False,
        "options": {"temperature": 0.2},
    }).encode()
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
    text = str((body.get("message") or {}).get("content", "")).strip() or str(body.get("response", "")).strip()
    if not text:
        raise RuntimeError("local_inference_empty")
    return text[:12000]


def _tags_url() -> str:
    parts = urlsplit(LOCAL_URL)
    return urlunsplit((parts.scheme, parts.netloc, "/api/tags", "", ""))


def probe_local(*, force: bool = False) -> dict[str, Any]:
    """Return bounded proof of Home Node reachability and configured model availability."""
    global _probe_cache
    now = time.monotonic()
    if not force and _probe_cache and now - _probe_cache[0] < _PROBE_TTL_SECONDS:
        return dict(_probe_cache[1])
    result: dict[str, Any] = {
        "reachable": False,
        "model_available": False,
        "model": LOCAL_MODEL,
        "reason": "local_inference_disabled" if not LOCAL_ENABLED else "unverified",
    }
    if LOCAL_ENABLED and LOCAL_URL and LOCAL_MODEL:
        req = urlrequest.Request(_tags_url(), headers={"Accept": "application/json"}, method="GET")
        try:
            with urlrequest.urlopen(req, timeout=1.0) as response:
                body = json.loads(response.read().decode("utf-8", errors="replace"))
            names = {
                str(item.get("name") or item.get("model") or "")
                for item in body.get("models", [])
                if isinstance(item, dict)
            }
            result.update(
                reachable=True,
                model_available=LOCAL_MODEL in names,
                reason="verified" if LOCAL_MODEL in names else "configured_model_missing",
            )
        except HTTPError as exc:
            result["reason"] = f"local_probe_http_{exc.code}"
        except (URLError, TimeoutError, OSError, json.JSONDecodeError):
            result["reason"] = "local_probe_unavailable"
    _probe_cache = (now, dict(result))
    return result


def generate(compatibility_engine: Callable[..., str], message: str, image_data: str = "",
             history: list[dict[str, str]] | None = None, brain: dict | None = None,
             adaptive_memory: list[str] | None = None, media: dict | None = None, *,
             code_mode: bool = False, on_delta: Callable[[str], None] | None = None) -> str:
    """Route Personal SMI generation through the OAP-owned policy boundary."""
    use_local = not image_data and not (media or {}).get("content_items") and not (media or {}).get("transcript")
    local_error: RuntimeError | None = None
    if use_local:
        try:
            text = _call_local(message, history, brain, adaptive_memory, code_mode=code_mode)
            if on_delta is not None:
                on_delta(text)
            return text
        except RuntimeError as exc:
            local_error = exc
    if not FALLBACK_ENABLED:
        raise RuntimeError("local_inference_required") from local_error
    return compatibility_engine(
        message, image_data, history, brain, adaptive_memory, media,
        code_mode=code_mode, on_delta=on_delta,
    )


def status(*, probe: bool = False) -> dict[str, Any]:
    proof = probe_local() if probe else {
        "reachable": None,
        "model_available": None,
        "model": LOCAL_MODEL,
        "reason": "not_probed",
    }
    sovereign_ready = bool(
        proof.get("reachable") and proof.get("model_available") and not FALLBACK_ENABLED
    )
    return {
        "gateway": "OAP Inference Gateway",
        "local_first": True,
        "local_enabled": LOCAL_ENABLED,
        "local_url_configured": bool(LOCAL_URL),
        "local_model_configured": bool(LOCAL_MODEL),
        "home_node": proof,
        "compatibility_fallback_enabled": FALLBACK_ENABLED,
        "sovereign_inference_ready": sovereign_ready,
        "human_authority_final": True,
    }
