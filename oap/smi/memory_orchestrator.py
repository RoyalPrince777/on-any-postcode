"""Governed memory composition for SMI.

Canonical truth outranks history. History explains evolution. The knowledge graph
adds relationships. Recent audited HRM memory adds current working context. The
combined context is always bounded to 21 items.
"""

from __future__ import annotations

from collections.abc import Iterable

from oap.contracts import MemoryItem

from .canonical_memory import canonical_memory_items
from .canonical_memory import status as canonical_status
from .knowledge_graph import graph_memory_items
from .knowledge_graph import status as graph_status
from .memory_history import historical_memory_items
from .memory_history import status as history_status

TOTAL_CONTEXT_CAP = 21
CANONICAL_BUDGET = 10
HISTORY_BUDGET = 4
GRAPH_BUDGET = 3
DYNAMIC_BUDGET = 4


def compose_memory(
    task_type: str | None,
    *,
    query: str = "",
    dynamic: Iterable[MemoryItem] = (),
    limit: int = TOTAL_CONTEXT_CAP,
) -> tuple[MemoryItem, ...]:
    """Compose bounded memory in descending authority order."""

    safe_limit = min(max(int(limit), 1), TOTAL_CONTEXT_CAP)
    canonical = canonical_memory_items(task_type, limit=CANONICAL_BUDGET)
    history = historical_memory_items(task_type, limit=HISTORY_BUDGET)
    graph = graph_memory_items(task_type, query=query, limit=GRAPH_BUDGET)
    recent_dynamic = tuple(dynamic)[-DYNAMIC_BUDGET:]
    return (canonical + history + graph + recent_dynamic)[:safe_limit]


def compose_text_memory(
    task_type: str | None,
    *,
    query: str = "",
    dynamic: Iterable[str] = (),
    limit: int = TOTAL_CONTEXT_CAP,
) -> tuple[str, ...]:
    """Text-only equivalent for the live generation provider."""

    safe_limit = min(max(int(limit), 1), TOTAL_CONTEXT_CAP)
    recent_dynamic = tuple(str(item)[:600] for item in dynamic)[-DYNAMIC_BUDGET:]
    if len(recent_dynamic) > safe_limit:
        recent_dynamic = recent_dynamic[-safe_limit:]
    static_limit = safe_limit - len(recent_dynamic)
    static = (
        compose_memory(task_type, query=query, dynamic=(), limit=static_limit)
        if static_limit > 0
        else ()
    )
    return tuple(item.summary for item in static) + recent_dynamic


def status() -> dict[str, object]:
    canonical = canonical_status()
    history = history_status()
    graph = graph_status()
    return {
        "component": "SMI Memory Orchestrator",
        "ready": bool(
            canonical.get("ready") and history.get("ready") and graph.get("ready")
        ),
        "context_cap": TOTAL_CONTEXT_CAP,
        "canonical_budget": CANONICAL_BUDGET,
        "historical_budget": HISTORY_BUDGET,
        "graph_budget": GRAPH_BUDGET,
        "dynamic_hrm_budget": DYNAMIC_BUDGET,
        "authority_order": (
            "CANONICAL",
            "HISTORICAL_CONTEXT",
            "KNOWLEDGE_GRAPH",
            "AUDITED_HRM_WORKING_MEMORY",
        ),
        "latest_founder_correction_wins": True,
        "raw_chat_dump": False,
        "human_authority_final": True,
    }
