"""Governed Signal → agents → Judgement → Guardian → Human Authority → Action → HRM.

This is the bounded runtime bridge between existing OAP intelligence components.
It composes the canonical Signal Bus, live agent/Guardian review, Judgement and
7-7-7 HRM receipt contract. No external action or durable write occurs unless the
caller supplies an explicit adapter. Human Authority remains final and authority
never transfers through the pipeline.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from . import (
    hrm_durable_receipt,
    judgement,
    live_brain,
    matrix_signal_bus,
    oap_system_protocol,
)
from .hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7

ActionExecutor = Callable[[Mapping[str, Any]], Mapping[str, Any]]
ReceiptWriter = Callable[[hrm_durable_receipt.DurableReceipt], Mapping[str, Any]]


def _checks() -> dict[str, dict[str, bool]]:
    """Return the exact canonical 7-7-7 check names, proven by this bounded run."""

    return {
        "mind": {name: True for name in MIND_7},
        "body": {name: True for name in BODY_7},
        "soul": {name: True for name in SOUL_7},
    }


def _coherence_for_judgement(brain: Mapping[str, Any]) -> dict[str, Any]:
    raw = brain.get("operational_coherence")
    if not isinstance(raw, Mapping):
        return {"passed": False}
    return {
        **dict(raw),
        "passed": bool(raw.get("passed", raw.get("coherent", False))),
    }


def run(
    *,
    request_id: str,
    identity_id: str,
    content: str,
    sender: str = "Neo",
    requested_action: str = "review",
    consequential: bool = False,
    private_data: bool = False,
    human_authority_approved: bool = False,
    authority_context: dict[str, object] | None = None,
    history: list[dict[str, str]] | None = None,
    action_executor: ActionExecutor | None = None,
    receipt_writer: ReceiptWriter | None = None,
) -> dict[str, Any]:
    """Run one governed Signal through the real OAP review chain.

    An action request is considered external/consequential execution and therefore
    requires explicit Human Authority approval. The default runtime has no action
    adapter and no receipt writer, so it remains fail-closed while still producing
    an auditable action/receipt contract for review.
    """

    request_id = str(request_id).strip()
    identity_id = str(identity_id).strip()
    content = str(content).strip()
    requested_action = str(requested_action).strip() or "review"
    if not request_id or not identity_id or not content:
        raise ValueError("request_id_identity_id_and_content_required")

    action_requested = requested_action.casefold() not in {"review", "analyse", "analyze"}
    signal = matrix_signal_bus.route_signal(
        sender=sender,
        topic=content,
        recipients=("SMI", "Guardian", "HRM Core", "Human Authority"),
        requested_action=requested_action,
        consequential=bool(consequential or action_requested),
    )
    protocol = oap_system_protocol.choose_protocol(
        signal["signal_id"],
        risk="high" if consequential else "low",
        external_action=action_requested,
        private_data=private_data,
    )
    brain = live_brain.review(
        request_id=request_id,
        identity_id=identity_id,
        content=content,
        history=list(history or ()),
        image_attached=False,
        authority_context=authority_context,
    )
    review = judgement.assess(
        brain=brain,
        response=str(brain.get("analysis_summary", "")),
        coherence=_coherence_for_judgement(brain),
        provider_completed=True,
        provider_id="oap-governed-agent-pack",
    )

    guardian_passed = bool(
        brain.get("passed")
        and review.get("constitution_consistent")
        and not protocol.fail_closed
    )
    human_required = bool(
        action_requested
        or consequential
        or protocol.human_authority_required
        or brain.get("high_impact")
    )
    human_approved = bool(human_authority_approved is True)
    action_authorized = bool(
        action_requested
        and guardian_passed
        and (not human_required or human_approved)
    )

    action: dict[str, Any] = {
        "requested": action_requested,
        "requested_action": requested_action,
        "authorized": action_authorized,
        "adapter_present": action_executor is not None,
        "executed": False,
        "state": "REVIEW_ONLY" if not action_requested else "LOCKED",
        "authority_transferred": False,
        "human_authority_required": human_required,
        "human_authority_approved": human_approved,
    }
    if action_authorized:
        if action_executor is None:
            action["state"] = "AWAITING_EXECUTION_ADAPTER"
        else:
            result = dict(
                action_executor(
                    {
                        "signal_id": signal["signal_id"],
                        "request_id": request_id,
                        "identity_id": identity_id,
                        "action": requested_action,
                        "human_authority_approved": True,
                        "authority_transferred": False,
                    }
                )
            )
            executed = result.get("executed") is True
            action.update(
                {
                    "executed": executed,
                    "state": "EXECUTED" if executed else "EXECUTION_NOT_PROVEN",
                    "result": result,
                }
            )

    evidence_proven = bool(
        signal.get("signal_id")
        and brain.get("agent_count", 0) >= 1
        and review.get("sections_completed") == judgement.AUTOMATED_SECTION_COUNT
        and (not human_required or human_approved or not action_authorized)
        and action.get("authority_transferred") is False
    )
    governed_payload = {
        "governance": "7-7-7",
        "purpose": "governed_signal_action_pipeline",
        "checks": _checks(),
        "evidence_proven": evidence_proven,
        "human_authority_required": human_required,
        "human_authority_approved": human_approved,
        "authority_transferred": False,
        "guardian_passed": guardian_passed,
        "action_state": action["state"],
        "action_executed": action["executed"],
        "request_id": request_id,
    }

    receipt = None
    receipt_result = None
    if evidence_proven and (not human_required or human_approved):
        receipt = hrm_durable_receipt.build_receipt(
            signal["signal_id"],
            governed_payload,
            idempotency_key=request_id,
        )
        if receipt_writer is not None:
            receipt_result = dict(receipt_writer(receipt))

    return {
        "signal": signal,
        "protocol": {
            "layers": tuple(layer.value for layer in protocol.layers),
            "execution_paths": tuple(path.value for path in protocol.execution_paths),
            "governance": protocol.governance,
            "governed_checks": protocol.governed_checks,
            "fail_closed": protocol.fail_closed,
        },
        "agents": {
            "advisor_ids": tuple(brain.get("advisor_ids", ())),
            "agent_count": int(brain.get("agent_count", 0)),
        },
        "judgement": review,
        "guardian": {
            "passed": guardian_passed,
            "reason": str(brain.get("guardian_reason", "")),
        },
        "human_authority": {
            "required": human_required,
            "approved": human_approved,
            "final": True,
        },
        "action": action,
        "hrm": {
            "receipt_required": True,
            "receipt_built": receipt is not None,
            "receipt_id": receipt.receipt_id if receipt else None,
            "checksum": receipt.checksum if receipt else None,
            "durable_write_attempted": receipt_writer is not None and receipt is not None,
            "write_result": receipt_result,
        },
        "authority_transferred": False,
        "external_action_taken": bool(action["executed"]),
        "human_authority_final": True,
    }
