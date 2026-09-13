"""Founder-governed live evidence adapters for Ecosystem Intelligence.

The module keeps source proof separate from execution authority. It can observe
approved OAP runtime evidence and bounded public sources, but it never upgrades
missing evidence to green, never reads device location silently and never grants
operational execution.
"""
from __future__ import annotations

import os
from typing import Any

from oap.guardian import GuardianEngine

from . import (
    ecosystem_intelligence,
    ecosystem_runtime,
    humanitarian_emergency_tracker,
    location_intelligence,
    smi_receipt_backend,
    telemetry,
)

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


def _render_runtime_present() -> bool:
    commit = os.getenv("RENDER_GIT_COMMIT", "").strip()
    identity = (
        os.getenv("RENDER_SERVICE_ID", "").strip()
        or os.getenv("RENDER_EXTERNAL_URL", "").strip()
        or os.getenv("RENDER_SERVICE_NAME", "").strip()
    )
    return bool(commit and identity)


def _owned_runtime_evidence() -> dict[str, Any]:
    local = telemetry.status()
    guardian = GuardianEngine().status()
    local_observability = bool(local.get("local_observability_ready"))
    aggregate_activity = bool(
        int(local.get("local_request_count") or 0) > 0
        and local.get("local_last_request_epoch") is not None
    )
    infrastructure = bool(local_observability and _render_runtime_present())
    trust = bool(guardian.get("ready") and local_observability)
    return {
        "telemetry": local,
        "guardian": guardian,
        "render_runtime_present": _render_runtime_present(),
        "infrastructure_telemetry_proven": infrastructure,
        "people_aggregate_proven": aggregate_activity,
        "trust_guardian_proven": trust,
    }


def _gate_states() -> tuple[dict[str, Any], ...]:
    location_state = location_intelligence.status()
    owned = _owned_runtime_evidence()
    proven = {
        "weather_environment": bool(location_state.get("weather_provider_verified")),
        "movement_navigation": False,
        "civic_public_services": False,
        "culture_provenance": False,
        "infrastructure_telemetry": bool(owned["infrastructure_telemetry_proven"]),
        "market_activity": False,
        "people_aggregate": bool(owned["people_aggregate_proven"]),
        "trust_guardian": bool(owned["trust_guardian_proven"]),
    }
    evidence = {
        "weather_environment": "bounded location/weather provider observation",
        "movement_navigation": "self-hosted live routing/transport evidence still required",
        "civic_public_services": "current public-service/civic adapter still required",
        "culture_provenance": "provenance-backed culture/history source still required",
        "infrastructure_telemetry": "fresh OAP request/health telemetry plus Render runtime identity",
        "market_activity": "real Market demand/supply/fulfilment evidence still required",
        "people_aggregate": "privacy-safe aggregate OAP request activity",
        "trust_guardian": "live Guardian readiness plus fresh local observability",
    }
    return tuple(
        {
            **gate,
            "proven": bool(proven.get(gate["id"])),
            "evidence": evidence[gate["id"]],
        }
        for gate in ecosystem_runtime.EXTERNAL_SOURCE_GATES
    )


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
    observation_time = str(
        intelligence.get("observation_time") or weather.get("time") or ""
    ).strip()

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
    gates = _gate_states()
    return {
        "mode": "founder_triggered_live_external_source",
        "location_query": query,
        "analysis": analysis,
        "pressure_scores": scores,
        "extended_matrix_lenses": ecosystem_runtime.extended_matrix_lenses(signals),
        "source_status": location_intelligence.status(),
        "external_source_gates": gates,
        "weather_environment_proven": any(
            gate["id"] == "weather_environment" and gate["proven"] for gate in gates
        ),
        "all_required_live_sources_proven": all(bool(gate["proven"]) for gate in gates),
        "silent_location_tracking": False,
        "execution_granted": False,
        "human_authority_final": True,
    }


def prove_full(place: object) -> dict[str, Any]:
    """Run one bounded Founder proof pass across available live evidence lanes."""

    query = " ".join(str(place or "").strip().split())[:120]
    if len(query) < 2:
        raise ValueError("location_required")

    source_failures: list[str] = []
    location_result: dict[str, Any] | None = None
    try:
        location_result = location_weather(query)
    except location_intelligence.LocationUnavailable:
        source_failures.append("location_weather_unavailable")

    humanitarian = humanitarian_emergency_tracker.humanitarian_emergency_snapshot(
        live_fetch=True,
        force=True,
    )
    if not humanitarian.get("live_data_ready"):
        source_failures.append("humanitarian_sources_unavailable")

    receipt = smi_receipt_backend.receipt_backend_status()
    current = status()
    gates = current["external_source_gates"]
    pending = tuple(gate["id"] for gate in gates if not gate["proven"])
    durable_hrm = bool(receipt.get("independent_durable_hrm_ready"))
    external_complete = not pending

    return {
        "mode": "founder_full_ecosystem_proof_pass",
        "location_query": query,
        "location_weather": location_result,
        "humanitarian": {
            "live_data_ready": bool(humanitarian.get("live_data_ready")),
            "live_source_count": int(humanitarian.get("live_source_count") or 0),
            "live_sources": tuple(humanitarian.get("live_sources") or ()),
            "event_count": int(humanitarian.get("event_count") or 0),
            "fetched_at": humanitarian.get("fetched_at"),
        },
        "receipt_backend": receipt,
        "external_source_gates": gates,
        "proven_gate_count": sum(bool(gate["proven"]) for gate in gates),
        "required_gate_count": len(gates),
        "pending_gates": pending,
        "all_required_live_sources_proven": external_complete,
        "durable_hrm_write_read_proven": durable_hrm,
        "full_ecosystem_green": bool(external_complete and durable_hrm),
        "source_failures": tuple(source_failures),
        "network_calls_made": True,
        "silent_location_tracking": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    """Read current source attestations without making network calls."""

    gates = _gate_states()
    proven_count = sum(bool(gate["proven"]) for gate in gates)
    owned = _owned_runtime_evidence()
    weather_proven = any(
        gate["id"] == "weather_environment" and gate["proven"] for gate in gates
    )
    return {
        "location_provider_verified": bool(
            location_intelligence.status().get("postcode_provider_verified")
            or location_intelligence.status().get("global_provider_verified")
        ),
        "weather_environment_proven": weather_proven,
        "infrastructure_telemetry_proven": owned["infrastructure_telemetry_proven"],
        "people_aggregate_proven": owned["people_aggregate_proven"],
        "trust_guardian_proven": owned["trust_guardian_proven"],
        "external_source_gates": gates,
        "proven_gate_count": proven_count,
        "required_gate_count": len(gates),
        "live_external_source_present": proven_count > 0,
        "all_required_live_sources_proven": proven_count == len(gates),
        "network_calls_made": False,
        "silent_location_tracking": False,
        "execution_granted": False,
        "human_authority_final": True,
    }
