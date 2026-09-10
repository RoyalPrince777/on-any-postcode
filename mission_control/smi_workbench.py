"""Secret-safe Founder workbench projection for Personal SMI."""

from __future__ import annotations

import os
from typing import Any

from . import smi_chat_runtime, studio_intelligence


def _configured(*names: str) -> bool:
    return any(bool(os.environ.get(name, "").strip()) for name in names)


def get_workbench_status() -> dict[str, Any]:
    """Report readiness and private inspection routes without returning credentials."""
    runtime = smi_chat_runtime.health()
    checks = runtime.get("checks", {})
    database_ready = bool(checks.get("database") and checks.get("schema"))
    render_configured = _configured("OAP_RENDER_API_KEY", "RENDER_API_KEY")
    github_configured = _configured("OAP_GITHUB_TOKEN")
    neon_database_configured = _configured(
        "OAP_NEON_DATABASE_URL",
        "DATABASE_URL",
        "OAP_NEON_DATABASE_URL_B64",
        "OAP_DB_SECRET_B64",
    )
    neon_management_configured = _configured("OAP_NEON_API_KEY", "NEON_API_KEY")
    neon_configured = bool(neon_database_configured or neon_management_configured)
    runtime_gate = {
        "state": "green" if database_ready else "yellow",
        "title": "Durable runtime ready" if database_ready else "Durable runtime unavailable",
        "summary": (
            "Managed identity, conversation memory, HRM receipts and durable writes are available."
            if database_ready
            else "Managed identity, conversation memory, HRM receipts and durable writes remain blocked; read-only Founder inspection stays separate."
        ),
        "blocked": []
        if database_ready
        else [
            "managed Founder identity",
            "conversation + HRM persistence",
            "signed approval receipts",
            "durable My World, Link and Market writes",
        ],
        "available": [
            "SMI gateway process health",
            "Founder read-only provider inspection",
            "War Room status and evidence surfaces",
            "OAP Studio Intelligence planning and preparation",
        ],
        "fail_closed": not database_ready,
    }
    studio = studio_intelligence.status()
    return {
        "status": "ready" if runtime.get("status") == "green" else "attention",
        "surface": "Founder-only Personal SMI",
        "runtime_gate": runtime_gate,
        "connectors": [
            {
                "id": "render",
                "name": "Render",
                "configured": render_configured,
                "ready": render_configured,
                "inspect_url": "/mission/tools/render/services",
                "mode": "read-only inspection; deploy actions are not exposed here",
                "purpose": "service health, deploy state and release evidence",
            },
            {
                "id": "github",
                "name": "GitHub",
                "configured": github_configured,
                "ready": github_configured,
                "inspect_url": "/mission/tools/github/repository",
                "mode": "read inspection; writes remain proposal + approval + Kernel governed",
                "purpose": "repository state, code evidence and governed proposals",
            },
            {
                "id": "neon",
                "name": "Neon · Identity/HRM" if database_ready else "Neon · Identity/HRM blocked",
                "configured": neon_configured,
                "ready": database_ready,
                "inspect_url": "/mission/tools/neon/status",
                "management_api_configured": neon_management_configured,
                "mode": "read-only database readiness; SQL writes and migrations are not exposed here",
                "purpose": "identity, conversations, HRM receipts and operational data",
            },
        ],
        "capabilities": [
            {"id": "chat", "name": "Chat", "ready": bool(checks.get("chat_route"))},
            {"id": "memory", "name": "Memory", "ready": bool(checks.get("conversation_memory"))},
            {"id": "war-room", "name": "War Room", "ready": bool(checks.get("war_room"))},
            {"id": "attachments", "name": "Files + media", "ready": True},
            {"id": "voice", "name": "Voice", "ready": True},
            {"id": "code", "name": "Code proposals", "ready": True},
            studio,
        ],
        "knowledge": {
            "name": "OAP operating context",
            "source": "versioned OAP code, protocols, receipts and Founder corrections",
            "rule": "Latest explicit Founder correction wins; private ChatGPT memory is not imported implicitly.",
        },
        "governance": {
            "recommendation_only": True,
            "human_authority_final": True,
            "secrets_exposed": False,
            "provider_reads_founder_only": True,
            "consequential_actions_require_separate_approval": True,
        },
    }
