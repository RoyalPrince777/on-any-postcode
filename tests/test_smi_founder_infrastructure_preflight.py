"""Fail-closed SMI preflight for existing Founder infrastructure readers.

No network calls, credentials or provider mutations are exercised.
"""

import pytest

from mission_control.founder_neon import FounderNeonReadAdapter
from mission_control.founder_render import FounderRenderReadAdapter
from oap.registry.tools import ToolRegistry


@pytest.mark.parametrize(
    ("adapter_class", "approved_ability"),
    [
        (FounderRenderReadAdapter, "service.read"),
        (FounderNeonReadAdapter, "schema.read"),
    ],
)
def test_approved_read_preflight(adapter_class, approved_ability) -> None:
    adapter = adapter_class(token="")
    adapter._authorize(approved_ability)


@pytest.mark.parametrize("adapter_class", [FounderRenderReadAdapter, FounderNeonReadAdapter])
def test_unknown_ability_denied(adapter_class) -> None:
    adapter = adapter_class(token="")
    with pytest.raises(PermissionError):
        adapter._authorize("secrets.export")


@pytest.mark.parametrize("adapter_class", [FounderRenderReadAdapter, FounderNeonReadAdapter])
def test_disabled_registry_denied(adapter_class) -> None:
    adapter = adapter_class(token="")
    adapter._registry = ToolRegistry()
    with pytest.raises(PermissionError):
        adapter._authorize("schema.read")
