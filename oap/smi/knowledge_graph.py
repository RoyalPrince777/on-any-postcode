"""Small first-party knowledge graph for canonical OAP relationships.

The graph improves relational recall without turning every prompt into a dump of
project history. It stores systems, products and concepts rather than people.
"""

from __future__ import annotations

from datetime import datetime, timezone

from oap.contracts import MemoryItem, OutputState

GRAPH_REVISION = "2026-09-04-v1"
_GRAPH_TIMESTAMP = datetime(2026, 9, 4, tzinfo=timezone.utc)

_EDGES: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    ("Human Authority", "final_authority_over", "SMI", ("GENERAL", "TECHNICAL", "STRATEGY")),
    ("OAP Core", "connects_into", "Nexus", ("GENERAL", "TECHNICAL")),
    ("Nexus", "routes_context_to", "Thalamus", ("GENERAL", "TECHNICAL")),
    ("Thalamus", "routes_within", "SMI Brain", ("GENERAL", "TECHNICAL")),
    ("SMI Brain", "contains_world", "Matrix", ("GENERAL", "TECHNICAL")),
    ("Nexus", "is", "Connective Nervous System", ("GENERAL", "TECHNICAL")),
    ("Oasis", "is", "Human Experience Environment", ("GENERAL", "COMMUNITY", "TECHNICAL")),
    ("Matrix", "is", "Spatial World-State Intelligence", ("GENERAL", "TECHNICAL")),
    ("Matrix Intelligence Agents", "live_inside", "Matrix System", ("GENERAL", "TECHNICAL")),
    ("Nirmata", "belongs_to", "Civilisation Intelligence", ("GENERAL", "TECHNICAL", "STRATEGY")),
    ("Nirmata", "role", "Creation Architect", ("GENERAL", "TECHNICAL", "STRATEGY")),
    ("OAP Maps", "human_interface_for", "OAP Spatial Core", ("GENERAL", "TECHNICAL", "COMMUNITY")),
    ("OAP Spatial Core", "feeds", "Matrix", ("GENERAL", "TECHNICAL")),
    ("Matrix", "provides_world_state_to", "OAP Maps", ("GENERAL", "TECHNICAL", "COMMUNITY")),
    ("HRM", "provides", "Temporal Memory", ("GENERAL", "TECHNICAL")),
    ("Guardian", "governs", "Matrix RF Intelligence", ("GENERAL", "TECHNICAL", "MONITORING")),
    ("Matrix RF Intelligence", "belongs_inside", "Matrix", ("GENERAL", "TECHNICAL", "MONITORING")),
    ("OAP Maps 2D", "means", "Street", ("GENERAL", "TECHNICAL", "COMMUNITY")),
    ("OAP Maps 3D", "means", "World", ("GENERAL", "TECHNICAL", "COMMUNITY")),
    ("OAP Maps 4D", "means", "Time", ("GENERAL", "TECHNICAL", "COMMUNITY")),
    ("OAP Maps 5D", "means", "Intelligence Context", ("GENERAL", "TECHNICAL", "COMMUNITY")),
    ("OAP Cockpit", "is_separate_presentation_of", "OAP Maps", ("GENERAL", "TECHNICAL", "COMMUNITY")),
    ("OAP World", "is", "Public Front Door", ("GENERAL", "COMMUNITY", "STRATEGY")),
    ("The Spot", "belongs_to", "OAP World Ecosystem", ("GENERAL", "COMMUNITY")),
    ("Pulse", "means", "Feed", ("GENERAL", "COMMUNITY")),
    ("Signal", "means", "News", ("GENERAL", "COMMUNITY")),
    ("The Link", "means", "Opportunities", ("GENERAL", "COMMUNITY")),
    ("Link Up", "lives_inside", "The Link", ("GENERAL", "COMMUNITY")),
    ("My Card", "is_presented_by", "Profile Stage", ("GENERAL", "COMMUNITY")),
    ("SIKA", "is", "Currency Value System", ("GENERAL", "STRATEGY")),
    ("SIKA", "is_distinct_from", "United States of Africa Royalty Bank", ("GENERAL", "STRATEGY")),
    ("SIKA", "is_distinct_from", "Future UK Banking Institution", ("GENERAL", "STRATEGY")),
    ("United States of Africa Royalty Bank", "faces", "Africa", ("GENERAL", "STRATEGY")),
    ("Future UK Banking Institution", "requires", "Separate UK Legal Entity", ("GENERAL", "STRATEGY")),
    ("OAP Network Core", "controls", "Mobile Core", ("GENERAL", "TECHNICAL")),
    ("OAP Radio Access", "controls", "RAN Identity", ("GENERAL", "TECHNICAL")),
    ("OAP Edge", "supports", "Local Compute", ("GENERAL", "TECHNICAL")),
    ("OAP 6G/7G Lab", "researches", "6G", ("GENERAL", "TECHNICAL", "STRATEGY")),
    ("OAP 6G/7G Lab", "researches", "7G", ("GENERAL", "TECHNICAL", "STRATEGY")),
    ("6G", "may_graduate_to", "Operational Connectivity", ("GENERAL", "TECHNICAL", "STRATEGY")),
    ("7G", "remains", "Long-Horizon Research", ("GENERAL", "TECHNICAL", "STRATEGY")),
    ("Open5GS", "may_foundation", "OAP Mobile Core", ("TECHNICAL", "STRATEGY")),
    ("OAI", "may_foundation", "OAP Radio Research", ("TECHNICAL", "STRATEGY")),
    ("Osmocom", "may_foundation", "OAP Legacy Cellular Compatibility", ("TECHNICAL", "STRATEGY")),
    ("OCUDU/srsRAN lineage", "may_foundation", "OAP RAN", ("TECHNICAL", "STRATEGY")),
    ("Postcode", "rolls_up_to", "Borough", ("GENERAL", "COMMUNITY", "TECHNICAL")),
    ("Borough", "rolls_up_to", "County/Region", ("GENERAL", "COMMUNITY", "TECHNICAL")),
    ("County/Region", "rolls_up_to", "Country", ("GENERAL", "COMMUNITY", "TECHNICAL")),
    ("Country", "rolls_up_to", "Continent", ("GENERAL", "COMMUNITY", "TECHNICAL")),
    ("Continent", "rolls_up_to", "Global", ("GENERAL", "COMMUNITY", "TECHNICAL")),
    ("Global", "rolls_up_to", "Beyond", ("GENERAL", "COMMUNITY", "TECHNICAL")),
)


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in value.casefold().replace("/", " ").replace("-", " ").split()
        if len(token) > 2
    }


