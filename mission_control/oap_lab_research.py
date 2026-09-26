"""OAP LAB isolated research records and synthetic-only experiment engine.

This is an opt-in domain module, not an HTTP route, migration, financial
service, medical service or alternate SMI brain. The caller owns authentication
and persistence. Nothing in this module writes to a database or network.
"""
from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

MISSIONS = (
    "debt_dependency", "digital_identity", "future_communications",
    "sustainable_energy", "health_longevity", "space_intelligence",
    "smi_research", "all_21_domains",
)
DOMAINS = (
    "artificial_intelligence", "communications", "isac", "physics", "energy",
    "biology", "human_intelligence", "nature", "robotics", "spatial",
    "scientific_discovery", "space", "futures", "materials", "health",
    "food_agriculture", "water_climate", "mobility", "economics",
    "security_privacy", "civilization",
)
PROHIBITED = frozenset({
    "payment", "banking", "clinical", "human_subject",
    "radio_transmit", "deployment", "publication", "self_modify",
    "external_io", "live_execution",
})


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(raw.encode("utf-8")).hexdigest()


def _required(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} required")
    return value.strip()


@dataclass(frozen=True)
class Evidence:
    source: str
    claim: str
    sha256: str
    classification: str = "unverified"

    def __post_init__(self) -> None:
        _required(self.source, "source")
        _required(self.claim, "claim")
        if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256):
            raise ValueError("source SHA-256 required")
        if self.classification not in ("unverified", "observed", "inferred", "challenged"):
            raise ValueError("unsupported evidence classification")


@dataclass(frozen=True)
class Notebook:
    identifier: str
    mission: str
    domain: str
    question: str
    hypothesis: str
    falsification: str
    evidence: tuple[Evidence, ...] = ()
    state: str = "research_draft"

    def __post_init__(self) -> None:
        _required(self.identifier, "identifier")
        _required(self.question, "question")
        _required(self.hypothesis, "hypothesis")
        _required(self.falsification, "falsification")
        if self.mission not in MISSIONS or self.domain not in DOMAINS:
            raise ValueError("unknown mission or domain")
        if self.state != "research_draft":
            raise ValueError("research notebook cannot assert approval or proof")
        if any(not isinstance(e, Evidence) for e in self.evidence):
            raise ValueError("invalid evidence")


@dataclass(frozen=True)
class Invention:
    identifier: str
    notebook_id: str
    title: str
    claimed_novelty: str
    proposed_use: str
    status: str = "unproven"

    def __post_init__(self) -> None:
        for name in ("identifier", "notebook_id", "title", "claimed_novelty", "proposed_use"):
            _required(getattr(self, name), name)
        if self.status != "unproven":
            raise ValueError("an invention proposal is not proof, a patent or a licence")


@dataclass(frozen=True)
class Experiment:
    identifier: str
    notebook_id: str
    operation: str
    dataset: tuple[float, ...]
    parameters: Mapping[str, float] = field(default_factory=dict)
    effects: frozenset[str] = frozenset()
    synthetic: bool = False
    human_approved: bool = False

    def __post_init__(self) -> None:
        _required(self.identifier, "identifier")
        _required(self.notebook_id, "notebook_id")


def run_isolated(experiment: Experiment, notebook: Notebook, *, stopped: bool = False) -> dict[str, Any]:
    """Run only deterministic arithmetic on explicitly synthetic input.

    human_approved denotes bounded design authorisation, NOT clinical,
    financial, publication, merge or deployment permission.
    """
    if type(stopped) is not bool:
        raise PermissionError("explicit STOP state required")
    if stopped:
        raise PermissionError("STOP: experiment not run")
    if not isinstance(experiment, Experiment) or not isinstance(notebook, Notebook):
        raise TypeError("typed laboratory records required")
    if experiment.notebook_id != notebook.identifier:
        raise ValueError("notebook reference mismatch")
    if experiment.synthetic is not True or experiment.human_approved is not True:
        raise PermissionError("synthetic data and bounded human approval required")
    if experiment.effects or experiment.effects.intersection(PROHIBITED):
        raise PermissionError("side effects forbidden in isolated experiment")
    if experiment.operation not in ("mean", "sum", "minimum", "maximum"):
        raise ValueError("operation not allowlisted")
    if experiment.parameters:
        raise ValueError("parameters are not executable instructions")
    if not experiment.dataset or len(experiment.dataset) > 10000:
        raise ValueError("dataset must contain 1..10000 values")
    if any(type(x) not in (float, int) or not math.isfinite(x) for x in experiment.dataset):
        raise ValueError("finite numeric synthetic values only")
    values = experiment.dataset
    try:
        result = {
            "mean": lambda: math.fsum(values) / len(values),
            "sum": lambda: math.fsum(values),
            "minimum": lambda: min(values),
            "maximum": lambda: max(values),
        }[experiment.operation]()
    except (OverflowError, ValueError) as exc:
        raise ValueError("synthetic_result_not_representable") from exc
    if not math.isfinite(result):
        raise ValueError("synthetic_result_not_representable")
    receipt = {
        "experiment_id": experiment.identifier,
        "notebook_id": notebook.identifier,
        "mission": notebook.mission,
        "operation": experiment.operation,
        "sample_size": len(values),
        "input_sha256": _digest(list(values)),
        "result": result,
        "synthetic": True,
        "scope": "isolated_arithmetic_only",
        "research_state": "unverified_experiment_result",
        "scientific_proof": False,
        "release_authorised": False,
    }
    return {**receipt, "receipt_sha256": _digest(receipt)}
