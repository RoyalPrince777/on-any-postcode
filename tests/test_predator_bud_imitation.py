"""Bud imitation must fail closed and never copy execution authority."""
from oap.smi.predator_bud_imitation import Procedure, imitate


def test_verified_successful_first_party_example_requires_review():
    proposal = imitate(Procedure("fix-1", "first_party", ("Inspect logs", "Check tests"), "success", True))
    assert proposal.decision == "HUMAN_REVIEW"
    assert proposal.steps == ("Inspect logs", "Check tests")
    assert proposal.executable is False


def test_missing_or_unverified_examples_denied():
    assert imitate(None).decision == "DENY"
    for example in (
        Procedure("fix-1", "external", ("Inspect",), "success", True),
        Procedure("fix-1", "first_party", ("Inspect",), "failure", True),
        Procedure("fix-1", "first_party", ("Inspect",), "success", False),
        Procedure("fix-1", "first_party", (), "success", True),
        Procedure("fix-1", "first_party", ("",), "success", True),
        Procedure("", "first_party", ("Inspect",), "success", True),
    ):
        assert imitate(example).decision == "DENY"
