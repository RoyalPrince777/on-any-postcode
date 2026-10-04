"""Regression coverage for M Town Language."""
from mission_control import earth_is_our_turf, mtown_language


def test_mtown_language_status_and_alias():
    state=mtown_language.status()
    assert state["name"]=="M Town Language"
    assert state["official_language_claim"] is False
    assert state["stereotype_guard"] is True
    assert mtown_language.place_label("Mitcham")=="M Town"
    assert mtown_language.place_label("Mitcham / CR4")=="M Town · CR4"


def test_mtown_language_tones_are_distinct():
    neutral=mtown_language.phrase("route",place="Lavender Avenue",tone="neutral_local")
    local=mtown_language.phrase("route",place="Lavender Avenue",tone="m_town")
    formal=mtown_language.phrase("route",place="Lavender Avenue",tone="formal")
    assert neutral != local
    assert local != formal
    assert "Pattern" in local
    assert formal=="Navigation set to Lavender Avenue."


def test_mtown_language_excludes_gang_set_language_from_canonical_system():
    state=mtown_language.status()
    assert state["gang_set_terms_canonical"] is False
    glossary=mtown_language.glossary()
    assert any(row["term"]=="M Town" and row["class"]=="local_alias" for row in glossary)


def test_mtown_language_is_exposed_in_game_world_state():
    world=earth_is_our_turf.public_state(earth_is_our_turf.new_world())
    assert world["language"]["status"]["name"]=="M Town Language"
    assert world["language"]["place_label"]=="M Town · CR4"
    assert "M Town Centre" in world["language"]["arrival"]
