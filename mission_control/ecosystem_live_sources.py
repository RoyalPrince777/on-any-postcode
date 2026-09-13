"""Founder-triggered live external source adapters for Ecosystem Intelligence.

These adapters only use already-approved bounded OAP source paths. A live source
may improve external-evidence status, but one source never upgrades the whole
Ecosystem to full green. No location is read silently: the Founder supplies the
place/postcode explicitly for each refresh.
"""
from __future__ import annotations

from typing import Any

from . import ecosystem_intelligence, ecosystem_runtime, location_intelligence

_ADVISORY_PRESSURE = {
    "green": 10,
    "yellow": 35,
    "amber": 65,
    "red": 90,
}


def _geography(location: dict[str, Any]) -> dict[str, str]:
    return {
        key: value
        for key, value in {
            "postcode": str(location.get("postcode") or "").strip(),
            "borough_district": str(location.get("borough") or "").strip(),
            "county_region": str(location.get("county") or "").strip(),
            "country": str(location.get("country") or "").strip(),
            "continent": str(location.get("continent") or "").strip(),
            "global": str(location.get("global") or "Global").strip(),
        }.items()
        if value
    }


def location_weather(place: object) -> dict[str, Any]:
    """Refresh explicit place + weather evidence and route it into Ecosystem analysis."""

    query = " ".join(str(place or "").strip().split())[:120]
    if len(query) < 2:
        raise ValueError("location_required")

    resolved = location_intelligence.lookup_with_weather(query)
    weather = dict(resolved.get("weather") or {})
    intelligence = dict(weather.get("intelligence") or {})
    advisory = str(intelligence.get("advisory_level") or "green").strip().lower()
    weather_pressure = _ADVISORY_PRESSURE.get(advisory, 35)
    geography = _geography(resolved)
    observation_time = str(intelligence.get("observation_time") or weather.get("time") or "").strip()

    place_provider = str(resolved.get("provider") or "bounded_location_source")
    weather_provider = str(weather.get("provider") or "bounded_weather_source")
    condition = str(intelligence.get("condition") or "Weather observation received")

    signals = (
        {
            "domain": "place",
            "horizon": "now",
            "truth_state": "observed",
            "summary": f"Location resolved for {query}",
            "source": "oap_location_live_source",
            "evidence": (f"provider:{place_provider}",),
            "pressure": 10,
            "confidence": 100,
            "geography": geography,
            "affected_systems": ("Place Intelligence", "The Spot"),
            "recommendation": "Continue evidence-bound local context refreshes.",
        },
        {
            "domain": "nature",
            "horizon": "now",
            "truth_state": "observed",
            "summary": f"{condition}; advisory={advisory}",
            "source": "oap_weather_live_source",
            "evidence": tuple(
                value
                for value in (
                    f"provider:{weather_provider}",
                    f"observation_time:{observation_time}" if observation_time else "",
                    f"advisory:{advisory}",
                )
                if value
            ),
            "pressure": weather_pressure,
            "confidence": 100,
            "geography": geography,
            "affected_systems": ("Nature Intelligence", "Movement Intelligence"),
            "risk": (
                "Weather conditions may affect local movement and fulfilment reliability."
                if weather_pressure >= 35
                else ""
            ),
            "recommendation": (
                "Review weather-sensitive movement plans before operational change."
                if weather_pressure >= 35
                else "Continue observation."
            ),
        },
    )

    scores = ecosystem_runtime.auto_pressure_scores(signals)
    analysis = ecosystem_intelligence.analyse(
        signals,
        scope=query,
        pressure_scores=scores,
    )
    source_status = location_intelligence.status()
    gates = tuple(
        {
            **gate,
            "proven": bool(
                gate["id"] == "weather_environment"
                and source_status.get("weather_provider_verified")
            ),
        }
        for gate in ecosystem_runtime.EXTERNAL_SOURCE_GATES
    )
    return {
        "mode": "founder_triggered_live_external_source",
        "location_query": query,
        "analysis": analysis,
        "pressure_scores": scores,
        "extended_matrix_lenses": ecosystem_runtime.extended_matrix_lenses(signals),
        "source_status": source_status,
        "external_source_gates": gates,
        "weather_environment_proven": bool(source_status.get("weather_provider_verified")),
        "all_required_live_sources_proven": all(bool(gate["proven"]) for gate in gates),
        "silent_location_tracking": False,
        "execution_granted": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    """Read provider attestation already observed by this process; make no network call."""

    current = location_intelligence.status()
    weather_proven = bool(current.get("weather_provider_verified"))
    return {
        "location_provider_verified": bool(
            current.get("postcode_provider_verified") or current.get("global_provider_verified")
        ),
        "weather_environment_proven": weather_proven,
        "live_external_source_present": weather_proven,
        "all_required_live_sources_proven": False,
        "network_calls_made": False,
        "silent_location_tracking": False,
        "execution_granted": False,
    }
