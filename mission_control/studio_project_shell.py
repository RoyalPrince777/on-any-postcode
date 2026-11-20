"""Founder-private PROJECT SHELL scene planning for canonical SMI OAP Studio.

This is a bounded scene preset and renderer preflight, NOT an additional renderer,
media library, agent, public endpoint, approval or video artifact. The approved
eight-panel character reference from a different chat is never assumed present.
"""
from __future__ import annotations

from typing import Any

from . import studio_media_backend

PROJECT = "PROJECT SHELL"
EPISODE = "01 · Founder-private"
SIZE_BY_RATIO = {"16:9": "1280x720", "9:16": "720x1280"}
FPS_TARGETS = (24, 30, 60)
SCENES = (
    {
        "id": "01",
        "name": "Quad Arrival",
        "action": (
            "A black-and-gold OAP quad approaches the underground crew. "
            "Tracking camera, physically believable rotating wheels, rain splashes. "
            "The masked OAP hero speaks: "
            "'You lot thought nobody was watching. I know exactly what you've "
            "been hiding. Put it down.'"
        ),
        "dialogue_reference": "Founder-supplied Scene 01 dialogue",
    },
    {
        "id": "02",
        "name": "Confrontation",
        "action": (
            "Continue the Founder-supplied PROJECT SHELL confrontation. "
            "Keep the original cast, costume, setting and camera continuity. "
            "No extra dialogue has been approved for this scene."
        ),
        "dialogue_reference": "No further approved dialogue supplied",
    },
    {
        "id": "03",
        "name": "Equipment Surrender",
        "action": (
            "Continue to the equipment surrender. Preserve original "
            "character identities and scene continuity without inventing "
            "objects, slogans or new dialogue."
        ),
        "dialogue_reference": "No further approved dialogue supplied",
    },
)
BASE_CONTEXT = (
    "PROJECT SHELL · Episode 1. Founder-private original OAP characters. "
    "Rainy neon South London at night, cinematic photorealistic 3D animation. "
    "White-and-gold masked OAP hero, black-haired female OAP partner, "
    "black-and-gold OAP quad, original adult human operatives. "
    "Approved identity, wardrobe, accessories, environment and scene order "
    "must be preserved from the attached image reference. No replacement cast, "
    "generic blocks, watermarks or subtitles. Smooth natural full-body action, "
    "fluid camera, physical reflections, believable rain, original cinematic "
    "audio, natural adult South London male dialogue where supplied."
)


def status() -> dict[str, Any]:
    backend = studio_media_backend.status()
    return {
        "project": PROJECT,
        "episode": EPISODE,
        "scenes": tuple(
            {"id": scene["id"], "name": scene["name"]}
            for scene in SCENES
        ),
        "ratios": tuple(SIZE_BY_RATIO),
        "fps_targets": FPS_TARGETS,
        "video_seconds": "8",
        "renderer_configured": backend.get("configured") is True,
        "renderer_contact_verified": False,
        "source_reference_attached": False,
        "approved_reference_available_in_smi": False,
        "frame_rate_verified": False,
        "voice_sync_verified": False,
        "read_only": True,
        "generated_mp4_proven": False,
        "requires_explicit_paid_submission": True,
        "publication_granted": False,
        "founder_final_required": True,
    }


def prepare(
    scene_id: object, *, ratio: object = "16:9",
    fps_target: object = 60, reference_attached: object = False,
) -> dict[str, Any]:
    """Prepare one scene for existing Studio; never start or bill a render."""
    scene_key = str(scene_id or "").strip()
    scene = next((item for item in SCENES if item["id"] == scene_key), None)
    if scene is None:
        raise ValueError("project_shell_scene_unsupported")
    clean_ratio = str(ratio or "").strip()
    if clean_ratio not in SIZE_BY_RATIO:
        raise ValueError("project_shell_ratio_unsupported")
    if isinstance(fps_target, bool):
        raise ValueError("project_shell_fps_unsupported")
    try:
        fps = int(fps_target)
    except (ValueError, TypeError) as exc:
        raise ValueError("project_shell_fps_unsupported") from exc
    if fps not in FPS_TARGETS or str(fps_target).strip() != str(fps):
        raise ValueError("project_shell_fps_unsupported")
    if not isinstance(reference_attached, bool):
        raise ValueError("project_shell_reference_flag_invalid")

    backend = studio_media_backend.status()
    configured = backend.get("configured") is True
    prompt = (
        f"{BASE_CONTEXT} Scene {scene['id']} · {scene['name']}. "
        f"{scene['action']} Compose for {clean_ratio}, target {fps} FPS. "
        "Respect the supplied source-image reference and continuity locks. "
        "Frame-rate, lip sync and actual output fidelity require verification "
        "on the final MP4; this prompt is not proof of those capabilities."
    )
    return {
        "project": PROJECT,
        "scene_id": scene_key,
        "scene_name": scene["name"],
        "tool_id": "scene_builder",
        "prompt": prompt,
        "video_size": SIZE_BY_RATIO[clean_ratio],
        "video_seconds": "8",
        "aspect_ratio": clean_ratio,
        "fps_target": fps,
        "reference_attached": reference_attached,
        "identity_lock_requested": True,
        "identity_continuity_verified": False,
        "renderer_configured": configured,
        "renderer_contact_verified": False,
        "can_request_render": configured and reference_attached,
        "blocked_reason": (
            "renderer_unconfigured" if not configured else
            "approved_reference_required" if not reference_attached else None
        ),
        "render_submitted": False,
        "paid_submission_authorised": False,
        "artifact_proven": False,
        "fps_verified": False,
        "voice_sync_verified": False,
        "execution_granted": False,
        "publication_granted": False,
        "founder_final_required": True,
    }
