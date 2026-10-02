"""First-party OAP Arena gaming-intelligence capability registry.

This module is deliberately truth-preserving: a game may have an agent fit,
training guidance, or review metadata without claiming an executable agent
opponent or ranked competitive system that does not exist yet.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

DIFFICULTY_LEVELS = ("easy", "standard", "strong", "a7")

GAME_PROFILES: dict[str, dict[str, Any]] = {
    "connect4": {
        "name": "Connect 4",
        "icon": "🔴🟡",
        "route": "/arena/connect4",
        "engine": "server_authoritative",
        "rules_status": "complete_core",
        "capabilities": {
            "local_play": True,
            "online_rooms": True,
            "agent_opponent": True,
            "training": True,
            "move_review": True,
            "ranked_results": False,
            "tournaments": False,
        },
        "training_focus": ("centre control", "threat detection", "forced wins"),
        "review_signals": ("winning move", "block required", "centre preference"),
    },
    "dot": {
        "name": "Dot",
        "icon": "🔵",
        "route": "/arena/dot",
        "engine": "server_authoritative",
        "rules_status": "playable_core",
        "capabilities": {
            "local_play": True,
            "online_rooms": True,
            "agent_opponent": False,
            "training": True,
            "move_review": True,
            "ranked_results": False,
            "tournaments": False,
        },
        "training_focus": ("box control", "chain awareness", "tempo"),
        "review_signals": ("box created", "chain opened", "forced concession"),
    },
    "ludo": {
        "name": "Ludo",
        "icon": "🎲",
        "route": "/arena/ludo",
        "engine": "server_authoritative",
        "rules_status": "four_piece_core",
        "capabilities": {
            "local_play": True,
            "online_rooms": False,
            "agent_opponent": False,
            "training": True,
            "move_review": True,
            "ranked_results": False,
            "tournaments": False,
        },
        "training_focus": ("piece activation", "safe squares", "capture timing"),
        "review_signals": ("safe move", "capture opportunity", "home progress"),
    },
    "chess": {
        "name": "Chess",
        "icon": "♟️",
        "route": "/arena/chess",
        "engine": "server_authoritative",
        "rules_status": "full_rules_local",
        "capabilities": {
            "local_play": True,
            "online_rooms": False,
            "agent_opponent": False,
            "training": True,
            "move_review": True,
            "ranked_results": False,
            "tournaments": False,
        },
        "training_focus": ("king safety", "tactics", "development", "endgames"),
        "review_signals": ("check", "capture", "promotion", "castle", "draw state"),
    },
    "oware": {
        "name": "Oware",
        "icon": "🌰",
        "route": "/arena/oware",
        "engine": "server_authoritative",
        "rules_status": "bounded_abapa_core",
        "capabilities": {
            "local_play": True,
            "online_rooms": False,
            "agent_opponent": False,
            "training": True,
            "move_review": True,
            "ranked_results": False,
            "tournaments": False,
        },
        "training_focus": ("seed count", "feeding", "capture timing"),
        "review_signals": ("capture", "feed required", "grand-slam protection"),
    },
    "iq": {
        "name": "IQ Arena",
        "icon": "🧠",
        "route": "/arena/iq",
        "engine": "server_authoritative_challenge",
        "rules_status": "seven_domain_challenge",
        "capabilities": {
            "local_play": True,
            "online_rooms": False,
            "agent_opponent": False,
            "training": True,
            "move_review": True,
            "ranked_results": False,
            "tournaments": False,
        },
        "training_focus": ("logic", "patterns", "memory", "spatial", "numbers", "language", "strategy"),
        "review_signals": ("domain", "correctness", "explanation", "skill profile"),
    },
    "route-empire": {
        "name": "Route Empire",
        "icon": "🗺️",
        "route": "/arena/route-empire",
        "engine": "server_authoritative",
        "rules_status": "strategy_core",
        "capabilities": {
            "local_play": True,
            "online_rooms": False,
            "agent_opponent": False,
            "training": True,
            "move_review": True,
            "ranked_results": False,
            "tournaments": False,
        },
        "training_focus": ("route efficiency", "expansion timing", "resource control"),
        "review_signals": ("claim", "development", "route value", "expansion"),
    },
}


def validate_registry() -> dict[str, Any]:
    errors: list[str] = []
    expected = {"connect4", "dot", "ludo", "chess", "oware", "iq", "route-empire"}
    if set(GAME_PROFILES) != expected:
        errors.append("arena_game_intelligence_catalog_invalid")
    for key, profile in GAME_PROFILES.items():
        caps = profile.get("capabilities")
        if not isinstance(caps, dict):
            errors.append(f"arena_game_capabilities_missing:{key}")
            continue
        required = {
            "local_play",
            "online_rooms",
            "agent_opponent",
            "training",
            "move_review",
            "ranked_results",
            "tournaments",
        }
        if set(caps) != required or any(not isinstance(value, bool) for value in caps.values()):
            errors.append(f"arena_game_capabilities_invalid:{key}")
        if not profile.get("training_focus") or not profile.get("review_signals"):
            errors.append(f"arena_game_guidance_missing:{key}")
    return {"passed": not errors, "errors": errors, "games": len(GAME_PROFILES)}


def catalogue() -> dict[str, Any]:
    validation = validate_registry()
    if not validation["passed"]:
        raise ValueError(validation["errors"][0])
    return {
        "schema": "oap.arena.game-intelligence.v1",
        "difficulty": list(DIFFICULTY_LEVELS),
        "games": deepcopy(GAME_PROFILES),
        "truth": {
            "agent_fit_is_not_agent_execution": True,
            "training_is_advisory": True,
            "ranked_results_require_durable_verified_results": True,
            "human_authority_final": True,
            "payments": False,
        },
    }


def game_profile(game_key: object) -> dict[str, Any]:
    key = str(game_key or "").strip().lower()
    if key not in GAME_PROFILES:
        raise ValueError("arena_game_intelligence_game_invalid")
    return {"key": key, **deepcopy(GAME_PROFILES[key])}


def summary() -> dict[str, Any]:
    data = catalogue()
    games = data["games"]
    return {
        "games": len(games),
        "local_play": sum(profile["capabilities"]["local_play"] for profile in games.values()),
        "online_rooms": sum(profile["capabilities"]["online_rooms"] for profile in games.values()),
        "agent_opponents": sum(profile["capabilities"]["agent_opponent"] for profile in games.values()),
        "training": sum(profile["capabilities"]["training"] for profile in games.values()),
        "move_review": sum(profile["capabilities"]["move_review"] for profile in games.values()),
        "ranked_results": sum(profile["capabilities"]["ranked_results"] for profile in games.values()),
        "tournaments": sum(profile["capabilities"]["tournaments"] for profile in games.values()),
    }
