"""Read-only projection for the governed first-party Personal SMI pathway."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from . import config, smi_thinking_process
from .smi_chat_runtime import health

PROVIDER_ID = "openai"
PROVIDER_NAME = "OpenAI"
DEFAULT_MODEL = "gpt-5-mini"
GENERATE_PATH = "/api/generate"

CHAT_PATHWAY = (
    {"step": "OAP Dashboard Chat", "responsibility": "Receives bounded human text"},
    {"step": "Identity", "responsibility": "Validates the human requester"},
    {"step": "Living Kernel", "responsibility": "Checks permission and safety gates"},
    {"step": "SMI Mind", "responsibility": "Runs the governed seven-stage Thinking Process"},
    {"step": "Inference Gateway", "responsibility": "Routes replaceable generation plumbing"},
    {"step": "Guardian", "responsibility": "Reviews the proposed response"},
    {"step": "Judgement", "responsibility": "Consolidates bounded evidence and confidence"},
    {"step": "HRM", "responsibility": "Records the reviewed interaction"},
    {"step": "Human Authority", "responsibility": "Remains the final authority"},
)


def _loopback_endpoint() -> bool:
    parsed = urlparse(config.OLLAMA_URL)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {
        "localhost",
        "127.0.0.1",
        "::1",
    }


def _public_runtime(runtime: dict[str, Any]) -> dict[str, Any]:
    """Project runtime health without exposing private integrity metadata."""

    projected = dict(runtime)
    memory = runtime.get("canonical_memory")
    if isinstance(memory, dict):
        projected["canonical_memory"] = {
            "ready": bool(memory.get("ready")),
            "revision": memory.get("revision"),
            "record_count": int(memory.get("record_count", 0) or 0),
            "latest_founder_correction_wins": bool(
                memory.get("latest_founder_correction_wins")
            ),
            "human_authority_final": bool(memory.get("human_authority_final")),
        }
    return projected


def get_public_ollama_chat() -> dict[str, Any]:
    """Return non-sensitive readiness without contacting inference or writing HRM."""

    runtime = health()
    public_runtime = _public_runtime(runtime)
    loopback_only = _loopback_endpoint()
    model = re.sub(r"[^a-zA-Z0-9._:-]", "", DEFAULT_MODEL)[:80]
    return {
        "title": "Personal SMI",
        "panel_name": "OAP Mind",
        "provider": {
            "id": PROVIDER_ID,
            "name": PROVIDER_NAME,
            "model": __import__("os").environ.get("OAP_AI_MODEL", model),
            "scope": "Replaceable governed inference plumbing",
            "connected": runtime["checks"]["provider_key"],
            "status": "Connected" if runtime["checks"]["provider_key"] else "Not connected",
            "authority": False,
            "agent": False,
            "identity": False,
        },
        "thinking_process": smi_thinking_process.process_contract(),
        "pathway": CHAT_PATHWAY,
        "conversation": (),
        "readiness": {
            "local_mode": config.OAP_LOCAL_MODE,
            "local_fallback_loopback": loopback_only,
            "identity_connected": runtime["checks"]["identity"],
            "permission_granted": runtime["checks"]["permission"],
            "provider_assignment_approved": runtime["checks"]["router"],
            "hrm_initialized": runtime["checks"]["hrm"],
            "thinking_process_ready": runtime["thinking_process"]["passed"],
            "composer_enabled": runtime["status"] == "green",
        },
        "allowed_output": "RECOMMENDATION_READY",
        "execution": "Recommendation only",
        "runtime": public_runtime,
        "activation_gate": (
            "Identity, REQUEST_RECOMMENDATION permission, an approved inference route "
            "and HRM initialization are required before chat can send."
        ),
        "human_authority": {
            "status": "Final approval required",
            "message": "Personal SMI advises only and cannot approve or execute consequential actions.",
        },
    }
