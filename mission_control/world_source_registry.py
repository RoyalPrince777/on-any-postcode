"""Trusted source registry for structured OAP world observations."""

from __future__ import annotations

from typing import Any

SOURCES: dict[str, dict[str, Any]] = {
    "api.open-meteo.com": {
        "source_ownership": "external_public",
        "required_evidence_prefixes": ("provider:", "observation_time:"),
        "max_fresh_for_seconds": 900,
        "max_stale_after_seconds": 3600,
        "max_expires_after_seconds": 21600,
        "observation_first_party": False,
    },
}


def get(source: object) -> dict[str, Any] | None:
    key = str(source or "").strip().lower()
    policy = SOURCES.get(key)
    return dict(policy) if policy else None


def status() -> dict[str, Any]:
    return {
        "registered_source_ids": tuple(sorted(SOURCES)),
        "registered_source_count": len(SOURCES),
        "unknown_sources_can_claim_live": False,
        "source_ownership_is_registry_bound": True,
        "execution_granted": False,
        "human_authority_final": True,
    }
