"""First-party worldwide territory matrix for OAP Open Cinema candidate leads.

Country-specific claim capture is NOT a grant. Server-verified agreement, chain
of title, asset integrity, and entitlement are not connected; all territories
remain blocked regardless of caller assertions or worldwide labels.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import date

MAX_TERRITORIES = 249
VIEWING_MODELS = frozenset({"SVOD", "TVOD", "AVOD", "FAST", "FREE_TO_VIEW"})


def _country(value: object) -> str | None:
    """ISO 3166-1 alpha-2 syntax, not a substitute for country registry validation."""
    if not isinstance(value, str) or len(value) != 2 or not value.isascii():
        return None
    country = value.upper()
    return country if country.isalpha() else None


def _iso_date(value: object) -> str | None:
    if not isinstance(value, str) or len(value) != 10:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def country_claim(row: object) -> dict[str, object] | None:
    if not isinstance(row, Mapping):
        return None
    country = _country(row.get("country"))
    models = row.get("models")
    start = _iso_date(row.get("starts_on"))
    end = _iso_date(row.get("ends_on"))
    if (
        not country or not isinstance(models, list)
        or not models or len(models) > len(VIEWING_MODELS)
        or any(not isinstance(model, str) or model not in VIEWING_MODELS for model in models)
        or len(set(models)) != len(models)
        or not start or not end or start > end
    ):
        return None
    return {
        "country": country,
        "claimed_models": sorted(models),
        "claimed_start": start,
        "claimed_end": end,
        "agreement_verified": False,
        "chain_of_title_verified": False,
        "asset_integrity_verified": False,
        "viewer_entitlement_verified": False,
        "human_release_approved": False,
        "available": False,
        "playback_enabled": False,
        "blockers": [
            "independent_title_and_country_rights_not_connected",
            "authorised_asset_and_entitlement_not_connected",
            "human_release_approval_not_granted",
        ],
    }


def matrix(rows: object) -> dict[str, object]:
    """A bounded private claim projection. Never infer worldwide clearance."""
    values = rows if isinstance(rows, list) else []
    claims: list[dict[str, object]] = []
    seen = set()
    for row in values[:MAX_TERRITORIES]:
        claim = country_claim(row)
        if claim is None or claim["country"] in seen:
            continue
        seen.add(claim["country"])
        claims.append(claim)
    return {
        "scope": "worldwide_country_by_country_claim_preview",
        "countries": claims,
        "country_count": len(claims),
        "worldwide_cleared": False,
        "global_license_acquired": False,
        "licensed_countries": [],
        "playback_enabled": False,
        "publication_enabled": False,
        "registry_connected": False,
        "human_authority_final": True,
    }
