"""Secret-safe Founder workbench projection for Personal SMI."""

from __future__ import annotations

import os
from typing import Any

from . import (
    a7_certification,
    coherent_automation,
    distribution_intelligence,
    oap_bank,
    smi_chat_runtime,
    studio_intelligence,
)


def _configured(*names: str) -> bool:
    return any(bool(os.environ.get(name, "").strip()) for name in names)


def _capability(
    capability_id: str,
    name: str,
    ready: bool,
    *,
    evidence: str,
    blocked_reason: str | None = None,
) -> dict[str, Any]:
    """Build a truth-labelled capability; green requires runtime evidence."""
    return {
        "id": capability_id,
        "name": name,
        "ready": bool(ready),
        "state": "green" if ready else "yellow",
        "evidence": evidence,
        "blocked_reason": None if ready else blocked_reason or "Runtime proof is not available.",
    }


def get_workbench_status() -> dict[str, Any]:
    """Report readiness and private inspection routes without returning credentials."""
    runtime = smi_chat_runtime.health()
    checks = runtime.get("checks", {})
    database_ready = bool(checks.get("database") and checks.get("schema"))
    render_configured = _configured("OAP_RENDER_API_KEY", "RENDER_API_KEY")
    github_configured = _configured("OAP_GITHUB_TOKEN")
    postgres_database_configured = _configured(
        "OAP_NEON_DATABASE_URL",
        "DATABASE_URL",
        "OAP_NEON_DATABASE_URL_B64",
        "OAP_DB_SECRET_B64",
    )
    neon_management_configured = _configured("OAP_NEON_API_KEY", "NEON_API_KEY")
    neon_configured = bool(postgres_database_configured or neon_management_configured)

    chat_ready = bool(checks.get("chat_route"))
    memory_ready = bool(checks.get("conversation_memory"))
    war_room_ready = bool(checks.get("war_room"))
    attachment_ready = bool(checks.get("attachments") or checks.get("media"))
    voice_ready = bool(checks.get("voice") or checks.get("speech"))
    code_ready = bool(checks.get("code_mode") or checks.get("code_proposals"))

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
            "OAP Coherent Automation 21-signal planning",
            "OAP Distribution Intelligence release and rights review",
            "SMI A7 certification readiness and governed evidence gate",
            "OAP Bank non-payment orchestration planning",
        ],
        "fail_closed": not database_ready,
    }
    studio = studio_intelligence.status()
    coherence = coherent_automation.status()
    distribution = distribution_intelligence.status()
    bank = oap_bank.status()
    a7 = a7_certification.status()
    a7_missing = tuple(a7.get("a7_missing") or ())
    a6_missing = tuple(a7.get("a6_missing") or ())
    a7_blockers = tuple((*a6_missing, *a7_missing))
    a7_capability = _capability(
        "smi-a7-certification",
        "A7 Certification",
        bool(a7.get("ready_for_founder_certification")),
        evidence="mission_control.a7_certification.status()",
        blocked_reason=(
            "Founder certification proof remains incomplete: " + ", ".join(a7_blockers)
            if a7_blockers
            else "Founder certification has not been granted."
        ),
    )
    a7_capability.update(
        {
            "level": "A7",
            "certification_granted": bool(a7.get("certification_granted")),
            "a7_enabled": bool(a7.get("a7_enabled")),
            "execution_granted": bool(a7.get("execution_granted")),
            "a6_missing": a6_missing,
            "a7_missing": a7_missing,
            "human_authority_final": bool(a7.get("human_authority_final")),
            "fail_closed": True,
        }
    )

    capabilities = [
        _capability(
            "chat",
            "Chat",
            chat_ready,
            evidence="smi_chat_runtime.health().checks.chat_route",
            blocked_reason="The governed chat route has not produced runtime proof.",
        ),
        _capability(
            "memory",
            "Memory",
            memory_ready,
            evidence="smi_chat_runtime.health().checks.conversation_memory",
            blocked_reason="Conversation memory has not produced runtime proof.",
        ),
        _capability(
            "war-room",
            "War Room",
            war_room_ready,
            evidence="smi_chat_runtime.health().checks.war_room",
            blocked_reason="War Room runtime proof is unavailable or advisory-only.",
        ),
        _capability(
            "attachments",
            "Files + media",
            attachment_ready,
            evidence="runtime checks attachments/media",
            blocked_reason="Files/media are present in UI but no runtime certification check is green.",
        ),
        _capability(
            "voice",
            "Voice",
            voice_ready,
            evidence="runtime checks voice/speech",
            blocked_reason="Voice UI may be present, but no runtime voice certification check is green.",
        ),
        _capability(
            "code",
            "Code proposals",
            code_ready,
            evidence="runtime checks code_mode/code_proposals",
            blocked_reason="Code mode may be exposed, but no runtime code-proposal certification check is green.",
        ),
        studio,
        coherence,
        distribution,
        a7_capability,
        bank,
    ]

    proven_core = chat_ready and memory_ready and database_ready
    return {
        "status": "ready" if runtime.get("status") == "green" and proven_core else "attention",
        "surface": "Founder-only Personal SMI",
        "truth_contract": {
            "no_fake_green": True,
            "green_requires_runtime_evidence": True,
            "ui_presence_is_not_readiness": True,
            "configured_is_not_ready": True,
        },
        "runtime_gate": runtime_gate,
        "connectors": [
            {
                "id": "render",
                "name": "Render",
                "configured": render_configured,
                "ready": False,
                "inspect_url": "/mission/tools/render/services",
                "mode": "read-only inspection; deploy actions are not exposed here",
                "purpose": "service health, deploy state and release evidence",
                "readiness_reason": "Configuration alone is not treated as live proof; use the inspection route for current provider evidence.",
            },
            {
                "id": "github",
                "name": "GitHub",
                "configured": github_configured,
                "ready": False,
                "inspect_url": "/mission/tools/github/repository",
                "mode": "read inspection; writes remain proposal + approval + Kernel governed",
                "purpose": "repository state, code evidence and governed proposals",
                "readiness_reason": "Configuration alone is not treated as live proof; use the inspection route for current repository evidence.",
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
                "readiness_reason": "Green only when the database and required schema both pass runtime checks.",
            },
        ],
        "capabilities": capabilities,
        "a7": {
            "level": "A7",
            "ready_for_founder_certification": bool(a7.get("ready_for_founder_certification")),
            "certification_granted": bool(a7.get("certification_granted")),
            "a7_enabled": bool(a7.get("a7_enabled")),
            "execution_granted": bool(a7.get("execution_granted")),
            "a6_missing": a6_missing,
            "a7_missing": a7_missing,
            "human_authority_final": bool(a7.get("human_authority_final")),
            "external_evidence_is_software_verified": bool(a7.get("external_evidence_is_software_verified")),
            "fail_closed": True,
        },
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
