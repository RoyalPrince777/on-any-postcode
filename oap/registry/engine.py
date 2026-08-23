"""Agent selection without creating agents, roles or provider assignments."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from oap.contracts import AdvisorSelection
from oap.permissions import PermissionEngine


def _normalise(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).casefold())


class RegistryEngine:
    """Immutable view over the approved registry supplied at startup."""

    def __init__(
        self,
        agents: Iterable[Mapping[str, Any]],
        family_ids: Iterable[str],
    ) -> None:
        self._agents = tuple(dict(agent) for agent in agents)
        self._family_ids = frozenset(family_ids)
        self._permission_engine = PermissionEngine()
        self._validate()

    def _validate(self) -> None:
        if len(self._family_ids) == 0:
            raise ValueError("At least one Intelligence family is required")
        ids = [_normalise(agent.get("agent_id", "")) for agent in self._agents]
        names = [
            _normalise(label)
            for agent in self._agents
            for label in (agent.get("name", ""), *(agent.get("aliases") or ()))
        ]
        if any(not value for value in ids) or any(not value for value in names):
            raise ValueError("Agent identifiers, names and aliases must be non-empty")
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate agent identifiers")
        if len(names) != len(set(names)):
            raise ValueError("Duplicate agent names or aliases")
        if any(agent.get("family_id") not in self._family_ids for agent in self._agents):
            raise ValueError("Agent belongs to an unknown Intelligence family")
        if any(name == "kaa" for name in names):
            raise ValueError("Kaa is not approved in the OAP Agent Registry")

        approved_roles = [
            _normalise(agent.get("role"))
            for agent in self._agents
            if agent.get("role_status") == "Approved" and agent.get("role")
        ]
        if len(approved_roles) != len(set(approved_roles)):
            raise ValueError("Duplicate approved agent roles")
        prohibited = [
            label
            for agent in self._agents
            for label in (agent.get("name", ""), *(agent.get("aliases") or ()))
            if _normalise(label) == "kaa" or "council" in str(label).casefold()
        ]
        if prohibited:
            raise ValueError("Prohibited or legacy agent naming conflict")

    def select_advisors(self, task_type: str) -> AdvisorSelection:
        requested_task = str(task_type or "GENERAL").strip().upper()
        selected: list[str] = []
        for agent in self._agents:
            supported_tasks = {
                str(value).strip().upper()
                for value in agent.get("task_types", ())
            }
            is_default_coordinator = agent.get("agent_id") == "NEO-001"
            if not is_default_coordinator and requested_task not in supported_tasks:
                continue
            decision = self._permission_engine.authorize_agent(
                agent,
                required_permission="ANALYSE",
            )
            if decision.allowed:
                selected.append(decision.identity)
        return AdvisorSelection(
            agent_ids=tuple(selected),
            reason=(
                "Bounded autonomous advisors selected by approved task family"
                if selected
                else "No bounded autonomous advisory assignment"
            ),
        )

    def passport(self, agent_id: str) -> dict[str, Any] | None:
        agent = next(
            (item for item in self._agents if item.get("agent_id") == agent_id),
            None,
        )
        return dict(agent) if agent else None

    def status(self) -> dict[str, object]:
        active = sum(agent.get("status") == "ACTIVE" for agent in self._agents)
        provider_assignments = sum(
            bool(agent.get("provider_ids")) for agent in self._agents
        )
        bounded_autonomous = sum(
            agent.get("autonomy", {}).get("mode") == "BOUNDED_ADVISORY"
            and agent.get("autonomy", {}).get("can_execute") is False
            for agent in self._agents
        )
        return {
            "component": "Registry",
            "ready": True,
            "agents": len(self._agents),
            "active_agents": active,
            "families": len(self._family_ids),
            "provider_assignments": provider_assignments,
            "bounded_autonomous_agents": bounded_autonomous,
            "independent_execute": False,
            "final_authority": "Human Authority",
        }
