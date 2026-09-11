"""Latest explicit Founder locks that outrank older project memory.

This is curated OAP project context only. It never contains passwords, credentials,
hidden prompts, private chain-of-thought, raw chat dumps, or unrelated personal data.
"""
from __future__ import annotations

from datetime import datetime, timezone

from oap.contracts import MemoryItem, OutputState

REVISION = "2026-09-11-founder-parity"
_TIMESTAMP = datetime(2026, 9, 11, tzinfo=timezone.utc)

_RECORDS = (
    (
        "joog.unified-memory",
        (
            "JOOG MEMORY is the single unified SMI/OAP memory core: one continuous "
            "governed system log for inputs, safe reasoning summaries, actions, "
            "outputs, context, learning, receipts and status. HRM remains governance, "
            "audit, review and lessons; Neon or another database is persistence "
            "infrastructure and does not replace HRM or JOOG semantics."
        ),
    ),
    (
        "production.no-fake-green",
        (
            "Canonical production law: no demo, no generic substitute, no static "
            "placeholder presented as working functionality, no experiment presented "
            "as production and no fake green. A feature becomes green only when real, "
            "connected, governed, tested, runtime-proven and evidence-backed. Blocked "
            "or degraded dependencies must be labelled truthfully."
        ),
    ),
    (
        "agents.kaa-excluded",
        (
            "Kaa is completely excluded from ON ANY POSTCODE/OAP. Kaa must not appear "
            "in the Jungle Book layer, registered agents, dashboards, backend, "
            "documentation, prompts, counts or future OAP designs unless Human "
            "Authority explicitly restores Kaa."
        ),
    ),
    (
        "smi.founder-workspace-parity",
        (
            "Personal SMI is the private Founder working home: clean 2027 chat, one "
            "canonical Send/Enter/Mic/Voice/Stop runtime, safe Thinking Process "
            "telemetry, JOOG/HRM continuity, connected governed tools such as "
            "GitHub/Render/Neon, and concise evidence-first status. It should support "
            "working continuity comparable to this ChatGPT workflow without claiming "
            "access to private model chain-of-thought or inaccessible external memory "
            "internals."
        ),
    ),
)


def latest_founder_memory_items(*, limit: int = 4) -> tuple[MemoryItem, ...]:
    safe_limit = min(max(int(limit), 1), len(_RECORDS))
    return tuple(
        MemoryItem(
            memory_id=f"founder-lock:{memory_id}",
            task_type="LATEST_FOUNDER_LOCK",
            summary=summary,
            output_state=OutputState.SYSTEM_LOG_ONLY.value,
            created_at=_TIMESTAMP,
        )
        for memory_id, summary in _RECORDS[:safe_limit]
    )


def status() -> dict[str, object]:
    ids = tuple(memory_id for memory_id, _ in _RECORDS)
    return {
        "component": "Latest Founder Memory Locks",
        "ready": bool(ids) and len(ids) == len(set(ids)),
        "revision": REVISION,
        "record_count": len(ids),
        "latest_founder_correction_wins": True,
        "raw_chat_dump": False,
        "private_chain_of_thought_included": False,
        "credentials_or_secrets_included": False,
        "human_authority_final": True,
    }
