"""M Town Language v1 for EARTH IS OUR TURF.

A respectful first-party language layer for Mitcham/M Town gameplay.
It separates:
- recognisable local/Greater London colloquial language,
- place aliases,
- OAP-created game language.

It does not claim every Mitcham resident speaks the same way and it excludes
gang-set naming from the canonical player/NPC language system.
"""
from __future__ import annotations

from typing import Any

SCHEMA = "oap.eiot.mtown-language.v1"

LEXICON: tuple[dict[str, Any], ...] = (
    {
        "term":"M Town",
        "meaning":"Mitcham",
        "class":"local_alias",
        "usage":"place_identity",
        "canonical":True,
        "official_name":"Mitcham",
    },
    {
        "term":"ends",
        "meaning":"local area / home area",
        "class":"south_london_colloquial",
        "usage":"area_reference",
        "canonical":False,
    },
    {
        "term":"link",
        "meaning":"meet / connect",
        "class":"south_london_colloquial",
        "usage":"social",
        "canonical":False,
    },
    {
        "term":"pattern",
        "meaning":"arrange / sort out",
        "class":"south_london_colloquial",
        "usage":"planning",
        "canonical":False,
    },
    {
        "term":"safe",
        "meaning":"okay / good / thanks depending on context",
        "class":"south_london_colloquial",
        "usage":"acknowledgement",
        "canonical":False,
    },
    {
        "term":"yard",
        "meaning":"home",
        "class":"london_colloquial",
        "usage":"home_reference",
        "canonical":False,
    },
    {
        "term":"bare",
        "meaning":"a lot / very",
        "class":"london_colloquial",
        "usage":"intensifier",
        "canonical":False,
    },
    {
        "term":"Tap In",
        "meaning":"open or enter an active game interaction",
        "class":"oap_game_language",
        "usage":"interaction",
        "canonical":True,
    },
    {
        "term":"My Card",
        "meaning":"player identity surface",
        "class":"oap_game_language",
        "usage":"identity",
        "canonical":True,
    },
    {
        "term":"Incoming",
        "meaning":"new notification or incoming event",
        "class":"oap_game_language",
        "usage":"notification",
        "canonical":True,
    },
    {
        "term":"Face Up",
        "meaning":"video call",
        "class":"oap_game_language",
        "usage":"communication",
        "canonical":True,
    },
    {
        "term":"Postcode Memory",
        "meaning":"the world remembering meaningful player actions",
        "class":"oap_game_language",
        "usage":"world_state",
        "canonical":True,
    },
)

PLACE_ALIASES = {
    "Mitcham":"M Town",
    "Mitcham / CR4":"M Town · CR4",
    "Mitcham · CR4":"M Town · CR4",
    "Mitcham Town Centre":"M Town Centre",
}

TONE_PROFILES = {
    "neutral_local":{
        "description":"Natural London English with light local wording.",
        "slang_density":"low",
        "default":True,
    },
    "m_town":{
        "description":"Stronger local flavour for familiar characters without caricature.",
        "slang_density":"medium",
        "default":False,
    },
    "formal":{
        "description":"Clear standard English for services, businesses and official game notices.",
        "slang_density":"none",
        "default":False,
    },
}

def glossary() -> list[dict[str, Any]]:
    return [dict(row) for row in LEXICON]

def place_label(name: object, *, local: bool=True) -> str:
    value=str(name or "").strip()
    if not value:
        return ""
    return PLACE_ALIASES.get(value, value) if local else value

def phrase(intent: object, *, place: object | None=None, tone: object="neutral_local") -> str:
    key=str(intent or "").strip().lower()
    profile=str(tone or "neutral_local").strip()
    if profile not in TONE_PROFILES:
        raise ValueError("mtown_language_tone_invalid")
    label=place_label(place) if place else "M Town"

    neutral={
        "arrival":f"You're in {label}.",
        "meet":f"Link at {label}.",
        "route":f"Route set for {label}.",
        "welcome":f"Welcome to {label}.",
    }
    stronger={
        "arrival":f"You're in {label} now.",
        "meet":f"Link up at {label}.",
        "route":f"Pattern the route to {label}.",
        "welcome":f"Welcome to {label} — M Town.",
    }
    formal={
        "arrival":f"Current location: {label}.",
        "meet":f"Meet at {label}.",
        "route":f"Navigation set to {label}.",
        "welcome":f"Welcome to {label}.",
    }
    source={"neutral_local":neutral,"m_town":stronger,"formal":formal}[profile]
    if key not in source:
        raise ValueError("mtown_language_intent_invalid")
    return source[key]

def status() -> dict[str, Any]:
    return {
        "schema":SCHEMA,
        "name":"M Town Language",
        "version":1,
        "identity":"Mitcham / M Town",
        "official_language_claim":False,
        "stereotype_guard":True,
        "gang_set_terms_canonical":False,
        "tone_profiles":list(TONE_PROFILES),
        "lexicon_size":len(LEXICON),
    }
