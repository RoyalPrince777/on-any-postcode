"""Secret-safe Founder workbench projection for Personal SMI."""

from __future__ import annotations

import os
from typing import Any

from . import smi_chat_runtime


def _configured(*names: str) -> bool:
    return any(bool(os.environ.get(name, "").strip()) for name in names)


def get_workbench_status() -> dict[str, Any]:
    """Report readiness without returning credentials or account identifiers."""
    runtime = smi_chat_runtime.health()
    checks = runtime.get("checks", {})
    database_ready = bool(checks.get("database") and checks.get("schema"))
    return {
        "status": "ready" if runtime.get("status") == "green" else "attention",
        "surface": "Founder-only Personal SMI",
        "connectors": [
            {"id": "render", "name": "Render", "configured": _configured("OAP_RENDER_API_KEY", "RENDER_API_KEY"), "mode": "read-only until explicit Human Authority approval", "purpose": "service health, deploy state, logs and release evidence"},
            {"id": "github", "name": "GitHub", "configured": _configured("OAP_GITHUB_TOKEN"), "mode": "proposal-first; writes remain separately governed", "purpose": "repository status, code proposals and release evidence"},
            {"id": "neon", "name": "Neon", "configured": _configured("OAP_NEON_DATABASE_URL", "DATABASE_URL", "OAP_NEON_DATABASE_URL_B64", "OAP_DB_SECRET_B64"), "ready": database_ready, "mode": "private data and governed memory", "purpose": "identity, conversations, HRM receipts and operational data"},
        ],
        "capabilities": [
            {"id": "chat", "name": "Chat", "ready": bool(checks.get("chat_route"))},
            {"id": "memory", "name": "Memory", "ready": bool(checks.get("conversation_memory"))},
            {"id": "war-room", "name": "War Room", "ready": bool(checks.get("war_room"))},
            {"id": "attachments", "name": "Files + media", "ready": True},
            {"id": "voice", "name": "Voice", "ready": True},
            {"id": "code", "name": "Code proposals", "ready": True},
        ],
        "knowledge": {"name": "OAP operating context", "source": "versioned OAP code, protocols, receipts and Founder corrections", "rule": "Latest explicit Founder correction wins; private ChatGPT memory is not imported implicitly."},
        "governance": {"recommendation_only": True, "human_authority_final": True, "secrets_exposed": False, "consequential_actions_require_separate_approval": True},
    }