def graph_memory_items(
    task_type: str | None = None,
    *,
    query: str = "",
    limit: int = 4,
) -> tuple[MemoryItem, ...]:
    """Return compact relationship statements relevant to task/query."""

    task = str(task_type or "GENERAL").strip().upper() or "GENERAL"
    safe_limit = min(max(int(limit), 1), 8)
    query_tokens = _tokens(query)
    candidates: list[tuple[int, int, tuple[str, str, str, tuple[str, ...]]]] = []
    for index, edge in enumerate(_EDGES):
        subject, relation, obj, scopes = edge
        if task not in scopes and "GENERAL" not in scopes:
            continue
        edge_tokens = _tokens(f"{subject} {relation} {obj}")
        score = len(query_tokens & edge_tokens) if query_tokens else 0
        candidates.append((score, -index, edge))
    candidates.sort(reverse=True)
    selected = [item[2] for item in candidates[:safe_limit]]
    return tuple(
        MemoryItem(
            memory_id=f"graph:{index}:{subject}:{relation}:{obj}",
            task_type="KNOWLEDGE_GRAPH",
            summary=f"RELATIONSHIP — {subject} -> {relation} -> {obj}.",
            output_state=OutputState.SYSTEM_LOG_ONLY.value,
            created_at=_GRAPH_TIMESTAMP,
        )
        for index, (subject, relation, obj, _scopes) in enumerate(selected, start=1)
    )


def status() -> dict[str, object]:
    nodes = {subject for subject, _, _, _ in _EDGES} | {obj for _, _, obj, _ in _EDGES}
    return {
        "component": "OAP Knowledge Graph",
        "ready": bool(_EDGES),
        "revision": GRAPH_REVISION,
        "node_count": len(nodes),
        "edge_count": len(_EDGES),
        "people_profiles_included": False,
        "private_reasoning_included": False,
        "human_authority_final": True,
    }
