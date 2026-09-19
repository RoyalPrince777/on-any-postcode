"""Canonical Founder-facing OAP Studio Intelligence contract.

Studio is the private creation and media-intelligence workspace powered by SMI.
SMI Chat may capture media and route it here; it must not duplicate Studio's media
reasoning, creation, editing or packaging engine. Studio does not expand execution,
publishing, rights, payment or distribution authority. Human Authority remains
final and external delivery stays locked until its existing proof gates pass.
The public Spot does not expose this Founder-only surface.
"""

from __future__ import annotations

from typing import Any

from . import smi_receipt_backend, studio_media_backend

STUDIO_ID = "oap-studio-intelligence"
STUDIO_NAME = "OAP Studio Intelligence"
PIPELINE = (
    "Create",
    "Edit",
    "Package",
    "Rights",
    "Publish",
    "Distribute",
    "Campaign",
    "Analyse",
)
MEDIA = (
    "image",
    "audio",
    "video",
    "documents",
    "music",
    "campaigns",
    "creator products",
)
CAPTURE_INPUTS = (
    "camera still",
    "screen still",
    "image attachment",
    "audio attachment",
    "video attachment",
    "document attachment",
)
ENTRY_POINTS = (
    "SMI Chat",
    "OAP Studio Intelligence",
)
DESTINATIONS = (
    "OAP Music",
    "OAP Player",
    "OAP Radio",
    "OAP TV & Media",
    "OAP Records",
    "OAP Distribution",
    "My Shop",
    "The Spot",
)
GENERATION_TOOLS = (
    {
        "id": "imagine",
        "name": "Imagine",
        "input": "text",
        "output": "image",
        "purpose": "Create a new visual from a written idea.",
    },
    {
        "id": "bring_alive",
        "name": "Bring Alive",
        "input": "image",
        "output": "video",
        "purpose": "Prepare motion, camera, expression and atmosphere from a source image.",
    },
    {
        "id": "scene_builder",
        "name": "Scene Builder",
        "input": "text",
        "output": "video",
        "purpose": "Prepare a short video scene directly from a written brief.",
    },
)

STUDIO_21_STAGES = (
    "Intent", "Input", "Rights", "Safety", "Context", "Route", "Evidence",
    "Creative brief", "Style", "Composition", "Motion", "Audio", "Continuity",
    "Quality", "Guardian", "Green Gate", "Chronicle", "HRM", "Output check",
    "Founder review", "Lock result",
)

ACTIVATION_PROMPT = (
    "OAP Studio Intelligence mode. Help me create, edit, package, check rights, "
    "prepare publishing, distribution, campaign and analysis for: "
)


def _tool(tool_id: str) -> dict[str, str]:
    clean = str(tool_id or "").strip().lower()
    for tool in GENERATION_TOOLS:
        if tool["id"] == clean:
            return dict(tool)
    raise ValueError("unsupported_studio_tool")


def prepare_generation(tool_id: str, *, prompt: object = "", source_ref: object = "") -> dict[str, Any]:
    """Prepare one governed Studio generation job and record its bounded proof receipt.

    This function deliberately does not claim generated media. A provider/renderer must
    return an artifact before output_generated can become true.
    """

    tool = _tool(tool_id)
    clean_prompt = str(prompt or "").strip()[:4000]
    clean_source = str(source_ref or "").strip()[:500]
    if tool["input"] == "text" and not clean_prompt:
        raise ValueError("studio_prompt_required")
    if tool["input"] == "image" and not clean_source:
        raise ValueError("studio_source_image_required")

    receipt = smi_receipt_backend.write_receipt(
        "studio_generation_receipt",
        {
            "brain_part": "studio_intelligence",
            "gate": 21,
            "command": tool["id"],
            "signal": "🟣",
            "guardian": "required",
            "green_gate": "blocked_until_artifact_proof",
            "founder_final": "required_for_full_green",
            "safe_payload": {
                "tool_id": tool["id"],
                "input_kind": tool["input"],
                "output_kind": tool["output"],
                "prompt_present": bool(clean_prompt),
                "source_ref_present": bool(clean_source),
                "stage_count": len(STUDIO_21_STAGES),
                "output_generated": False,
                "execution_authority_expanded": False,
            },
        },
    )
    return {
        "studio": STUDIO_NAME,
        "tool": tool,
        "smi_depth": 21,
        "stages": list(STUDIO_21_STAGES),
        "state": "prepared",
        "output_generated": False,
        "artifact": None,
        "next_gate": "media_generation_backend",
        "chronicle_receipt": receipt,
        "execution_granted": False,
        "publishing_granted": False,
        "distribution_granted": False,
        "human_authority_final": True,
    }


