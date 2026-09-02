"""Governed tool capabilities for the Founder workspace.

This extends OAP Registry with tool metadata only. It never holds credentials,
invokes providers, approves actions, or bypasses Living Kernel/Builder.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ToolCapability:
    tool_id: str
    name: str
    category: str
    abilities: tuple[str, ...]
    read_only: bool = True
    requires_human_approval: bool = True
    requires_kernel: bool = True
    enabled: bool = True

    @property
    def can_execute_independently(self) -> bool:
        return False


class ToolRegistry:
    """Immutable allow-list of capabilities exposed to OAP Mind.

    Read capabilities may be routed by an authenticated workspace adapter.
    Every mutation remains a proposed action until Human Authority approval and
    Living Kernel/Builder execution. Credentials are deliberately external.
    """

    def __init__(self, tools: Iterable[ToolCapability] = ()) -> None:
        self._tools = tuple(tools)
        self._validate()

    def _validate(self) -> None:
        ids = [tool.tool_id.strip().casefold() for tool in self._tools]
        names = [tool.name.strip().casefold() for tool in self._tools]
        if any(not value for value in ids + names):
            raise ValueError("Tool identifiers and names must be non-empty")
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate tool identifiers")
        if len(names) != len(set(names)):
            raise ValueError("Duplicate tool names")
        for tool in self._tools:
            if not tool.abilities:
                raise ValueError(f"Tool {tool.tool_id} must declare abilities")
            if not tool.read_only and not (tool.requires_human_approval and tool.requires_kernel):
                raise ValueError("Mutable tools must require Human Authority and Living Kernel")

    def capability(self, tool_id: str) -> ToolCapability | None:
        wanted = str(tool_id or "").strip().casefold()
        return next((tool for tool in self._tools if tool.tool_id.casefold() == wanted), None)

    def available(self, *, category: str | None = None) -> tuple[ToolCapability, ...]:
        wanted = str(category or "").strip().casefold()
        return tuple(
            tool for tool in self._tools
            if tool.enabled and (not wanted or tool.category.casefold() == wanted)
        )

    def authorize_capability(self, tool_id: str, ability: str, *, mutation: bool = False) -> ToolCapability:
        tool = self.capability(tool_id)
        if tool is None or not tool.enabled:
            raise LookupError("Tool capability is not approved")
        requested = str(ability or "").strip().casefold()
        if requested not in {item.casefold() for item in tool.abilities}:
            raise PermissionError("Requested tool ability is not approved")
        if mutation and tool.read_only:
            raise PermissionError("Read-only tool cannot perform mutations")
        if mutation and not (tool.requires_human_approval and tool.requires_kernel):
            raise PermissionError("Mutation is not governed by Human Authority and Living Kernel")
        return tool

    def status(self) -> dict[str, object]:
        enabled = self.available()
        mutable = tuple(tool.tool_id for tool in enabled if not tool.read_only)
        return {
            "component": "Registry / Founder Tools",
            "ready": True,
            "tools": len(self._tools),
            "enabled_tools": len(enabled),
            "mutable_tools": mutable,
            "credentials_stored": False,
            "independent_execute": False,
            "human_authority_final": True,
            "kernel_required_for_mutation": True,
        }


def founder_tool_registry() -> ToolRegistry:
    """Canonical initial Founder capabilities; adapters are connected separately."""
    return ToolRegistry(
        (
            ToolCapability(
                tool_id="github",
                name="GitHub",
                category="code",
                abilities=("repo.read", "code.search", "file.read", "diff.read", "branch.create", "file.write", "pr.create", "pr.merge"),
                read_only=False,
            ),
            ToolCapability(
                tool_id="render",
                name="Render",
                category="infrastructure",
                abilities=("service.read", "deploy.read", "logs.read", "metrics.read", "deploy.trigger"),
                read_only=False,
            ),
            ToolCapability(
                tool_id="postgres",
                name="Postgres",
                category="data",
                abilities=("schema.read", "query.read", "migration.propose", "migration.apply"),
                read_only=False,
            ),
        )
    )
