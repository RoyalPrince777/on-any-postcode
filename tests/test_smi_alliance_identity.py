"""Identity overlay must not alter canonical SMI authority or selection."""
from dataclasses import FrozenInstanceError

import pytest

from oap.smi.alliance_identity import ALLIANCE_IDENTITIES, get_alliance_identity


def test_alliance_identity_contract_is_complete():
    assert len(ALLIANCE_IDENTITIES) == 34
    for agent_id, agent in ALLIANCE_IDENTITIES.items():
        assert agent_id
        assert all(isinstance(value, str) and value.strip() for value in vars(agent).values())


def test_brothers_remain_distinct():
    tank = get_alliance_identity("TANK")
    dozer = get_alliance_identity("dozer")
    assert tank.family == dozer.family == "Brothers"
    assert tank.motto == "Nothing breaks us."
    assert dozer.motto == "Nothing stops progress."
    assert tank.primary_role != dozer.primary_role
    assert tank.command == "Gorilla"


def test_unknown_agent_does_not_gain_authority():
    assert get_alliance_identity("unregistered") is None
    assert get_alliance_identity(None) is None


def test_identity_metadata_is_immutable():
    with pytest.raises(FrozenInstanceError):
        get_alliance_identity("tank").command = "self-authorised"


def test_twins_independently_define_and_verify():
    expected = get_alliance_identity("twin_one")
    observed = get_alliance_identity("twin_two")
    assert expected.family == observed.family == "Matrix"
    assert expected.primary_role != observed.primary_role
    assert expected.motto == "Define what must be true."
    assert observed.motto == "Prove what is true."
    assert "Independent" in observed.command