def execute_generation(
    tool_id: str,
    *,
    prompt: object = "",
    source_image_data: object = "",
) -> dict[str, Any]:
    """Execute one supported provider-backed Studio generation request.

    Image generation may return a complete artifact immediately. Video generation
    returns a governed job and remains purple until the provider reports completed.
    """

    tool = _tool(tool_id)
    clean_prompt = str(prompt or "").strip()
    if tool["id"] == "imagine":
        artifact = studio_media_backend.generate_image(clean_prompt)
    elif tool["id"] in {"scene_builder", "bring_alive"}:
        source_data = str(source_image_data or "").strip()
        if tool["id"] == "bring_alive" and not source_data:
            raise ValueError("studio_source_image_data_required")
        artifact = studio_media_backend.create_video(
            clean_prompt,
            source_image_data=source_data,
        )
    else:  # pragma: no cover - guarded by _tool
        raise ValueError("unsupported_studio_tool")

    artifact_proven = bool(artifact.get("artifact_proven"))
    receipt = smi_receipt_backend.write_receipt(
        "studio_generation_receipt",
        {
            "brain_part": "studio_intelligence",
            "gate": 21,
            "command": tool["id"],
            "signal": "🟢" if artifact_proven else "🟣",
            "guardian": "required",
            "green_gate": "artifact_proven" if artifact_proven else "awaiting_artifact_proof",
            "founder_final": "required_for_full_green",
            "safe_payload": {
                "tool_id": tool["id"],
                "output_kind": tool["output"],
                "provider": "openai",
                "model": str(artifact.get("model") or ""),
                "artifact_proven": artifact_proven,
                "video_job_id_present": bool(artifact.get("id")),
                "execution_authority_expanded": False,
            },
        },
    )
    return {
        "studio": STUDIO_NAME,
        "tool": tool,
        "smi_depth": 21,
        "state": "generated" if artifact_proven else "provider_job_started",
        "output_generated": artifact_proven,
        "artifact": artifact,
        "chronicle_receipt": receipt,
        "execution_granted": False,
        "publishing_granted": False,
        "distribution_granted": False,
        "human_authority_final": True,
    }


def generation_status(video_id: object) -> dict[str, Any]:
    """Check one Studio video job and Chronicle its current proof state."""

    artifact = studio_media_backend.video_status(str(video_id or ""))
    artifact_proven = bool(artifact.get("artifact_proven"))
    receipt = smi_receipt_backend.write_receipt(
        "studio_generation_receipt",
        {
            "brain_part": "studio_intelligence",
            "gate": 21,
            "command": "video_status",
            "signal": "🟢" if artifact_proven else "🟣",
            "guardian": "required",
            "green_gate": "artifact_proven" if artifact_proven else "awaiting_artifact_proof",
            "founder_final": "required_for_full_green",
            "safe_payload": {
                "video_job_id_present": bool(artifact.get("id")),
                "status": str(artifact.get("status") or ""),
                "progress": int(artifact.get("progress") or 0),
                "artifact_proven": artifact_proven,
                "execution_authority_expanded": False,
            },
        },
    )
    return {
        "studio": STUDIO_NAME,
        "smi_depth": 21,
        "state": "generated" if artifact_proven else "provider_job_active",
        "output_generated": artifact_proven,
        "artifact": artifact,
        "chronicle_receipt": receipt,
        "execution_granted": False,
        "publishing_granted": False,
        "distribution_granted": False,
        "human_authority_final": True,
    }



def generation_content(video_id: object) -> dict[str, Any]:
    """Return completed video bytes only after the provider completion proof gate."""

    status_result = generation_status(video_id)
    if not status_result["output_generated"]:
        raise RuntimeError("studio_generation_artifact_not_ready")
    artifact = studio_media_backend.video_content(str(video_id or ""))
    if not artifact.get("artifact_proven"):
        raise RuntimeError("studio_generation_artifact_missing")
    return artifact


def status() -> dict[str, Any]:
    """Return the secret-free Studio contract for the Founder workbench."""

    return {
        "id": STUDIO_ID,
        "name": STUDIO_NAME,
        "ready": True,
        "powered_by": "SMI",
        "pipeline": list(PIPELINE),
        "generation_tools": [dict(tool) for tool in GENERATION_TOOLS],
        "studio_21_stage_count": len(STUDIO_21_STAGES),
        "studio_21_stages": list(STUDIO_21_STAGES),
        "generation_backend": studio_media_backend.status(),
        "generation_backend_configured": bool(studio_media_backend.status()["configured"]),
        "generation_runtime_proven": False,
        "generation_backend_proven": bool(studio_media_backend.status()["configured"]),
        "full_live_certificate": False,
        "media": list(MEDIA),
        "capture_inputs": list(CAPTURE_INPUTS),
        "entry_points": list(ENTRY_POINTS),
        "destinations": list(DESTINATIONS),
        "activation_prompt": ACTIVATION_PROMPT,
        "mode": "Founder creation workspace; recommendation and preparation only",
        "purpose": (
            "Canonical OAP media intelligence for creating, analysing and preparing OAP-owned "
            "media, releases, campaigns and creator products before governed publishing or distribution."
        ),
        "alignment": {
            "smi_chat_is_entry_surface": True,
            "studio_is_canonical_media_engine": True,
            "duplicate_studio_engine_allowed": False,
            "capture_does_not_grant_execution": True,
        },
        "governance": {
            "human_authority_final": True,
            "rights_proof_required": True,
            "external_distribution_locked_until_proof": True,
            "payment_authority_granted": False,
            "publishing_authority_granted": False,
            "execution_authority_granted": False,
        },
    }
