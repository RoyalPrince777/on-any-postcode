"""Identity enrichment must never alter existing Alliance selection."""
from oap.smi.alliance_identity_selection import (
    describe_alliance,
    select_identified_alliance,
)
from oap.smi.alliance_selection import AllianceSelection, select_alliance


def test_enrichment_preserves_canonical_selection():
    original = select_alliance("code", "review a failed build")
    described = describe_alliance(original)
    assert described.selection is original
    assert tuple(item.name for item in described.specialists) == original.specialists
    for item in described.specialists:
        if item.identity is not None:
            assert item.identity.motto
            assert item.identity.command


def test_unknown_specialist_is_retained_without_fabricated_identity():
    original = AllianceSelection((), ("Unknown Specialist", "Fox"), ())
    described = describe_alliance(original)
    assert described.specialists[0].identity is None
    assert described.specialists[0].name == "Unknown Specialist"
    assert described.specialists[1].identity.identity == "The Route Master"
    assert described.selection.advisory_only
    assert described.selection.founder_final


def test_selected_identity_is_advisory_only():
    result = select_identified_alliance("code", "review a failed build")
    assert result.selection.advisory_only
    assert result.selection.founder_final
