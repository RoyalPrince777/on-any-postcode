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

from oap.smi import capability_fabric

from . import postgres_db, smi_founder_assets, smi_receipt_backend, studio_media_backend

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


STUDIO_WORKSPACES = (
    {"id":"build","name":"Build","icon":"🏗️","purpose":"Build apps, sites, dashboards and product surfaces through governed code proposals, tests, preview preparation and GitHub handoff.","thinking_level":"deep_dive","code_mode":True,"studio_mode":True,"capabilities":("agentic_code_review","artifact_workflows","workspace_isolation","long_horizon_delivery")},
    {"id":"data","name":"Data","icon":"🗄️","purpose":"Inspect, model and explain owner-authorised OAP Data and database state through read-only first-party inspection unless Human Authority explicitly approves a governed write.","thinking_level":"think","code_mode":False,"studio_mode":True,"capabilities":("structured_output","long_context_synthesis","evidence_first")},
    {"id":"code","name":"Code","icon":"⌘","purpose":"Plan, write, review, debug and test code with exact diffs, rollback awareness and evidence before completion claims.","thinking_level":"deep_dive","code_mode":True,"studio_mode":True,"capabilities":("agentic_code_review","gap_adversarial_review","workspace_isolation")},
    {"id":"fast","name":"Fast","icon":"⚡","purpose":"Use the smallest sufficient path for rapid answers, transformations and bounded tool routing without lowering safety or truth standards.","thinking_level":"instant","code_mode":False,"studio_mode":True,"capabilities":("cost_aware_routing","context_tiering")},
    {"id":"motion","name":"Motion","icon":"🎞️","purpose":"Create and reason about image-to-video, text-to-video, scene continuity, camera movement, timing and governed video artifacts.","thinking_level":"think","code_mode":False,"studio_mode":True,"capabilities":("multimodal_spatial_reasoning","realtime_audio_visual","artifact_workflows")},
    {"id":"music","name":"Music","icon":"🎵","purpose":"Develop original music concepts, structure, arrangement, rights-safe release preparation and OAP Music handoff; audio synthesis remains separately evidence-gated.","thinking_level":"think","code_mode":False,"studio_mode":True,"capabilities":("multimodal_fusion","creation_communication","artifact_workflows")},
    {"id":"omni","name":"Omni","icon":"◎","purpose":"Combine text, images, audio, video, files, camera and screen evidence in one governed multimodal workspace.","thinking_level":"auto","code_mode":False,"studio_mode":True,"capabilities":("multimodal_fusion","multimodal_spatial_reasoning","realtime_audio_visual")},
    {"id":"research","name":"Research","icon":"🔎","purpose":"Run evidence-first deep research with source provenance, parallel retrieval, comparison and compact synthesis.","thinking_level":"deep_dive","code_mode":False,"studio_mode":True,"capabilities":("cited_live_research","parallel_retrieval","multi_expert_synthesis")},
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




_WORKSPACE_TERMS = (
    ("build", ("build","app","website","dashboard","preview","deploy candidate")),
    ("data", ("database","schema","table","query","sql","migration","data model")),
    ("code", ("code","debug","bug","refactor","test","pull request","commit")),
    ("motion", ("video","motion","animate","scene","camera","bring alive")),
    ("music", ("music","song","beat","lyrics","mix","master","stems","album")),
    ("research", ("research","sources","compare","evidence","deep dive","report")),
    ("omni", ("screen","camera","image","audio","video","document","multimodal")),
    ("fast", ("quick","fast","short","rewrite","summarise","summarize")),
)


def select_workspace(query: object) -> dict[str, Any]:
    text = str(query or "").casefold()
    scored: list[tuple[int, int, str]] = []
    for index, (workspace_id, terms) in enumerate(_WORKSPACE_TERMS):
        score = sum(term in text for term in terms)
        if score:
            scored.append((score, -index, workspace_id))
    if not scored:
        return workspace("auto")
    scored.sort(reverse=True)
    return workspace(scored[0][2])


def workspace_preflight(workspace_id: object) -> dict[str, Any]:
    item = workspace(workspace_id)
    if item["id"] == "auto":
        return {"workspace":item,"state":"ready","signal":"green","action":"auto_route","message":"SMI will select the smallest sufficient workspace from the request.","execution_granted":False,"human_authority_final":True}
    backend = studio_media_backend.status()
    asset_store = smi_founder_assets.schema_status()
    receipt_state = smi_receipt_backend.backend_configuration_status()
    db_state = postgres_db.postgres_status()
    fabric = capability_fabric.status()
    common = {
        "workspace": item,
        "execution_granted": False,
        "publishing_granted": False,
        "distribution_granted": False,
        "payment_authority_granted": False,
        "human_authority_final": True,
        "stop_available": True,
        "privacy_fail_closed": True,
        "provider_neutral_capability_fabric": bool(fabric.get("provider_neutral")),
        "durable_receipt_backend_configured": bool(receipt_state.get("durable_backend_configured")),
        "owner_asset_store_ready": bool(asset_store.get("schema_ready")),
    }
    if item["id"]=="build":
        return {**common,"state":"ready","signal":"green","action":"governed_build","message":"Build is ready for proposals, tests, exact diffs, rollback-aware GitHub handoff and preview preparation. Production mutation remains receipt-gated.","live_preview_loop":"candidate_preview_then_human_review"}
    if item["id"]=="data":
        ready=bool(db_state.get("initialized"))
        return {**common,"state":"ready" if ready else "blocked","signal":"green" if ready else "red","action":"read_only_data_builder","message":"Data can inspect schema/state and prepare migration/query plans. Writes remain locked behind explicit Human Authority.","database_initialized":ready,"write_performed":False,"migration_preview_supported":True}
    if item["id"]=="code":
        return {**common,"state":"ready","signal":"green","action":"governed_code","message":"Code is ready for plan, edit, debug, test, review and rollback-aware proposal work. Deploy remains separately governed."}
    if item["id"]=="fast":
        return {**common,"state":"ready","signal":"green","action":"instant_route","message":"Fast uses the smallest sufficient reasoning path without bypassing Guardian, STOP, receipts or truth checks."}
    if item["id"]=="motion":
        ready=bool(backend.get("configured") and backend.get("scene_builder_ready") and backend.get("bring_alive_ready"))
        return {**common,"state":"ready" if ready else "locked","signal":"green" if ready else "yellow","action":"motion_generation","message":"Motion uses the Studio image/video backend when configured; artifact proof remains required before Green.","generation_backend_configured":bool(backend.get("configured")),"artifact_proof_required":True}
    if item["id"]=="music":
        return {**common,"state":"ready","signal":"yellow","action":"music_creation_intelligence","message":"Music is ready for original concepts, lyrics, arrangement, release preparation and OAP Music handoff. Direct audio synthesis stays locked until independently proven.","audio_generation_proven":False,"rights_proof_required":True}
    if item["id"]=="omni":
        return {**common,"state":"ready","signal":"green","action":"multimodal_workspace","message":"Omni accepts governed text, image, audio, video, document, camera and screen context through existing SMI capture boundaries."}
    if item["id"]=="research":
        return {**common,"state":"ready","signal":"green","action":"evidence_research","message":"Research uses evidence-first, parallel retrieval and synthesis capabilities with provenance and Human Authority boundaries."}
    raise ValueError("unsupported_studio_workspace")


def threat_posture() -> dict[str, Any]:
    backend=studio_media_backend.status()
    assets=smi_founder_assets.schema_status()
    receipts=smi_receipt_backend.backend_configuration_status()
    return {
        "component":"OAP Studio Threat Posture",
        "feature_sprawl_control":"one_studio_eight_modes",
        "provider_dependency_visible":True,
        "media_backend_configured":bool(backend.get("configured")),
        "provider_outage_fails_closed":True,
        "rights_proof_required":True,
        "raw_generated_media_retained_in_index":False,
        "owner_scoped_asset_index_ready":bool(assets.get("schema_ready")),
        "durable_receipts_configured":bool(receipts.get("durable_backend_configured")),
        "silent_database_write_allowed":False,
        "silent_publish_allowed":False,
        "silent_distribution_allowed":False,
        "silent_payment_allowed":False,
        "mobile_contextual_workspace_required":True,
        "external_named_agent_authority":False,
        "human_authority_final":True,
    }


def workspace(workspace_id: object = "auto") -> dict[str, Any]:
    clean = str(workspace_id or "auto").strip().lower()
    if clean in {"", "auto"}:
        return {"id":"auto","name":"Auto","icon":"🧠","purpose":"Let SMI choose the smallest sufficient Studio workspace from the request.","thinking_level":"auto","code_mode":False,"studio_mode":True,"capabilities":()}
    for item in STUDIO_WORKSPACES:
        if item["id"] == clean:
            return dict(item)
    raise ValueError("unsupported_studio_workspace")


def workspace_instruction(workspace_id: object = "auto") -> str:
    item = workspace(workspace_id)
    if item["id"] == "auto":
        return " STUDIO WORKSPACE: Auto-select the smallest sufficient OAP-native workspace for this request."
    caps = ", ".join(item.get("capabilities") or ())
    return (
        f" STUDIO WORKSPACE {item['name'].upper()}: {item['purpose']} "
        f"Prefer these OAP capability-fabric paths when relevant: {caps or 'adaptive_reasoning'}. "
        "Do not copy another provider's branding, UI identity, hidden prompts, proprietary architecture or model weights."
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


def generation_content(video_id: object) -> tuple[bytes, str]:
    """Return one completed video artifact without expanding publishing authority."""

    clean_id = str(video_id or "").strip()
    status_payload = studio_media_backend.video_status(clean_id)
    if not status_payload.get("artifact_proven"):
        raise RuntimeError("studio_video_not_completed")
    return studio_media_backend.video_content(clean_id)


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


def status() -> dict[str, Any]:
    """Return the secret-free Studio contract for the Founder workbench."""

    backend = studio_media_backend.status()
    asset_store = smi_founder_assets.schema_status()
    receipt_config = smi_receipt_backend.backend_configuration_status()
    machine_dependencies_configured = bool(
        backend.get("configured")
        and asset_store.get("schema_ready")
        and receipt_config.get("durable_backend_configured")
    )
    generated_artifact_proven = bool(asset_store.get("studio_generated_asset_count", 0))
    full_live_certificate = bool(machine_dependencies_configured and generated_artifact_proven)
    return {
        "id": STUDIO_ID,
        "name": STUDIO_NAME,
        "ready": True,
        "powered_by": "SMI",
        "pipeline": list(PIPELINE),
        "generation_tools": [dict(tool) for tool in GENERATION_TOOLS],
        "workspaces": [dict(item) for item in STUDIO_WORKSPACES],
        "workspace_default": "auto",
        "first_party_workspace_identity": True,
        "copies_provider_branding": False,
        "music_audio_generation_proven": False,
        "studio_21_stage_count": len(STUDIO_21_STAGES),
        "studio_21_stages": list(STUDIO_21_STAGES),
        "generation_backend": backend,
        "generation_backend_proven": bool(backend["configured"]),
        "owner_asset_store": {
            "schema_ready": bool(asset_store.get("schema_ready")),
            "raw_content_retained": False,
            "owner_scoped": True,
            "error": asset_store.get("error"),
        },
        "durable_receipt_backend_configured": bool(
            receipt_config.get("durable_backend_configured")
        ),
        "machine_dependencies_configured": machine_dependencies_configured,
        "machine_scope_complete": machine_dependencies_configured,
        "full_live_certificate": full_live_certificate,
        "full_live_certificate_reason": (
            "proven_generated_artifact_indexed"
            if full_live_certificate
            else ("real_generated_artifact_receipt_required" if machine_dependencies_configured else "machine_dependency_not_configured")
        ),
        "proven_generated_artifact_count": int(asset_store.get("studio_generated_asset_count", 0)),
        "auto_workspace_routing": True,
        "threat_posture": threat_posture(),
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
