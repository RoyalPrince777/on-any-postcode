from __future__ import annotations

import sqlite3

from mission_control import smi_chat_runtime
from oap.audit import initialize_audit_schema
from oap.contracts import FocusedSignal
from oap.hrm import HRMCore, initialize_brain_schema
from oap.smi.canonical_memory import (
    CANONICAL_MEMORY_DIGEST,
    CANONICAL_MEMORY_REVISION,
    status,
)
from oap.smi.context_engine import ContextEngine
from oap.world import WorldEngine


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    initialize_audit_schema(connection)
    initialize_brain_schema(connection)
    connection.commit()
    return connection


def test_canonical_memory_manifest_is_bounded_auditable_and_private():
    snapshot = status()
    assert snapshot["ready"] is True
    assert snapshot["revision"] == CANONICAL_MEMORY_REVISION
    assert snapshot["digest"] == CANONICAL_MEMORY_DIGEST
    assert snapshot["record_count"] >= 20
    assert snapshot["latest_founder_correction_wins"] is True
    assert snapshot["private_chain_of_thought_included"] is False
    assert snapshot["hidden_prompts_included"] is False
    assert snapshot["credentials_or_secrets_included"] is False
    assert snapshot["unrelated_personal_data_included"] is False
    assert snapshot["human_authority_final"] is True


def test_context_engine_merges_canonical_and_dynamic_memory_with_21_cap():
    connection = _connection()
    engine = ContextEngine(HRMCore(connection), WorldEngine(connection))
    signal = FocusedSignal(
        request_id="canonical-context",
        identity_id="founder",
        task_type="TECHNICAL",
        content="Review OAP Maps and SMI architecture",
        oapcore={},
        high_impact=False,
        tags=(),
    )
    context = engine.load(signal)
    assert 1 <= len(context.memories) <= 21
    assert any(item.memory_id.startswith("canonical:") for item in context.memories)
    assert any(
        "SMI" in item.summary or "OAP" in item.summary for item in context.memories
    )


def test_live_provider_memory_includes_canonical_truth_and_recent_hrm():
    brain = {"task_type": "TECHNICAL"}
    merged = smi_chat_runtime._canonical_provider_memory(
        brain,
        ["old lesson", "recent audited HRM lesson"],
    )
    assert 1 <= len(merged) <= 21
    assert any("SMI" in item or "OAP" in item for item in merged)
    assert merged[-1] == "recent audited HRM lesson"
    joined = " ".join(merged).casefold()
    assert "private chain-of-thought" in joined or "private chain of thought" in joined
    assert "credentials" in joined or "secrets" in joined
