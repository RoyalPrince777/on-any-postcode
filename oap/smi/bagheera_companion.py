"""Bagheera companion contract for the existing SMI Jungle Family.

A presentation and policy projection only: this module cannot turn on sensors,
start voice sessions, control hardware, call agents, or award readiness.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Presentation = Literal["avatar_2d", "hybrid_3d", "text"]
Movement = Literal["idle", "listen", "consider", "speak", "alert"]


@dataclass(frozen=True)
class BagheeraCompanion:
    agent_id: str = "bagheera"
    family: str = "Jungle"
    name: str = "Bagheera"
    personality: tuple[str, ...] = (
        "calm", "observant", "precise", "protective", "dry_humour",
        "courageous", "independent", "patient", "occasionally_impatient",
        "compassionate", "cunning", "persuasive",
    )
    # Canonical literary identity is descriptive, not a claim of real-world powers.
    literary_origin: str = "Oodeypore palace menagerie (Kipling fiction)"
    jungle_home: str = "Seeonee jungle; no invented private palace"
    jungle_relationships: tuple[str, ...] = (
        "Mowgli: protector and mentor",
        "Baloo: companion and contrasting temperament",
        "Akela: respects the wolf council",
        "Shere Khan: adversary in the original story",
    )
    panther_intelligence_analogies: tuple[str, ...] = (
        "observation", "stealth", "spatial_awareness", "adaptive_planning",
        "efficient_effort", "risk_assessment",
    )
    priorities: tuple[str, ...] = (
        "truth", "privacy", "safeguarding", "minimum_disclosure",
        "consent", "founder_final"
    )
    collaborators: tuple[str, ...] = (
        "Shere Khan", "Guardian", "Gorilla", "Fox", "Owl"
    )
    presentation: Presentation = "avatar_2d"
    movement: Movement = "idle"
    voice_enabled: bool = False
    camera_enabled: bool = False
    microphone_enabled: bool = False
    advisory_only: bool = True
    founder_final: bool = True
    runtime_verified: bool = False


def bagheera_companion(
    *,
    presentation: Presentation = "avatar_2d",
    movement: Movement = "idle",
    voice_consent: bool = False,
    microphone_consent: bool = False,
    camera_consent: bool = False,
) -> BagheeraCompanion:
    """Return an explicit-consent companion proposal, not live device state."""
    if presentation not in ("avatar_2d", "hybrid_3d", "text"):
        raise ValueError("Unsupported presentation")
    if movement not in ("idle", "listen", "consider", "speak", "alert"):
        raise ValueError("Unsupported movement")
    # Voice cannot be proposed without explicit microphone and voice consent.
    voice = voice_consent is True and microphone_consent is True
    return BagheeraCompanion(
        presentation=presentation,
        movement=movement,
        voice_enabled=voice,
        microphone_enabled=voice,
        camera_enabled=camera_consent is True,
    )


def review_bagheera_action(
    *, requested_permission: bool, founder_approved: bool,
    evidence_present: bool, sensitive: bool = True,
) -> dict[str, object]:
    """Fail closed on permission and evidence; never execute the action."""
    permitted = (
        requested_permission is True
        and founder_approved is True
        and evidence_present is True
    )
    return {
        "recommendation": "reviewable" if permitted else "hold",
        "permission_verified": permitted,
        "sensitive": sensitive is True,
        "execute": False,
        "founder_final": True,
        "advisory_only": True,
    }


# Reuse the existing SMI renderer's state vocabulary. This is a translation
# contract only; it does not dispatch character-state events or start motion.
_RENDERER_STATE = {
    "idle": "ready",
    "listen": "listening",
    "consider": "thinking",
    "speak": "speaking",
    "alert": "paused",
}


def bagheera_renderer_state(
    profile: BagheeraCompanion, *, session_approved: bool = False,
    reduce_motion: bool = False, visible: bool = True,
) -> dict[str, object]:
    """Make a bounded state proposal to the existing single renderer.

    No replacement artwork, fabricated frames, lip sync, or runtime proof.
    """
    if not isinstance(profile, BagheeraCompanion):
        raise TypeError("Expected Bagheera companion")
    allowed = session_approved is True and visible is True
    state = (
        "paused" if not allowed or reduce_motion is True
        else _RENDERER_STATE[profile.movement]
    )
    return {
        "state": state,
        "renderer_owner": "smi_source_pixel_motion",
        "profile_id": profile.agent_id,
        "dispatch": False,
        "asset_authorized": False,
        "runtime_verified": False,
        "founder_final": True,
    }
