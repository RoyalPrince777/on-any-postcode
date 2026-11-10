"""Bounded adapter tests: preflight precedes any GitHub provider request."""

import pytest

from mission_control.founder_github import FounderGitHubReadAdapter
from oap.registry.tools import ToolRegistry


def test_founder_github_read_is_preflighted_without_network() -> None:
    adapter = FounderGitHubReadAdapter(token="")
    adapter._authorize("repo.read")


def test_founder_github_unknown_ability_fails_closed() -> None:
    adapter = FounderGitHubReadAdapter(token="")
    with pytest.raises(PermissionError):
        adapter._authorize("secrets.export")


def test_founder_github_disabled_registry_fails_closed() -> None:
    adapter = FounderGitHubReadAdapter(token="")
    adapter._registry = ToolRegistry()
    with pytest.raises(PermissionError):
        adapter._authorize("repo.read")
