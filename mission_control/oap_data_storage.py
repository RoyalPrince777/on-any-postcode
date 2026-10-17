"""OAP Data: first-party, fail-closed storage allocation policy.

No storage is provisioned by this module. Capacities must be supplied from
measured infrastructure, not guessed from device or cloud assumptions.
"""
from __future__ import annotations

from dataclasses import dataclass

SYSTEMS = frozenset({"music", "tv", "drive", "market", "mail", "library", "world", "sika"})
DEFAULT_RESERVE_PERCENT = 20


@dataclass(frozen=True)
class StorageCapacity:
    total_bytes: int
    used_bytes: int
    measured: bool = False

    def __post_init__(self) -> None:
        if (
            isinstance(self.total_bytes, bool)
            or isinstance(self.used_bytes, bool)
            or not isinstance(self.total_bytes, int)
            or not isinstance(self.used_bytes, int)
            or self.total_bytes < 0
            or self.used_bytes < 0
            or self.used_bytes > self.total_bytes
        ):
            raise ValueError("invalid_storage_capacity")

    @property
    def free_bytes(self) -> int:
        return self.total_bytes - self.used_bytes


def admission(
    *,
    system: str,
    requested_bytes: int,
    capacity: StorageCapacity | None,
    reserve_percent: int = DEFAULT_RESERVE_PERCENT,
) -> dict[str, object]:
    """Conservatively admit an allocation only against measured free space.

    The reserve is calculated against total capacity, and never overcommitted.
    This is a preflight only; real allocation must recheck capacity atomically.
    """
    if system not in SYSTEMS:
        raise ValueError("unknown_oap_storage_system")
    if isinstance(requested_bytes, bool) or not isinstance(requested_bytes, int) or requested_bytes < 0:
        raise ValueError("invalid_requested_bytes")
    if isinstance(reserve_percent, bool) or not isinstance(reserve_percent, int) or not 0 <= reserve_percent <= 99:
        raise ValueError("invalid_reserve_percent")
    if capacity is None or not capacity.measured:
        return {"allowed": False, "reason": "capacity_unverified", "system": system}
    reserve = (capacity.total_bytes * reserve_percent + 99) // 100
    usable = max(0, capacity.free_bytes - reserve)
    return {
        "allowed": requested_bytes <= usable,
        "reason": "within_budget" if requested_bytes <= usable else "insufficient_capacity",
        "system": system,
        "requested_bytes": requested_bytes,
        "usable_bytes": usable,
        "reserve_bytes": reserve,
    }
