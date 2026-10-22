"""Queen Bee / Bee Swarm: fail-closed, advisory task assignment contracts.

No workers are launched, no cross-family access is granted, and Honey is
coordination metadata only. Execution must be authorised by a separate gate.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SwarmTask:
    task_id: str
    home_family: str
    requested_by: str
    capability: str
    allowed_sources: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class SwarmPlan:
    assignments: tuple[SwarmTask, ...]
    honey_receipts: tuple[str, ...]
    advisory_only: bool = True
    authority_granted: bool = False
    workers_started: bool = False
    family_ownership_unchanged: bool = True


def plan_swarm(tasks: tuple[SwarmTask, ...], *, distributed_work: bool = False) -> SwarmPlan:
    """Plan only explicit, independent, bounded tasks; never execute them."""
    if not distributed_work or not tasks:
        return SwarmPlan((), ())
    seen: set[str] = set()
    for task in tasks:
        if not task.task_id or not task.home_family or not task.requested_by or not task.capability:
            raise ValueError("Swarm tasks require identity, home family, requester and capability")
        if task.task_id in seen or task.task_id in task.depends_on:
            raise ValueError("Duplicate or self-dependent swarm task")
        seen.add(task.task_id)
    if any(dependency not in seen for task in tasks for dependency in task.depends_on):
        raise ValueError("Unknown swarm task dependency")
    return SwarmPlan(tasks, tuple(f"honey:planned:{task.task_id}" for task in tasks))
