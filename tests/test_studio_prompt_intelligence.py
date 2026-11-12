"""Focused tests for the canonical Studio prompt upgrade."""
import pytest

from mission_control import studio_prompt_intelligence as prompt


def test_image_prompt_preserves_user_intent_and_stays_nonexecuting():
    original = "Improve the chandelier lighting while keeping the same throne."
    result = prompt.compile_prompt("edit_image", original, has_reference=True, character_lock=True)
    assert result["compiled_prompt"].startswith(original)
    assert "Only change what the user's request asks" in result["compiled_prompt"]
    assert result["media"] == "image"
    assert result["execution_authorised"] is False
    assert result["publishing_authorised"] is False
    assert result["human_authority_final"] is True


def test_video_prompt_guides_temporal_motion_and_preserves_reference():
    original = "Make a slow seven-second push towards the king."
    result = prompt.compile_prompt("bring_alive", original, has_reference=True, character_lock=True)
    assert result["compiled_prompt"].startswith(original)
    assert "camera movement" in result["compiled_prompt"]
    assert "beat synchronisation" in result["compiled_prompt"]
    assert result["media"] == "video"
    assert result["reference_used"] is True


def test_reference_required_for_character_lock_and_bring_alive():
    with pytest.raises(ValueError, match="studio_character_lock_requires_source_image"):
        prompt.compile_prompt("imagine", "Same face", character_lock=True)
    with pytest.raises(ValueError, match="studio_source_image_data_required"):
        prompt.compile_prompt("bring_alive", "Animate the artwork")


def test_reject_unknown_tool_empty_prompt_and_oversize_prompt():
    with pytest.raises(ValueError, match="unsupported_studio_tool"):
        prompt.compile_prompt("publish", "Post this publicly")
    with pytest.raises(ValueError, match="studio_prompt_required"):
        prompt.compile_prompt("scene_builder", "  ")
    with pytest.raises(ValueError, match="studio_prompt_too_long"):
        prompt.compile_prompt("scene_builder", "a" * 4001)


def test_near_limit_video_prompt_does_not_append_partial_guidance():
    original = "Keep the same actors and original music. " + "x" * 3930
    assert len(original) < prompt.MAX_VIDEO_PROMPT
    result = prompt.compile_prompt("bring_alive", original, has_reference=True)
    assert result["compiled_prompt"] == original
    assert result["prompt_instruction_preserved"] is True


def test_guidance_is_complete_when_it_fits():
    result = prompt.compile_prompt("scene_builder", "Slow camera pan.")
    assert result["compiled_prompt"].endswith(
        "These instructions do not establish rendered continuity or beat synchronisation."
    )
