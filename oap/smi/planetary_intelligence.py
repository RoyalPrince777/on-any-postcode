"""Bounded Observation Ladder Level 06 Planetary Intelligence.

This layer reuses Earth and Ecosystem Intelligence to correlate explicit,
authorised local-to-global signals. It performs no collection, tracking, network
calls, prediction of individuals, permission changes or consequential actions.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from mission_control import earth_intelligence, ecosystem_intelligence

PLANETARY_LEVELS = (
    "postcode",
    "borough_district",
    "county_region",
    "country",
    "continent",
    "global",
)

ALLOWED_TRUTH_STATES = ecosystem_intelligence.TRUTH_STATES


def status() -> dict[str, Any]:
    """Return Level 06 readiness without making network calls."""
    earth = earth_intelligence.status(weather_ready=False)
    ecosystem = ecosystem_intelligence.status()
    return {
        "component": "Planetary Intelligence",
        "observation_ladder_level": 6,
        "mode": "BOUNDED_LOCAL_TO_GLOBAL_CORRELATION",
        "geography_levels": PLANETARY_LEVELS,
        "truth_states": ALLOWED_TRUTH_STATES,
        "earth_intelligence_reused": earth["architecture_passed"] is True,
        "ecosystem_intelligence_reused": ecosystem["execution_granted"] is False,
        "network_calls_made": False,
        "universal_surveillance": False,
        "individual_tracking": False,
        "execution_granted": False,
        "approval_granted": False,
        "permission_change_allowed": False,
        "human_authority_final": True,
        "full_planetary_runtime_ready": False,
    }


def correlate(
    signals: Iterable[Mapping[str, Any]],
    *,
    scope: str = "OAP World",
) -> dict[str, Any]:
    """Correlate caller-supplied evidence while preserving truth-state boundaries."""
    items = tuple(signals)
    if not items:
        raise ValueError("At least one authorised planetary signal is required")

    for signal in items:
        geography = signal.get("geography")
        if not isinstance(geography, Mapping) or not geography:
            raise ValueError("Planetary signals require explicit geography")
        unsupported = {str(key).strip().lower() for key in geography} - set(PLANETARY_LEVELS)
        if unsupported:
            raise ValueError(f"Unsupported planetary geography: {sorted(unsupported)!r}")
        truth_state = str(signal.get("truth_state") or "").strip().lower()
        if truth_state not in ALLOWED_TRUTH_STATES:
            raise ValueError("Planetary signals require an explicit supported truth_state")
        if not str(signal.get("source") or "").strip():
            raise ValueError("Planetary signals require an attributable source")
        if not tuple(signal.get("evidence") or ()):
            raise ValueError("Planetary signals require explicit evidence")

    analysis = ecosystem_intelligence.analyse(items, scope=scope)
    geography = analysis["geography"]
    represented_levels = tuple(level for level in PLANETARY_LEVELS if geography.get(level))
    return {
        "kind": "smi_planetary_intelligence_review",
        "scope": analysis["scope"],
        "represented_levels": represented_levels,
        "geography": geography,
        "truth_mix": analysis["truth_mix"],
        "domains": analysis["domains"],
        "evidence": analysis["evidence"],
        "risks": analysis["risks"],
        "opportunities": analysis["opportunities"],
        "recommendations": analysis["recommendations"],
        "geographic_pattern": analysis["geographic_pattern"],
        "smi_review_required": True,
        "guardian_required": True,
        "green_gate_required": True,
        "network_calls_made": False,
        "universal_surveillance": False,
        "individual_tracking": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
        "full_planetary_runtime_ready": False,
        "truth_boundary": (
            "This result correlates only caller-supplied attributed evidence. "
            "Cross-area patterns are not causal proof, universal observation or live planetary coverage."
        ),
    }