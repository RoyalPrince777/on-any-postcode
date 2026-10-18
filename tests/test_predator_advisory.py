"""Fail-closed contract tests for advisory Predator role metadata."""
from dataclasses import FrozenInstanceError
import pytest
from oap.smi.predator_advisory import ROLES, role

def test_roles_are_unique_and_advisory_only():
    assert len(ROLES) == 7
    assert len({r.role_id for r in ROLES}) == len(ROLES)
    assert all(r.execution_class == "advisory" and not r.sensor_connected for r in ROLES)

def test_unknown_role_has_no_fallback():
    assert role("unknown") is None
    assert role("") is None
    assert role("Jungle_Hunter") is None

def test_role_metadata_is_immutable():
    with pytest.raises(FrozenInstanceError):
        ROLES[0].execution_class = "execute"
