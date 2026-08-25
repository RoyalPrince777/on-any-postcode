"""Operational self-model for SMI without consciousness or sentience claims."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone


def _string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    return (str(value),)


def _clamp_uncertainty(value: object, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(0.0, min(1.0, number))


@dataclass(frozen=True, slots=True)
class ComponentSnapshot:
    """A truthful point-in-time observation of one SMI/OAP component."""

    component: str
    ready: bool
    mode: str
    uncertainty: float
    dependencies: tuple[str, ...]
    permissions: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "component": self.component,
            "ready": self.ready,
            "mode": self.mode,
            "uncertainty": self.uncertainty,
            "dependencies": self.dependencies,
            "permissions": self.permissions,
        }


@dataclass(frozen=True, slots=True)
class SelfModelSnapshot:
    """Bounded internal world-model derived only from observed runtime state."""

    revision: int
    observed_at: str
    overall_ready: bool
    degraded_components: tuple[str, ...]
    unknown_components: tuple[str, ...]
    components: tuple[ComponentSnapshot, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "revision": self.revision,
            "observed_at": self.observed_at,
            "overall_ready": self.overall_ready,
            "degraded_components": self.degraded_components,
            "unknown_components": self.unknown_components,
            "components": tuple(component.as_dict() for component in self.components),
            "sentience_claimed": False,
            "consciousness_claimed": False,
        }


class SelfModel:
    """Observe component state; never invent state that was not reported."""

    def __init__(self) -> None:
        self._revision = 0
        self._last_snapshot: SelfModelSnapshot | None = None

    def observe(
        self,
        statuses: Iterable[Mapping[str, object]],
    ) -> SelfModelSnapshot:
        components: list[ComponentSnapshot] = []
        unknown: list[str] = []

        for index, status in enumerate(statuses):
            component = str(status.get("component") or f"unknown-{index + 1}")
            ready_value = status.get("ready")
            readiness_known = isinstance(ready_value, bool)
            ready = bool(ready_value) if readiness_known else False
            if not readiness_known:
                unknown.append(component)

            default_uncertainty = 0.0 if ready and readiness_known else 0.5
            components.append(
                ComponentSnapshot(
                    component=component,
                    ready=ready,
                    mode=str(status.get("mode") or "unknown"),
                    uncertainty=_clamp_uncertainty(
                        status.get("uncertainty"),
                        default_uncertainty,
                    ),
                    dependencies=_string_tuple(status.get("dependencies")),
                    permissions=_string_tuple(status.get("permissions")),
                )
            )

        self._revision += 1
        degraded = tuple(
            component.component for component in components if not component.ready
        )
        snapshot = SelfModelSnapshot(
            revision=self._revision,
            observed_at=datetime.now(timezone.utc).isoformat(),
            overall_ready=bool(components) and not degraded and not unknown,
            degraded_components=degraded,
            unknown_components=tuple(unknown),
            components=tuple(components),
        )
        self._last_snapshot = snapshot
        return snapshot

    def status(self) -> dict[str, object]:
        if self._last_snapshot is None:
            return {
                "component": "SMI Self Model",
                "ready": False,
                "initialized": False,
                "sentience_claimed": False,
                "consciousness_claimed": False,
            }
        return {
            "component": "SMI Self Model",
            "ready": True,
            "initialized": True,
            "snapshot": self._last_snapshot.as_dict(),
            "sentience_claimed": False,
            "consciousness_claimed": False,
        }
