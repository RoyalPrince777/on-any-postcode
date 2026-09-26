import pytest

from mission_control import knowledge_core


def test_knowledge_contract_is_owner_scoped_private_and_complete():
    result = knowledge_core.validate_knowledge_contract()
    assert result["passed"] is True
    assert result["checks"]["tables"] == 10
    assert result["checks"]["private_by_default"] is True
    assert result["checks"]["owner_scoped"] is True


def test_knowledge_card_defaults_private_and_raw():
    card = knowledge_core.KnowledgeCardInput(
        title="Local business trust",
        insight="Proof should precede public claims.",
    ).validated()

    assert card.visibility == "PRIVATE"
    assert card.evidence_state == "RAW"


@pytest.mark.parametrize("state", ["RAW", "SUMMARISED", "SUPPORTED", "CERTIFIED"])
def test_all_evidence_states_are_explicit_and_valid(state):
    card = knowledge_core.KnowledgeCardInput(
        title="A card",
        insight="An insight",
        evidence_state=state,
    ).validated()
    assert card.evidence_state == state


@pytest.mark.parametrize("visibility", ["UNLISTED", "PUBLIC"])
def test_non_private_visibility_requires_human_approval(visibility):
    with pytest.raises(PermissionError, match="human_publication_approval_required"):
        knowledge_core.require_publication_approval(visibility)


def test_private_visibility_needs_no_publication_approval():
    assert knowledge_core.require_publication_approval("PRIVATE") == "PRIVATE"


def test_publication_can_be_explicitly_approved():
    assert (
        knowledge_core.require_publication_approval("PUBLIC", human_approved=True)
        == "PUBLIC"
    )


def test_schema_requires_explicit_human_approval():
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        knowledge_core.init_schema()


def test_schema_approval_only_returns_statements_not_execution():
    statements = knowledge_core.init_schema(human_approved=True)
    assert statements == knowledge_core.KNOWLEDGE_SCHEMA_STATEMENTS


def test_public_contract_preserves_oap_ownership_boundaries():
    contract = knowledge_core.public_contract()
    assert contract["system"] == "OAP Knowledge"
    assert contract["private_surface"] == "The Vault"
    assert contract["owner"] == "My World"
    assert contract["default_visibility"] == "PRIVATE"
    assert contract["registry_owns_provenance"] is True
    assert contract["smi_may_summarise_but_not_silently_certify"] is True
    assert contract["human_approval_before_publication"] is True
    assert contract["private_chain_of_thought_stored"] is False
