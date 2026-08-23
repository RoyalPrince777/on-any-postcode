"""Coordinate regions inside the one SMI Brain."""

from __future__ import annotations

from oap.contracts import IntegratedAnalysis, OrganFinding

from .organs import (
    Amygdala,
    Brainstem,
    Cerebellum,
    CorpusCallosum,
    Hippocampus,
    Hypothalamus,
    LeftHemisphere,
    OccipitalLobe,
    ParietalLobe,
    RightHemisphere,
    SyntheticMind,
    TemporalLobe,
)
from .organs.base import BrainPacket


class OrganManager:
    """Run internal regions without duplicating external systems."""

    def __init__(self) -> None:
        self._analysis_organs = (
            LeftHemisphere(),
            RightHemisphere(),
            ParietalLobe(),
            TemporalLobe(),
            OccipitalLobe(),
            Hypothalamus(),
            Hippocampus(),
            Amygdala(),
            Cerebellum(),
            Brainstem(),
            SyntheticMind(),
        )
        self.corpus_callosum = CorpusCallosum()

    def run_regions(self, packet: BrainPacket) -> tuple[OrganFinding, ...]:
        return tuple(organ.analyse(packet) for organ in self._analysis_organs)

    def integrate(self, findings: tuple[OrganFinding, ...]) -> IntegratedAnalysis:
        return self.corpus_callosum.merge(findings)

    def status(self) -> dict[str, object]:
        internal_regions = tuple(organ.organ_id for organ in self._analysis_organs)
        return {
            "component": "SMI Organ Manager",
            "ready": True,
            "analysis_regions": internal_regions,
            "integration_region": self.corpus_callosum.organ_id,
            "brain_count": 1,
        }
