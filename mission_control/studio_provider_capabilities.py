"""Founder-private, read-only SMI Studio provider capability catalogue.

This extends the ONE canonical OAP Studio. Models are documented possibilities,
not connected providers. No credentials, prompts, media, paid calls or execution
authority flow through this module. Provider integrations require separate,
audited adapters and independent Guardian/HRM + Founder Final approval.
"""
from __future__ import annotations

from typing import Any, Mapping

# Model families rather than unstable provider-specific API IDs.
# The source links identify the legitimate provider documentation.
_PROVIDERS = (
    {
        "id": "oap-image",
        "name": "OAP Image",
        "maker": "Existing OAP Studio adapter",
        "kind": "image",
        "tasks": ("image", "edit"),
        "transport": "external",
        "integration": "existing_adapter",
        "docs": "/mission/ollama",
        "note": "Existing OpenAI image adapter; key presence is not runtime or artefact proof.",
    },
    {
        "id": "oap-video",
        "name": "OAP Video",
        "maker": "Existing OAP Studio adapter",
        "kind": "video",
        "tasks": ("video", "animate"),
        "transport": "external",
        "integration": "existing_adapter",
        "docs": "/mission/ollama",
        "note": "Existing asynchronous video adapter; completed verified MP4 still required.",
    },
    {
        "id": "nano-banana",
        "name": "Nano Banana",
        "maker": "Google Gemini",
        "kind": "image",
        "tasks": ("image", "edit"),
        "transport": "external",
        "integration": "research_only",
        "docs": "https://ai.google.dev/gemini-api/docs/image-generation",
        "note": "Model/version/API permissions and pricing require a fresh official check.",
    },
    {
        "id": "seedance",
        "name": "Seedance",
        "maker": "ByteDance",
        "kind": "video",
        "tasks": ("video", "animate"),
        "transport": "external",
        "integration": "research_only",
        "docs": "https://seed.bytedance.com/en/seedance-enterprise/api",
        "note": "Video and multimodal reference capabilities vary by version and gateway.",
    },
    {
        "id": "higgsfield",
        "name": "Higgsfield",
        "maker": "Higgsfield AI",
        "kind": "video",
        "tasks": ("video", "animate"),
        "transport": "external",
        "integration": "research_only",
        "docs": "https://open.higgsfield.ai/quick-start",
        "note": "Model catalogue and credits are external; never assume credits are available.",
    },
    {
        "id": "elevenlabs",
        "name": "ElevenLabs",
        "maker": "ElevenLabs",
        "kind": "voice",
        "tasks": ("voice", "dub"),
        "transport": "external",
        "integration": "research_only",
        "docs": "https://elevenlabs.io/docs/overview/intro",
        "note": "Voice rights, consent, provider terms and audio-retention review required.",
    },
    {
        "id": "voicestudio",
        "name": "VoiceStudio",
        "maker": "Open-source voice workspace",
        "kind": "voice",
        "tasks": ("voice", "dub"),
        "transport": "local_optional",
        "integration": "research_only",
        "docs": "https://github.com/debpalash/VoiceStudio",
        "note": "Local models, licences and Android compatibility unverified on Redmi A5.",
    },
    {
        "id": "oap-local",
        "name": "OAP Local Compositor",
        "maker": "OAP Studio FFmpeg tooling",
        "kind": "editing",
        "tasks": ("edit", "composite"),
        "transport": "local",
        "integration": "existing_tooling",
        "docs": "/mission/ollama",
        "note": "Existing source code is not evidence that the device renderer is installed.",
    },
)
_BY_ID = {item["id"]: item for item in _PROVIDERS}
_ALLOWED_FIELDS = frozenset({
    "model_id", "task", "aspect_ratio", "duration_seconds",
    "owner_rights_confirmed", "subject_consent_confirmed", "remote_approved",
})
_ASPECTS = frozenset({"16:9", "9:16", "1:1"})


def status(existing_backend: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Secret-free provider discovery; never claim runtime Green."""
    configured = bool((existing_backend or {}).get("configured"))
    entries = []
    for item in _PROVIDERS:
        entry = dict(item)
        entry["tasks"] = list(item["tasks"])
        entry["adapter_configured"] = configured if item["integration"] == "existing_adapter" else False
        entry["runtime_verified"] = False
        entry["artifacts_verified"] = False
        entry["state"] = (
            "configured_unverified" if entry["adapter_configured"]
            else "code_only" if item["integration"] in ("existing_adapter", "existing_tooling")
            else "research_only"
        )
        entry["execution_granted"] = False
        entries.append(entry)
    return {
        "studio": "oap-studio-intelligence",
        "provider_catalogue": entries,
        "total": len(entries),
        "one_canonical_studio": True,
        "external_calls_enabled_by_catalogue": False,
        "privacy": "first_party_default",
        "guardian_hrm_verified": False,
        "founder_final_required": True,
        "note": "Readiness and models are informational, never an install, paid render or connection.",
    }


def preflight(payload: object, existing_backend: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate a selection without executing, storing, charging or uploading."""
    if not isinstance(payload, dict):
        raise ValueError("studio_provider_selection_object_required")
    if set(payload).difference(_ALLOWED_FIELDS):
        raise ValueError("studio_provider_unexpected_fields")
    model_id = payload.get("model_id")
    task = payload.get("task")
    aspect = payload.get("aspect_ratio", "16:9")
    seconds = payload.get("duration_seconds", 5)
    if not isinstance(model_id, str) or model_id not in _BY_ID:
        raise ValueError("studio_provider_unknown")
    if not isinstance(task, str) or task not in _BY_ID[model_id]["tasks"]:
        raise ValueError("studio_task_unsupported_for_provider")
    if not isinstance(aspect, str) or aspect not in _ASPECTS:
        raise ValueError("studio_aspect_ratio_invalid")
    if isinstance(seconds, bool) or not isinstance(seconds, int) or not 1 <= seconds <= 30:
        raise ValueError("studio_duration_out_of_policy")
    flags = ("owner_rights_confirmed", "subject_consent_confirmed", "remote_approved")
    if any(type(payload.get(name, False)) is not bool for name in flags):
        raise ValueError("studio_approval_flags_must_be_boolean")

    provider = _BY_ID[model_id]
    missing = ["guardian_hrm_independent_proof", "founder_final_runtime_approval",
               "verified_runtime_and_artifact"]
    if provider["transport"] == "external":
        missing.extend(["privacy_and_data_processing_review", "itemised_cost_quote",
                        "provider_endpoint_and_model_id_verification"])
        if not payload.get("remote_approved"):
            missing.append("external_transfer_not_approved")
    elif provider["transport"] == "local_optional":
        missing.extend(["local_model_licence_review", "on_device_runtime_proof"])
    else:
        missing.append("local_render_device_proof")
    if task in ("animate", "edit", "dub", "composite"):
        if not payload.get("owner_rights_confirmed"):
            missing.append("reference_ownership_not_confirmed")
        if not payload.get("subject_consent_confirmed"):
            missing.append("subject_consent_not_confirmed")
    return {
        "studio": "oap-studio-intelligence",
        "model_id": model_id,
        "task": task,
        "aspect_ratio": aspect,
        "duration_seconds": seconds,
        "state": "blocked_pending_evidence",
        "missing_evidence": missing,
        "adapter_configured": bool((existing_backend or {}).get("configured"))
        if provider["integration"] == "existing_adapter" else False,
        "execution_granted": False,
        "payment_authorised": False,
        "upload_performed": False,
        "provider_called": False,
        "output_generated": False,
        "founder_final_required": True,
        "next_route": "/mission/ollama",
    }
