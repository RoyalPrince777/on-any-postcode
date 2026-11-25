"""Fail-closed SMI mission signal scoring; no synthetic proof."""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from mission_control.smi_73_signal_field import SIGNAL_KEYS, evaluate

REGISTER_PATH = Path(__file__).with_name("smi_mission_evidence_register.json")


def load_register(path: Path = REGISTER_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    missions = data["missions"]
    if len(missions) != 44 or {m["id"] for m in missions} != set(range(1, 45)):
        raise ValueError("SMI mission register must contain 44 unique missions")
    if data["signal_model"]["expected_count"] != len(SIGNAL_KEYS):
        raise ValueError("SMI canonical signal count changed")
    return data


def mission_status(mission_id: int, *, register: Mapping[str, Any] | None = None) -> dict[str, Any]:
    data = dict(register) if register is not None else load_register()
    mission = next((m for m in data["missions"] if m["id"] == mission_id), None)
    if mission is None:
        raise ValueError("Unknown SMI mission")
    signals = mission.get("signals") or {}
    raw = signals.get("states") or {}
    if not isinstance(raw, dict):
        raise TypeError("Signal states must be a mapping")
    unknown = set(raw).difference(SIGNAL_KEYS)
    if unknown:
        raise ValueError("Unrecognised SMI signals: " + ", ".join(sorted(unknown)))
    # Stored states are declarations, not independently authenticated proof.
    # Do not award completion without a verified source, timestamp and evidence.
    evidenced = bool(signals.get("source_commit") and signals.get("evidence_timestamp") and mission.get("evidence"))
    result = evaluate(raw if evidenced else {})
    return {
        "id": mission_id,
        "name": mission["name"],
        "signal_count": result["signal_count"],
        "signal_percentage": result["completion_percentage"] if evidenced else None,
        "overall_percent": None,  # Weighted product readiness requires independent gate evidence.
        "green_100": False,  # Never promote from stored declarations alone.
        "signal_states": result["counts"],
        "stars": result["star_summary"],
        "evidence_verified": False,
        "status": "requires_independent_verification",
    }


def all_mission_statuses(*, register: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    data = dict(register) if register is not None else load_register()
    return [mission_status(m["id"], register=data) for m in data["missions"]]
