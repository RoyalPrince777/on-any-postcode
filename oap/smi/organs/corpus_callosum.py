"""Merge logical and creative findings into one analysis."""

from __future__ import annotations

from oap.contracts import IntegratedAnalysis, OrganFinding, SignalLevel

_LEVEL_WEIGHT = {
    SignalLevel.WHITE: 0,
    SignalLevel.GREEN: 1,
    SignalLevel.YELLOW: 2,
    SignalLevel.ORANGE: 3,
    SignalLevel.RED: 4,
}


class CorpusCallosum:
    organ_id = "corpus_callosum"

    def merge(self, findings: tuple[OrganFinding, ...]) -> IntegratedAnalysis:
        if not findings:
            raise ValueError("Corpus callosum requires organ findings")
        level = max(
            (item.signal_level for item in findings),
            key=_LEVEL_WEIGHT.__getitem__,
        )
        confidence = sum(item.confidence for item in findings) / len(findings)
        return IntegratedAnalysis(
            summary=(
                f"Merged {len(findings)} internal SMI region findings into one "
                "recommendation context."
            ),
            findings=findings,
            signal_level=level,
            confidence=round(confidence, 3),
        )
