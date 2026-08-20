"""Shared packet and helpers for SMI biological regions."""

from __future__ import annotations

from dataclasses import dataclass

from oap.contracts import (
    AdvisorSelection,
    ContextSnapshot,
    FocusedSignal,
    OrganFinding,
    ProviderResult,
    SignalLevel,
)


@dataclass(frozen=True, slots=True)
class BrainPacket:
    signal: FocusedSignal
    context: ContextSnapshot
    advisors: AdvisorSelection
    provider_results: tuple[ProviderResult, ...]


def finding(
    organ_id: str,
    summary: str,
    confidence: float,
    *tags: str,
    signal_level: SignalLevel = SignalLevel.GREEN,
) -> OrganFinding:
    return OrganFinding(
        organ_id=organ_id,
        summary=summary,
        confidence=max(0.0, min(confidence, 1.0)),
        tags=tuple(tags),
        signal_level=signal_level,
    )
