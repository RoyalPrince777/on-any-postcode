"""Detect runtime disagreement without silently choosing a winner."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CoherenceConflict:
    """A disagreement that requires explicit review instead of silent resolution."""

    claim: str
    values: tuple[str, ...]
    components: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "claim": self.claim,
            "values": self.values,
            "components": self.components,
        }


@dataclass(frozen=True, slots=True)
class CoherenceReport:
    """Result of comparing component claims and duplicate component state."""

    coherent: bool
    checked_components: int
    uncertainty: float
    human_review_required: bool
    conflicts: tuple[CoherenceConflict, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "coherent": self.coherent,
            "checked_components": self.checked_components,
            "uncertainty": self.uncertainty,
            "human_review_required": self.human_review_required,
            "resolution": (
                "coherent" if self.coherent else "human_review_required"
            ),
            "conflicts": tuple(conflict.as_dict() for conflict in self.conflicts),
        }


class CoherenceEngine:
    """Compare shared claims; conflicts remain visible for Human Authority review."""

    def evaluate(
        self,
        statuses: Iterable[Mapping[str, object]],
    ) -> CoherenceReport:
        records = tuple(statuses)
        conflicts: list[CoherenceConflict] = []

        duplicate_ready: dict[str, list[tuple[str, str]]] = defaultdict(list)
        duplicate_mode: dict[str, list[tuple[str, str]]] = defaultdict(list)
        shared_claims: dict[str, list[tuple[str, str]]] = defaultdict(list)

        for index, status in enumerate(records):
            component = str(status.get("component") or f"unknown-{index + 1}")
            if "ready" in status:
                duplicate_ready[component].append((component, repr(status.get("ready"))))
            if "mode" in status:
                duplicate_mode[component].append((component, repr(status.get("mode"))))

            claims = status.get("coherence_claims")
            if isinstance(claims, Mapping):
                for claim, value in claims.items():
                    shared_claims[str(claim)].append((component, repr(value)))

        conflicts.extend(self._find_conflicts("ready", duplicate_ready))
        conflicts.extend(self._find_conflicts("mode", duplicate_mode))
        conflicts.extend(self._find_conflicts("claim", shared_claims))

        conflict_count = len(conflicts)
        checked = len(records)
        uncertainty = min(1.0, conflict_count / max(checked, 1))
        return CoherenceReport(
            coherent=conflict_count == 0,
            checked_components=checked,
            uncertainty=uncertainty,
            human_review_required=conflict_count > 0,
            conflicts=tuple(conflicts),
        )

    @staticmethod
    def _find_conflicts(
        namespace: str,
        grouped: Mapping[str, list[tuple[str, str]]],
    ) -> list[CoherenceConflict]:
        conflicts: list[CoherenceConflict] = []
        for key, entries in grouped.items():
            unique_values = tuple(sorted({value for _, value in entries}))
            if len(unique_values) <= 1:
                continue
            components = tuple(component for component, _ in entries)
            claim = f"{namespace}:{key}" if namespace != "claim" else key
            conflicts.append(
                CoherenceConflict(
                    claim=claim,
                    values=unique_values,
                    components=components,
                )
            )
        return conflicts
