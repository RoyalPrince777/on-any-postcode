"""Always-on, low-noise SMI intelligence routing for OAP requests.

This module does not call a model, mutate state, approve actions, or create audit
noise. It classifies each request into the minimum governed intelligence lenses
needed for that surface. Consequential actions escalate to War Room review while
Human Authority remains final.
"""
from __future__ import annotations

from collections.abc import Iterable

AUTO_VERSION = 1
AUTO_LIGHT = "purple"
BASE_LENSES = ("truth", "evidence", "alignment")
WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _add(target: list[str], values: Iterable[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def observe(method: object, path: object, endpoint: object = None) -> dict[str, object]:
    """Return deterministic SMI routing metadata for one request.

    The result is intentionally side-effect free. It is safe to run on every
    request and exists to keep SMI present without turning every click into an
    expensive provider call or noisy database event.
    """

    method_key = str(method or "GET").upper()
    path_key = "/" + str(path or "").lstrip("/").lower()
    endpoint_key = str(endpoint or "").lower()
    lenses: list[str] = list(BASE_LENSES)

    private_surface = path_key.startswith(("/mission", "/my-world", "/myworld", "/infrastructure"))
    write_action = method_key in WRITE_METHODS

    if private_surface:
        _add(lenses, ("security", "privacy"))
    if any(token in path_key for token in ("map", "atlas", "movement", "route", "travel", "booking", "direct")):
        _add(lenses, ("dependency", "architecture", "risk", "performance"))
    if any(token in path_key for token in ("link", "message", "voice", "call", "presence")):
        _add(lenses, ("privacy", "security", "behaviour"))
    if any(token in path_key for token in ("market", "sika", "payment", "wallet", "commerce")):
        _add(lenses, ("risk", "data", "privacy", "readiness"))
    if any(token in path_key for token in ("health", "status", "proof", "receipt", "audit")):
        _add(lenses, ("readiness", "resilience"))
    if any(token in path_key for token in ("war-room", "judgement", "approval")):
        _add(lenses, ("gap", "swot", "risk", "dependency", "readiness", "decision", "judgement"))
    if write_action:
        _add(lenses, ("risk", "security", "privacy", "readiness", "decision", "judgement"))

    consequential = write_action or any(
        token in path_key
        for token in (
            "judgement",
            "approval",
            "deploy",
            "migration",
            "dispatch",
            "payment",
            "wallet",
            "certify",
        )
    )

    return {
        "component": "SMI Automatic Intelligence",
        "version": AUTO_VERSION,
        "active": True,
        "light": AUTO_LIGHT,
        "mode": "automatic_low_noise",
        "method": method_key,
        "path": path_key,
        "endpoint": endpoint_key,
        "lenses": tuple(lenses),
        "private_surface": private_surface,
        "write_action": write_action,
        "war_room_escalation": consequential,
        "provider_call_performed": False,
        "database_write_performed": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }


def public_status() -> dict[str, object]:
    """Return the stable architecture contract without request-specific data."""

    return {
        "component": "SMI Automatic Intelligence",
        "version": AUTO_VERSION,
        "active": True,
        "light": AUTO_LIGHT,
        "mode": "automatic_low_noise",
        "base_lenses": BASE_LENSES,
        "provider_call_per_request": False,
        "database_write_per_request": False,
        "consequential_actions_escalate": True,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }
