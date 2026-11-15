"""Founder-only, fail-closed character-swap preparation for canonical SMI Studio.

This is not a provider executor. Credit spending, publishing and promotion must
remain separately authorised. Media must be pre-registered in a private asset
store; never accept a remote URL as a replacement for ownership checks.
"""
from __future__ import annotations

import re
from typing import Any

_MEDIA_ID = re.compile(r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
MAX_SECONDS = 30.0
MIN_SECONDS = 4.0


def prepare(*, source_video_id: object, character_image_id: object,
            source_duration_seconds: object, target: object = "primary_person",
            quoted_credits: object = None) -> dict[str, Any]:
    """Validate input metadata; do not call the rendering provider."""
    video_id = str(source_video_id or "").strip()
    image_id = str(character_image_id or "").strip()
    if not _MEDIA_ID.fullmatch(video_id) or not _MEDIA_ID.fullmatch(image_id):
        raise ValueError("studio_swap_registered_media_ids_required")
    if video_id == image_id:
        raise ValueError("studio_swap_distinct_media_required")
    try:
        duration = float(source_duration_seconds)
    except (ValueError, TypeError) as exc:
        raise ValueError("studio_swap_duration_invalid") from exc
    if not (MIN_SECONDS <= duration <= MAX_SECONDS):
        raise ValueError("studio_swap_duration_out_of_range")
    if str(target or "") != "primary_person":
        raise ValueError("studio_swap_target_unsupported")
    if quoted_credits is not None:
        if isinstance(quoted_credits, bool) or not isinstance(quoted_credits, int) or quoted_credits < 1:
            raise ValueError("studio_swap_quote_invalid")
    return {
        "operation": "character_swap",
        "workspace": "motion",
        "state": "prepared",
        "model_intent": "hf_mult_replace_object",
        "source_video_id": video_id,
        "character_image_id": image_id,
        "source_duration_seconds": duration,
        "target": "primary_person",
        "quote_claimed_credits": quoted_credits,
        "quote_verified_by_smi": False,
        "media_ownership_verified": False,
        "provider_connected_to_smi": False,
        "render_submitted": False,
        "output_generated": False,
        "execution_granted": False,
        "payment_authorised": False,
        "publishing_granted": False,
        "distribution_granted": False,
        "guardian_required": True,
        "hrm_receipt_required": True,
        "founder_final": True,
        "next_gate": "owner_media_and_live_quote_verification",
    }
