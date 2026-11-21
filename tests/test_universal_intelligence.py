"""Universal SMI growth records remain advisory and fail closed."""
from oap.smi.universal_intelligence import PROTOCOL, advisory_growth_record

import pytest


EVIDENCE = {"source": "review", "reference": "case-1", "observation": "observed"}


def test_cross_specialist_capability_does_not_change_owner():
    result = advisory_growth_record(agent="Hathi", capability="memory_reconstruction",
                                    evidence=EVIDENCE, shared_from="Elephant")
    assert result["accountable_lead"] == "Elephant"
    assert result["agent"] == "Hathi"
    assert result["shared_from"] == "Elephant"


def test_learning_and_promotion_not_faked():
    result = advisory_growth_record(agent="Bagheera", capability="agent_governance",
                                    evidence=EVIDENCE)
    assert result["learning_verified"] is False
    assert result["rank_change"] is None
    assert result["production_gate"] == "blocked"
    assert result["founder_final"] is True


def test_missing_evidence_fails_closed():
    with pytest.raises(ValueError):
        advisory_growth_record(agent="Hathi", capability="memory_reconstruction", evidence={})


def test_no_exclusive_owner_for_unmapped_capability():
    result = advisory_growth_record(agent="Tigress", capability="adaptive_timing",
                                    evidence=EVIDENCE)
    assert result["accountable_lead"] is None
    assert result["guardian_review_required"] is True


def test_protocol_has_universal_guards():
    assert "guardian_and_founder_final" in PROTOCOL
    assert "evidence_before_promotion" in PROTOCOL
