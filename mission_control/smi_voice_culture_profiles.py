"""Local-first voice character contracts. Not an accent synthesizer or voice certification.

Profiles are metadata for authorised creative performances only. Never infer
a person's culture or accent from their identity, appearance or postcode.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceProfile:
    profile_id: str
    display_name: str
    language: str
    requested_accent: str
    performance_direction: str
    approved_dialogue: str
    voice_reference_authorised: bool = False
    accent_authenticated: bool = False
    speech_engine_verified: bool = False

GENERIC_ENGLISH = VoiceProfile(
    profile_id="generic_en",
    display_name="Generic English local fallback",
    language="en",
    requested_accent="unspecified",
    performance_direction="No character voice or regional authenticity claim.",
    approved_dialogue="",
)

N247_SOUTH_LONDON = VoiceProfile(
    profile_id="n247_south_london",
    display_name="N24-7 creative voice target",
    language="en",
    requested_accent="South London",
    performance_direction=(
        "Confident adult South London male; natural contemporary conversational "
        "rhythm, cheeky comic timing, genuine regional pronunciation, "
        "no caricature or exaggerated slang; emphasis builds toward the final line."
    ),
    approved_dialogue=(
        "Oi, Burns! You're having a laugh, bruv! Get out that chair. "
        "EARTH IS OUR TURF — ON ANY POSTCODE! You get me?"
    ),
)

_PROFILES = {p.profile_id: p for p in (GENERIC_ENGLISH, N247_SOUTH_LONDON)}

def get_voice_profile(profile_id: str) -> VoiceProfile:
    if not isinstance(profile_id, str) or profile_id not in _PROFILES:
        raise ValueError("unapproved_voice_profile")
    return _PROFILES[profile_id]

def require_voice_reference_authorisation(profile: VoiceProfile) -> None:
    """Fail closed before any future reference-audio or cloning operation."""
    if not isinstance(profile, VoiceProfile) or not profile.voice_reference_authorised:
        raise PermissionError("voice_reference_not_authorised")

def voice_claims(profile_id: str, *, engine_locale: str = "en") -> dict:
    """Return truthful, privacy-safe metadata; never assert accent quality."""
    profile = get_voice_profile(profile_id)
    if engine_locale != "en":
        raise ValueError("unsupported_local_voice_locale")
    return {
        "voiceProfileId": profile.profile_id,
        "requestedAccent": profile.requested_accent,
        "engineLocale": engine_locale,
        "accentAuthenticated": False,
        "voiceReferenceAuthorised": profile.voice_reference_authorised,
        "externalProviderUsed": False,
        "productionApproved": False,
        "humanFinalApproved": False,
    }
