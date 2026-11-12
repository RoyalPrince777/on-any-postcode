"""Bounded prompt intelligence for the canonical Founder Studio.

Transforms a user's own creative instruction into a media-specific production
instruction. This module neither executes tools nor grants any authority.
It deliberately does not infer characters, rights, locations, or soundtrack
assets that were not supplied.
"""
from __future__ import annotations

from typing import Any

VIDEO_TOOLS = frozenset({"bring_alive", "scene_builder"})
IMAGE_TOOLS = frozenset({"imagine", "edit_image", "refine_image"})
MAX_VIDEO_PROMPT = 4000
MAX_IMAGE_PROMPT = 32000

VIDEO_GUIDANCE = (
    " Production direction: specify the subject's action over time, "
    "shot framing, camera movement, lighting and atmospheric motion. "
    "Use restrained physically coherent movement and stable proportions. "
    "Avoid unnecessary scene cuts, extra characters and invented dialogue. "
    "Preserve source-image typography and branding when a reference is used. "
    "These instructions do not establish rendered continuity or beat synchronisation."
)
IMAGE_GUIDANCE = (
    " Production direction: maintain deliberate composition, clear lighting, "
    "legible intended typography and consistent visual detail. "
    "Only change what the user's request asks to change."
)


def compile_prompt(
    tool_id: object,
    prompt: object,
    *,
    has_reference: bool = False,
    character_lock: bool = False,
) -> dict[str, Any]:
    """Produce a deterministic, secret-free brief for an existing Studio tool.

    No speculative project context is added. A video requires an instruction;
    the Studio's existing refine-image default is handled before this function.
    """
    tool = str(tool_id or "").strip()
    if tool not in VIDEO_TOOLS | IMAGE_TOOLS:
        raise ValueError("unsupported_studio_tool")
    text = str(prompt or "").strip()
    if not text:
        raise ValueError("studio_prompt_required")
    if character_lock and not has_reference:
        raise ValueError("studio_character_lock_requires_source_image")
    if tool == "bring_alive" and not has_reference:
        raise ValueError("studio_source_image_data_required")

    guidance = VIDEO_GUIDANCE if tool in VIDEO_TOOLS else IMAGE_GUIDANCE
    limit = MAX_VIDEO_PROMPT if tool in VIDEO_TOOLS else MAX_IMAGE_PROMPT
    # Preserve the actual user instruction before advisory guidance.
    if len(text) > limit:
        raise ValueError("studio_prompt_too_long")
    # Never chop production guidance mid-sentence. A truncated instruction can
    # reverse or obscure continuity requirements and mislead the model.
    # User-authored instructions always take precedence over optional guidance.
    compiled = text + guidance if len(text) + len(guidance) <= limit else text
    return {
        "tool_id": tool,
        "media": "video" if tool in VIDEO_TOOLS else "image",
        "compiled_prompt": compiled,
        "reference_used": bool(has_reference),
        "character_lock": bool(character_lock),
        "prompt_instruction_preserved": compiled.startswith(text),
        "execution_authorised": False,
        "publishing_authorised": False,
        "human_authority_final": True,
    }
