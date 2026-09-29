"""Always-on, low-noise SMI intelligence routing for OAP requests.

This module does not call a model, mutate state, approve actions, or create audit
noise. It classifies each request into the minimum governed intelligence lenses
needed for that surface. Consequential actions escalate to War Room review while
Human Authority remains final.
"""
from __future__ import annotations

from collections.abc import Iterable

AUTO_VERSION = 2
AUTO_LIGHT = "purple"
BASE_LENSES = ("truth", "evidence", "alignment")
WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

SEMANTIC_RULES = (
    (("confusing", "usability", "navigation", "button", "layout", "mobile", "desktop"), ("ux", "behaviour")),
    (("slow", "latency", "performance", "speed", "bottleneck"), ("performance", "architecture")),
    (("failure", "broken", "rollback", "recover", "recovery", "fallback"), ("resilience", "risk")),
    (("privacy", "consent", "retention", "sensitive"), ("privacy", "data")),
    (("database", "schema", "record", "ledger", "data", "provenance", "duplicate"), ("data", "architecture")),
    (("architecture", "ownership", "boundary", "interface", "route", "api"), ("architecture", "dependency")),
    (("ready", "readiness", "release", "green", "proof", "verify", "evidence"), ("readiness", "gap")),
    (("priority", "next", "roadmap", "sequence", "dependency"), ("priority", "dependency")),
    (("opportunity", "improve", "upgrade", "value", "growth"), ("opportunity", "impact")),
    (("competitor", "competitive", "compare", "alternative"), ("competitive", "decision")),
    (("trend", "latest", "change"), ("trend", "impact")),
    (("swot",), ("swot",)),
    (("behaviour", "behavior", "repetition"), ("behaviour",)),
    (("scenario", "what if", "what-if"), ("scenario", "risk")),
)

SEMANTIC_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("confusing", "hard to use", "usability", "navigation", "button", "layout", "mobile", "desktop"), ("ux", "behaviour")),
    (("slow", "latency", "performance", "speed", "bottleneck", "load"), ("performance", "architecture")),
    (("crash", "failure", "broken", "rollback", "recover", "recovery", "fallback"), ("resilience", "risk")),
    (("secure", "security", "auth", "permission", "secret", "attack", "abuse"), ("security", "risk")),
    (("privacy", "consent", "retention", "tracking", "sensitive"), ("privacy", "data")),
    (("database", "schema", "record", "ledger", "data", "provenance", "duplicate"), ("data", "architecture")),
    (("architecture", "ownership", "boundary", "interface", "route", "api"), ("architecture", "dependency")),
    (("ready", "readiness", "release", "green", "proof", "verify", "evidence"), ("readiness", "gap")),
    (("priority", "next", "roadmap", "sequence", "dependency"), ("priority", "dependency")),
    (("opportunity", "improve", "upgrade", "value", "growth"), ("opportunity", "impact")),
    (("competitor", "competitive", "compare", "alternative"), ("competitive", "decision")),
    (("trend", "latest", "change", "market shift"), ("trend", "impact")),
    (("swot",), ("swot",)),
    (("behaviour", "behavior", "repetition", "overconfident"), ("behaviour",)),
    (("scenario", "what if", "what-if"), ("scenario", "risk")),
)


def _add(target: list[str], values: Iterable[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def _semantic_lenses(message: object) -> tuple[str, ...]:
    """Select only mission-relevant specialist lenses from safe message text.

    This is deterministic keyword routing, not private reasoning and not a model
    call. It can enrich surface routing without granting any authority.
    """
    text = str(message or "").casefold().strip()
    if not text:
        return ()
    selected: list[str] = []
    for triggers, lenses in SEMANTIC_RULES:
        if any(trigger in text for trigger in triggers):
            _add(selected, lenses)
    return tuple(selected)


def observe(method: object, path: object, endpoint: object = None, message: object = None) -> dict[str, object]:
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

    semantic_lenses = _semantic_lenses(message)
    _add(lenses, semantic_lenses)

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
        "semantic_lenses": semantic_lenses,
        "selector": "surface+action+mission",
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
        "selector": "surface+action+mission",
        "semantic_routing": True,
        "provider_call_per_request": False,
        "database_write_per_request": False,
        "consequential_actions_escalate": True,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }
