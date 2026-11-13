"""First-party culture/voice contract tests; no external synthesis required."""
import pytest

from mission_control.smi_voice_culture_profiles import (
    N247_SOUTH_LONDON, get_voice_profile,
    require_voice_reference_authorisation, voice_claims,
)


def test_n247_dialogue_exact_and_approved_direction():
    assert N247_SOUTH_LONDON.approved_dialogue == (
        "Oi, Burns! You're having a laugh, bruv! Get out that chair. "
        "EARTH IS OUR TURF — ON ANY POSTCODE! You get me?"
    )
    assert "no caricature" in N247_SOUTH_LONDON.performance_direction
    assert N247_SOUTH_LONDON.requested_accent == "South London"


def test_local_engine_never_claims_south_london_proof():
    claims = voice_claims("n247_south_london")
    assert claims["requestedAccent"] == "South London"
    assert claims["engineLocale"] == "en"
    assert claims["accentAuthenticated"] is False
    assert claims["voiceReferenceAuthorised"] is False
    assert claims["externalProviderUsed"] is False
    assert claims["productionApproved"] is False
    assert claims["humanFinalApproved"] is False


@pytest.mark.parametrize("bad", ["london", "", "n247-south-london", None, 42])
def test_unknown_profiles_fail_closed(bad):
    with pytest.raises(ValueError, match="unapproved_voice_profile"):
        get_voice_profile(bad)


def test_reference_audio_is_not_authorised_by_a_character_profile():
    with pytest.raises(PermissionError, match="voice_reference_not_authorised"):
        require_voice_reference_authorisation(N247_SOUTH_LONDON)


def test_unsupported_engine_locale_fails_closed():
    with pytest.raises(ValueError, match="unsupported_local_voice_locale"):
        voice_claims("n247_south_london", engine_locale="en-GB")


def test_generic_profile_remains_default():
    claims = voice_claims("generic_en")
    assert claims["requestedAccent"] == "unspecified"
    assert claims["accentAuthenticated"] is False
