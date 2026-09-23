"""Bounded OAP LAB research proof; no deployment or external side effects."""
from dataclasses import replace

import pytest

from mission_control.oap_lab_research import (
    DOMAINS,
    MISSIONS,
    Evidence,
    Experiment,
    Invention,
    Notebook,
    run_isolated,
)


def notebook(mission="debt_dependency"):
    return Notebook(
        "lab-001", mission, DOMAINS[0],
        "Can this hypothesis be falsified?",
        "The measured synthetic mean changes.",
        "Reject when repeated result differs.",
    )


def experiment(**overrides):
    values = {
        "identifier": "exp-001",
        "notebook_id": "lab-001",
        "operation": "mean",
        "dataset": (2.0, 4.0, 6.0),
        "synthetic": True,
        "human_approved": True,
    }
    values.update(overrides)
    return Experiment(**values)


@pytest.mark.parametrize("mission", MISSIONS)
def test_all_eight_missions_use_one_canonical_contract(mission):
    entry = notebook(mission)
    result = run_isolated(experiment(), entry)
    assert result["mission"] == mission
    assert result["result"] == 4.0
    assert result["scientific_proof"] is False
    assert result["release_authorised"] is False


def test_repeated_runs_are_reproducible_and_receipted():
    first = run_isolated(experiment(), notebook())
    assert first == run_isolated(experiment(), notebook())
    assert len(first["input_sha256"]) == len(first["receipt_sha256"]) == 64


@pytest.mark.parametrize("operation,answer", [
    ("sum", 12.0), ("minimum", 2.0), ("maximum", 6.0)
])
def test_arithmetic_allowlist(operation, answer):
    assert run_isolated(experiment(operation=operation), notebook())["result"] == answer


@pytest.mark.parametrize("change", [
    {"synthetic": False}, {"human_approved": False},
    {"effects": frozenset({"payment"})}, {"effects": frozenset({"external_io"})},
    {"effects": frozenset({"clinical"})}, {"effects": frozenset({"publication"})},
    {"effects": frozenset({"radio_transmit"})}, {"effects": frozenset({"self_modify"})},
])
def test_fail_closed_execution(change):
    with pytest.raises(PermissionError):
        run_isolated(experiment(**change), notebook())


def test_stop_blocks_execution():
    with pytest.raises(PermissionError, match="STOP"):
        run_isolated(experiment(), notebook(), stopped=True)


@pytest.mark.parametrize("change", [
    {"operation": "eval"}, {"operation": "external_io"},
    {"dataset": (float("nan"),)}, {"dataset": (float("inf"),)},
    {"dataset": ()}, {"dataset": ("1",)}, {"dataset": (True,)},
    {"parameters": {"callback": 1.0}},
    {"notebook_id": "wrong"},
])
def test_invalid_input_rejected(change):
    with pytest.raises(ValueError):
        run_isolated(experiment(**change), notebook())


def test_no_unverified_source_promotion():
    with pytest.raises(ValueError):
        Evidence("paper", "claim", "fake-hash")
    with pytest.raises(ValueError):
        replace(notebook(), state="proven")
    with pytest.raises(ValueError):
        Invention("inv-001", "lab-001", "Idea", "Unverified", "Proposed", status="patented")


def test_evidence_and_invention_are_proposals_not_patents():
    source = Evidence("local:source-001", "A test claim", "0" * 64)
    entry = replace(notebook(), evidence=(source,))
    invention = Invention("inv-001", entry.identifier, "Idea", "Proposed novelty", "Synthetic research")
    assert entry.evidence[0].classification == "unverified"
    assert invention.status == "unproven"
