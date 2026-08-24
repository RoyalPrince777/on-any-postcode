"""Read-only OAP Dashboard Chat projection for the local Ollama provider."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from . import config
from .smi_chat_runtime import health
from .database import db_status

PROVIDER_ID = "ollama"
PROVIDER_NAME = "Ollama Local"
DEFAULT_MODEL = "qwen2.5:1.5b"
GENERATE_PATH = "/api/generate"

CHAT_PATHWAY = (
    {"step": "OAP Dashboard Chat", "responsibility": "Receives bounded human text"},
    {"step": "Identity", "responsibility": "Validates the human requester"},
    {"step": "Living Kernel", "responsibility": "Checks permission and safety gates"},
    {"step": "SMI Mind", "responsibility": "Forms an advisory prompt"},
    {"step": "Ollama Local", "responsibility": "Generates provider text only"},
    {"step": "Guardian", "responsibility": "Reviews the proposed response"},
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


def get_public_ollama_chat() -> dict[str, Any]:
    """Return non-sensitive readiness without contacting Ollama or writing HRM."""

    database = db_status()
    runtime = health()
    loopback_only = _loopback_endpoint()
    model = re.sub(r"[^a-zA-Z0-9._:-]", "", DEFAULT_MODEL)[:80]
    return {
        "title": "OAP Dashboard Chat",
        "panel_name": "OAP Mind Assistant Panel",
        "provider": {
            "id": PROVIDER_ID,
            "name": "OpenAI Cloud / Ollama Local",
            "model": __import__("os").environ.get("OAP_AI_MODEL", model),
            "scope": "Hybrid governed provider",
            "connected": runtime["checks"]["provider_key"],
            "status": "Connected" if runtime["checks"]["provider_key"] else "Not connected",
            "authority": False,
            "agent": False,
        },
        "pathway": CHAT_PATHWAY,
        "conversation": (),
        "readiness": {
            "local_mode": config.OAP_LOCAL_MODE,
            "loopback_endpoint": loopback_only,
            "identity_connected": runtime["checks"]["identity"],
            "permission_granted": runtime["checks"]["permission"],
            "provider_assignment_approved": runtime["checks"]["router"],
            "hrm_initialized": runtime["checks"]["hrm"],
            "composer_enabled": runtime["status"] == "green",
        },
        "allowed_output": "RECOMMENDATION_READY",
        "execution": "Recommendation only",
        "runtime": runtime,
        "activation_gate": (
            "Identity, REQUEST_RECOMMENDATION permission, an approved Ollama "
            "assignment and HRM initialization are required before chat can send."
        ),
        "human_authority": {
            "status": "Final approval required",
            "message": "Ollama advises only and cannot approve or execute actions.",
        },
    }
