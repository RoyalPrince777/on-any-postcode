"""Governed memory composition for SMI.

Latest explicit Founder locks outrank older canonical truth. History explains
evolution, the knowledge graph adds relationships, the audited Founder channel
carries explicit approved imports, live operational memory supplies privacy-reduced
OAP state, and recent HRM adds working context. The combined context stays bounded
to 21 items.
"""

from __future__ import annotations

from collections.abc import Iterable

from oap.contracts import MemoryItem

from .canonical_memory import canonical_memory_items
from .canonical_memory import status as canonical_status
from .founder_memory_channel import status as founder_channel_status
from .founder_memory_channel import synced_memory_items
from .knowledge_graph import graph_memory_items
from .knowledge_graph import status as graph_status
from .latest_founder_memory import latest_founder_memory_items
from .latest_founder_memory import status as latest_founder_status
from .memory_history import historical_memory_items
from .memory_history import status as history_status
from .operational_memory import operational_memory_items
from .operational_memory import status as operational_status

TOTAL_CONTEXT_CAP = 21
LATEST_FOUNDER_BUDGET = 4
CANONICAL_BUDGET = 6
HISTORY_BUDGET = 2
GRAPH_BUDGET = 1
FOUNDER_SYNC_BUDGET = 2
OPERATIONAL_BUDGET = 3
DYNAMIC_BUDGET = 3


def compose_memory(
    task_type: str | None,
    *,
    query: str = "",
    dynamic: Iterable[MemoryItem] = (),
    limit: int = TOTAL_CONTEXT_CAP,
) -> tuple[MemoryItem, ...]:
    """Compose bounded memory in descending authority order."""

    safe_limit = min(max(int(limit), 1), TOTAL_CONTEXT_CAP)
    latest_founder = latest_founder_memory_items(limit=LATEST_FOUNDER_BUDGET)
    canonical = canonical_memory_items(task_type, limit=CANONICAL_BUDGET)
    history = historical_memory_items(task_type, limit=HISTORY_BUDGET)
    graph = graph_memory_items(task_type, query=query, limit=GRAPH_BUDGET)
    founder_sync = synced_memory_items(
        task_type,
        query=query,
        limit=FOUNDER_SYNC_BUDGET,
    )
    operational = operational_memory_items(
        task_type,
        query=query,
        limit=OPERATIONAL_BUDGET,
    )
    recent_dynamic = tuple(dynamic)[-DYNAMIC_BUDGET:]
    return (
        latest_founder
        + canonical
        + history
        + graph
        + founder_sync
        + operational
        + recent_dynamic
    )[:safe_limit]


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
    latest_founder = latest_founder_status()
    canonical = canonical_status()
    history = history_status()
    graph = graph_status()
    founder_channel = founder_channel_status()
    operational = operational_status()
    budget_total = (
        LATEST_FOUNDER_BUDGET
        + CANONICAL_BUDGET
        + HISTORY_BUDGET
        + GRAPH_BUDGET
        + FOUNDER_SYNC_BUDGET
        + OPERATIONAL_BUDGET
        + DYNAMIC_BUDGET
    )
    return {
        "component": "SMI Memory Orchestrator",
        "ready": bool(
            latest_founder.get("ready")
            and canonical.get("ready")
            and history.get("ready")
            and graph.get("ready")
            and founder_channel.get("ready")
            and operational.get("ready")
            and budget_total == TOTAL_CONTEXT_CAP
        ),
        "context_cap": TOTAL_CONTEXT_CAP,
        "budget_total": budget_total,
        "latest_founder_budget": LATEST_FOUNDER_BUDGET,
        "canonical_budget": CANONICAL_BUDGET,
        "historical_budget": HISTORY_BUDGET,
        "graph_budget": GRAPH_BUDGET,
        "founder_sync_budget": FOUNDER_SYNC_BUDGET,
        "operational_memory_budget": OPERATIONAL_BUDGET,
        "dynamic_hrm_budget": DYNAMIC_BUDGET,
        "latest_founder_memory": latest_founder,
        "authority_order": (
            "LATEST_FOUNDER_LOCK",
            "CANONICAL",
            "HISTORICAL_CONTEXT",
            "KNOWLEDGE_GRAPH",
            "FOUNDER_APPROVED_SYNC_CONTEXT",
            "LIVE_OPERATIONAL_MEMORY",
            "AUDITED_HRM_WORKING_MEMORY",
        ),
        "operational_memory": operational,
        "all_governed_memory_sources_connected": True,
        "latest_founder_correction_wins": True,
        "raw_chat_dump": False,
        "raw_database_dump": False,
        "github_memory_channel_connected": bool(
            founder_channel.get("github_audited_transport_connected")
        ),
        "direct_chatgpt_http_connected": False,
        "human_authority_final": True,
    }
