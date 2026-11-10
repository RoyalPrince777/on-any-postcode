"""Truth-labelled OAP Events pulse calculations.

Pure calculation only: this module does not invent bookings, watchers, money or
people-flow observations. Callers must supply measured values from an authorised
store before presenting them as live.
"""
from __future__ import annotations

RAM_STAGES = (
    (14, "Quiet For Now 👀"),
    (34, "Warming Up"),
    (54, "Getting Ram 🔥"),
    (74, "Ram"),
    (89, "Proper Ram"),
    (99, "About To Be Ram Out 🚨"),
    (100, "RAM OUT 🔥"),
)

MOMENTUM_STAGES = (
    (0, "Cold"),
    (1, "Moving"),
    (2, "Heating Up 🔥"),
    (3, "Flying 🔥🔥"),
    (4, "Going Mad 🔥🔥🔥"),
)


def ram_meter(confirmed: int, capacity: int) -> dict[str, object]:
    """Return the seven-stage Ram Meter from confirmed capacity only."""
    if capacity <= 0:
        raise ValueError("capacity_must_be_positive")
    if confirmed < 0:
        raise ValueError("confirmed_must_be_non_negative")
    confirmed = min(confirmed, capacity)
    percent = int((confirmed * 100) / capacity)
    label = RAM_STAGES[-1][1]
    for ceiling, candidate in RAM_STAGES:
        if percent <= ceiling:
            label = candidate
            break
    return {
        "confirmed": confirmed,
        "capacity": capacity,
        "spaces_left": max(capacity - confirmed, 0),
        "percent": percent,
        "stage": label,
    }


def momentum_stage(level: int) -> str:
    """Map a bounded 0–4 evidence-backed momentum level to five public stages."""
    if level < 0 or level > 4:
        raise ValueError("momentum_level_out_of_range")
    return MOMENTUM_STAGES[level][1]
