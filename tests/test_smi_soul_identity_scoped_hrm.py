"""Soul: HRM context must never cross identity boundaries."""

import pytest

from oap.hrm import HRMCore


def _insert_memory(hrm: HRMCore, *, request_id: str, identity_id: str) -> None:
    hrm.connection.execute(
        "INSERT INTO smi_memory_records ("
        "memory_id, request_id, identity_id, task_type, content_hash, "
        "summary, output_state, signal_level, rationale_json, "
        "processing_states_json, created_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            request_id,
            request_id,
            identity_id,
            "GENERAL",
            "a" * 64,
            f"private memory of {identity_id}",
            "RECOMMENDATION_READY",
            "YELLOW",
            "[]",
            "[]",
            "2026-09-23T06:00:00+00:00",
        ),
    )
    hrm.connection.commit()


def test_hrm_retrieval_is_scoped_to_requester_identity():
    hrm = HRMCore.in_memory()
    _insert_memory(hrm, request_id="owner-memory", identity_id="owner")
    _insert_memory(hrm, request_id="another-memory", identity_id="another")

    owner = hrm.retrieve_context("GENERAL", identity_id="owner")
    another = hrm.retrieve_context("GENERAL", identity_id="another")
    assert [item.memory_id for item in owner] == ["owner-memory"]
    assert [item.memory_id for item in another] == ["another-memory"]
    assert hrm.retrieve_context("GENERAL", identity_id="unknown") == ()


@pytest.mark.parametrize("identity_id", ["", " ", None])
def test_hrm_refuses_missing_identity(identity_id):
    hrm = HRMCore.in_memory()
    with pytest.raises(ValueError, match="verified identity"):
        hrm.retrieve_context("GENERAL", identity_id=identity_id)


def test_hrm_refuses_implicit_unscoped_lookup():
    hrm = HRMCore.in_memory()
    with pytest.raises(TypeError, match="identity_id"):
        hrm.retrieve_context("GENERAL")


def test_context_engine_supplies_filtered_identity():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    source = (root / "oap/smi/context_engine.py").read_text(encoding="utf-8")
    assert "signal.task_type, identity_id=signal.identity_id, limit=4" in source
