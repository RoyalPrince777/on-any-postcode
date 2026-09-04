"""Provider-neutral capability fabric for Sovereign Megaverse Intelligence.

OAP absorbs useful capability patterns from the wider AI ecosystem without copying
provider branding, prompts, private reasoning, model weights or product identity.
External providers may remain optional inference/tool adapters, but SMI owns the
routing policy, memory, evidence rules, governance and user experience.
"""

from __future__ import annotations

from dataclasses import dataclass

CAPABILITY_FABRIC_REVISION = "2026-09-04-v1"


@dataclass(frozen=True)
class Capability:
    capability_id: str
    purpose: str
    trigger_terms: tuple[str, ...]
    task_types: tuple[str, ...]
    requires_fresh_evidence: bool = False
    high_impact_safe: bool = True


_CAPABILITIES: tuple[Capability, ...] = (
    Capability(
        "adaptive_reasoning",
        "Use the smallest sufficient SMI depth and escalate 3 -> 7 -> 21 when complexity or uncertainty requires it.",
        ("reason", "complex", "analyse", "analyze", "plan", "strategy"),
        ("GENERAL", "TECHNICAL", "STRATEGY", "COMMUNITY", "MONITORING"),
    ),
    Capability(
        "agentic_code_review",
        "Inspect, plan, implement, test, review and verify code in bounded stages before claiming completion.",
        ("code", "bug", "fix", "test", "repo", "github", "deploy", "refactor"),
        ("TECHNICAL",),
    ),
    Capability(
        "advisor_challenger",
        "Use a planner/reviewer or challenger pass on difficult work before committing to a consequential recommendation.",
        ("architecture", "complex", "risk", "review", "challenge", "decision"),
        ("TECHNICAL", "STRATEGY", "MONITORING"),
    ),
    Capability(
        "long_context_synthesis",
        "Chunk, retrieve, compact and synthesise large histories or documents instead of flooding every request with all context.",
        ("history", "document", "pdf", "long", "all", "everything", "memory", "archive"),
        ("GENERAL", "TECHNICAL", "STRATEGY", "CULTURE"),
    ),
    Capability(
        "multimodal_fusion",
        "Fuse text, images, audio, video, PDFs and structured data while preserving modality provenance.",
        ("image", "audio", "video", "pdf", "file", "multimodal", "voice"),
        ("GENERAL", "TECHNICAL", "COMMUNITY", "CULTURE"),
    ),
    Capability(
        "cited_live_research",
        "Use fresh retrieval for time-sensitive facts, preserve source provenance and present citations or evidence references.",
        ("latest", "today", "current", "research", "source", "news", "live", "verify"),
        ("GENERAL", "TECHNICAL", "STRATEGY", "MONITORING", "COMMUNITY"),
        requires_fresh_evidence=True,
    ),
    Capability(
        "parallel_retrieval",
        "Decompose complex research into bounded parallel queries and merge only non-duplicative evidence.",
        ("compare", "deep dive", "research", "many", "across", "multiple"),
        ("GENERAL", "TECHNICAL", "STRATEGY", "MONITORING"),
        requires_fresh_evidence=True,
    ),
    Capability(
        "live_signal_awareness",
        "Use public live signals such as news, web and authorised social/community data without depending on one platform.",
        ("trend", "social", "signal", "breaking", "live", "community"),
        ("GENERAL", "MONITORING", "COMMUNITY", "STRATEGY"),
        requires_fresh_evidence=True,
    ),
    Capability(
        "cost_aware_routing",
        "Route simple work to efficient local/fast paths and reserve deeper compute for tasks that justify it.",
        ("fast", "cheap", "efficient", "cost", "instant", "scale"),
        ("GENERAL", "TECHNICAL", "STRATEGY", "MONITORING"),
    ),
    Capability(
        "tool_orchestration",
        "Select and sequence approved tools, functions and specialist agents while preserving permissions and audit boundaries.",
        ("tool", "agent", "workflow", "execute", "action", "connect", "integrate"),
        ("GENERAL", "TECHNICAL", "STRATEGY", "MONITORING"),
    ),
    Capability(
        "structured_output",
        "Return validated schemas, plans, records or machine-readable structures when downstream systems require reliability.",
        ("json", "schema", "structured", "table", "record", "api"),
        ("GENERAL", "TECHNICAL", "STRATEGY"),
    ),
    Capability(
        "context_compaction",
        "Preserve durable task state across long workflows while compressing stale detail and retaining authoritative decisions.",
        ("continue", "remember", "resume", "long", "session", "context", "memory"),
        ("GENERAL", "TECHNICAL", "STRATEGY"),
    ),
    Capability(
        "evidence_first",
        "Separate observed, retrieved, inferred and proposed information and refuse unsupported completion claims.",
        ("proof", "evidence", "verify", "confirmed", "live", "status"),
        ("GENERAL", "TECHNICAL", "STRATEGY", "MONITORING"),
        requires_fresh_evidence=True,
    ),
    Capability(
        "local_first_failover",
        "Prefer OAP-controlled local/Home Node paths, use governed fallbacks when needed and never grant a provider authority.",
        ("local", "ollama", "offline", "fallback", "provider", "sovereign"),
        ("GENERAL", "TECHNICAL", "MONITORING"),
    ),
    Capability(
        "safe_process_telemetry",
        "Expose stage, time, tools, evidence and confidence telemetry without exposing private chain-of-thought.",
        ("thinking", "progress", "time", "telemetry", "process", "stage"),
        ("GENERAL", "TECHNICAL", "MONITORING"),
    ),
)


def select_capabilities(
    task_type: str | None,
    query: str,
    *,
    high_impact: bool = False,
    limit: int = 8,
) -> tuple[str, ...]:
    """Select deterministic SMI capability IDs for one request."""

    task = str(task_type or "GENERAL").strip().upper() or "GENERAL"
    text = str(query or "").casefold()
    safe_limit = min(max(int(limit), 1), 12)
    ranked: list[tuple[int, int, Capability]] = []
    for index, capability in enumerate(_CAPABILITIES):
        if task not in capability.task_types and "GENERAL" not in capability.task_types:
            continue
        score = sum(term in text for term in capability.trigger_terms)
        if task in capability.task_types:
            score += 1
        if high_impact and capability.capability_id in {
            "advisor_challenger",
            "evidence_first",
            "structured_output",
        }:
            score += 3
        if score:
            ranked.append((score, -index, capability))
    ranked.sort(reverse=True)
    selected = [item[2].capability_id for item in ranked[:safe_limit]]
    if "adaptive_reasoning" not in selected:
        selected.insert(0, "adaptive_reasoning")
    if high_impact and "evidence_first" not in selected:
        selected.append("evidence_first")
    return tuple(dict.fromkeys(selected))[:safe_limit]


def capability_descriptions(capability_ids: tuple[str, ...]) -> tuple[str, ...]:
    lookup = {item.capability_id: item.purpose for item in _CAPABILITIES}
    return tuple(lookup[item] for item in capability_ids if item in lookup)


def status() -> dict[str, object]:
    ids = tuple(item.capability_id for item in _CAPABILITIES)
    return {
        "component": "OAP Intelligence Capability Fabric",
        "ready": bool(ids) and len(ids) == len(set(ids)),
        "revision": CAPABILITY_FABRIC_REVISION,
        "capability_count": len(ids),
        "provider_neutral": True,
        "copies_provider_identity": False,
        "copies_private_prompts": False,
        "copies_model_weights": False,
        "external_provider_authority": False,
        "local_first": True,
        "human_authority_final": True,
    }
