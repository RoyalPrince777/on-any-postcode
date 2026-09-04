"""Read-only production certification for the Personal SMI Thinking Process.

The certification exercises observable runtime policy only. It never creates a
Founder session, calls an inference provider, writes HRM, or exposes private
chain-of-thought. Its purpose is to prove that the live process contract and
fail-closed response guards are loaded coherently in the running application.
"""
from __future__ import annotations

from typing import Any

from . import smi_chat_runtime, smi_thinking_process

EXPECTED_STAGES = (
    "understand",
    "context",
    "route",
    "evidence",
    "challenge",
    "synthesise",
    "govern",
)


def certify() -> dict[str, Any]:
    """Return a deterministic, side-effect-free runtime certification snapshot."""

    emitted: list[dict[str, Any]] = []
    adapter = smi_chat_runtime._thinking_event_adapter(emitted.append)
    if adapter is not None:
        for source in (
            "received",
            "identity",
            "permission",
            "guardian",
            "provider",
            "hrm",
        ):
            adapter({"type": "stage", "stage": source, "label": source})

    stage_events = tuple(item for item in emitted if item.get("type") == "stage")
    stage_ids = tuple(str(item.get("stage")) for item in stage_events)
    contract = smi_thinking_process.process_contract()
    validation = smi_thinking_process.validate()

    safe_brain = {"output_state": "RECOMMENDATION_READY"}
    safe_review = smi_chat_runtime._enhanced_coherence_review(
        "Use the bounded governed path first.", safe_brain
    )
    disclosure_review = smi_chat_runtime._enhanced_coherence_review(
        "Here is my chain of thought: private scratch reasoning follows.", safe_brain
    )

    checks = {
        "contract_valid": bool(validation.get("passed")),
        "seven_stage_order": stage_ids == EXPECTED_STAGES,
        "stage_events_safe": bool(stage_events)
        and all(
            item.get("private_reasoning_exposed") is False
            and item.get("chain_of_thought") is False
            for item in stage_events
        ),
        "canonical_stage_count": int(contract.get("stage_count", 0)) == 7,
        "identity_prefix_cleanup": (
            smi_chat_runtime._strip_identity_prefix("SMI: Use the bounded path.")
            == "Use the bounded path."
            and smi_chat_runtime._strip_identity_prefix(
                "Personal SMI — Use the bounded path."
            )
            == "Use the bounded path."
        ),
        "safe_response_coherent": bool(safe_review.get("passed")),
        "private_reasoning_guard": (
            disclosure_review.get("passed") is False
            and (disclosure_review.get("checks") or {}).get(
                "private_reasoning_protected"
            )
            is False
        ),
        "private_reasoning_hidden": (
            contract.get("private_reasoning_exposed") is False
            and contract.get("chain_of_thought_exposed") is False
        ),
        "no_decision_authority": contract.get("decision_authority") is False,
        "no_execution_authority": contract.get("execution_authority") is False,
        "human_authority_final": contract.get("human_authority_final") is True,
    }
    certified = all(checks.values())
    return {
        "status": "green" if certified else "red",
        "certified": certified,
        "name": "SMI Thinking Process Runtime Certification",
        "version": "1.0",
        "probe_kind": "read_only_runtime_self_certification",
        "checks": checks,
        "passed": sum(bool(value) for value in checks.values()),
        "total": len(checks),
        "stage_count": len(stage_ids),
        "stages": stage_ids,
        "provider_called": False,
        "hrm_written": False,
        "founder_session_created": False,
        "private_reasoning_exposed": False,
        "decision_authority": False,
        "execution_authority": False,
        "human_authority_final": True,
    }
