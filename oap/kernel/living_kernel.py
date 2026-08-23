"""Living Kernel heart: coordinates only verified Human-approved work."""

from __future__ import annotations

from oap.contracts import (
    ActionPlan,
    ApprovalDecision,
    ApprovalReceipt,
    BuilderContext,
    KernelResult,
    OutputState,
    Recommendation,
)
from oap.hrm import ApprovalReceiptReplay, HRMCore
from oap.state_machine import (
    InvalidStateTransition,
    ProcessingState,
    RequestStateMachine,
)

from .approval import HumanApprovalAuthority
from .builder import BuilderRegistry


class LivingKernel:
    """The one heart; it never reasons or approves."""

    def __init__(
        self,
        authority: HumanApprovalAuthority,
        builder: BuilderRegistry,
        hrm: HRMCore,
    ) -> None:
        self.authority = authority
        self.builder = builder
        self.hrm = hrm

    def coordinate(
        self,
        recommendation: Recommendation,
        plan: ActionPlan,
        receipt: ApprovalReceipt,
    ) -> KernelResult:
        if recommendation.request_id != plan.request_id:
            return self._record_block(
                recommendation.request_id,
                "Action plan does not match the recommendation",
                (),
                receipt.receipt_id,
            )
        if not plan.requires_human_approval:
            return self._record_block(
                recommendation.request_id,
                "Action plan attempted to remove the Human Authority gate",
                recommendation.processing_states,
                receipt.receipt_id,
            )
        if recommendation.output_state not in {
            OutputState.RECOMMENDATION_READY,
            OutputState.REVIEW_REQUIRED,
        }:
            return self._record_block(
                recommendation.request_id,
                "SMI output is not eligible for execution",
                recommendation.processing_states,
                receipt.receipt_id,
            )

        try:
            state = self._resume(recommendation.processing_states)
        except (InvalidStateTransition, ValueError):
            blocked = RequestStateMachine()
            blocked.block_and_record()
            return self._record_block(
                recommendation.request_id,
                "Recommendation processing history is invalid",
                blocked.history,
                receipt.receipt_id,
            )
        valid_receipt = self.authority.verify(
            receipt,
            recommendation.request_id,
            plan=plan,
            require_approved=False,
        )
        if not valid_receipt:
            state.block_and_record()
            return self._record_block(
                recommendation.request_id,
                "Human Authority receipt is invalid or expired",
                state.history,
                receipt.receipt_id,
            )
        try:
            self.hrm.record_approval(receipt)
        except ApprovalReceiptReplay as exc:
            state.block_and_record()
            return self._record_block(
                recommendation.request_id,
                str(exc),
                state.history,
                receipt.receipt_id,
            )
        if receipt.decision == ApprovalDecision.REJECTED:
            state.advance(ProcessingState.HUMAN_REJECTED)
            state.block_and_record()
            return self._record_block(
                recommendation.request_id,
                "Human Authority rejected the recommendation",
                state.history,
                receipt.receipt_id,
            )

        state.advance(ProcessingState.HUMAN_APPROVED)
        try:
            self.builder.execute(
                plan,
                BuilderContext(
                    request_id=receipt.request_id,
                    receipt_id=receipt.receipt_id,
                    identity_id=receipt.identity_id,
                    authority_level=receipt.authority_level,
                    action_digest=receipt.action_digest,
                ),
            )
        except Exception as exc:  # noqa: BLE001 - Builder is a plugin boundary.
            state.advance(ProcessingState.EXECUTION_BLOCKED)
            state.advance(ProcessingState.HRM_RECORDED)
            return self._record_block(
                recommendation.request_id,
                str(exc),
                state.history,
                receipt.receipt_id,
            )

        state.advance(ProcessingState.KERNEL_EXECUTED)
        state.advance(ProcessingState.HRM_RECORDED)
        result = KernelResult(
            request_id=recommendation.request_id,
            state=ProcessingState.KERNEL_EXECUTED.value,
            executed=True,
            reason="Verified Human-approved Builder action completed",
            processing_states=state.history,
        )
        outcome_id = self.hrm.record_kernel_result(result, receipt.receipt_id)
        return KernelResult(
            request_id=result.request_id,
            state=result.state,
            executed=result.executed,
            reason=result.reason,
            processing_states=result.processing_states,
            audit_event_id=outcome_id,
        )

    def _record_block(
        self,
        request_id: str,
        reason: str,
        processing_states: tuple[str, ...],
        receipt_id: str | None,
    ) -> KernelResult:
        result = KernelResult(
            request_id=request_id,
            state=ProcessingState.EXECUTION_BLOCKED.value,
            executed=False,
            reason=reason,
            processing_states=processing_states,
        )
        outcome_id = self.hrm.record_kernel_result(result, receipt_id)
        return KernelResult(
            request_id=result.request_id,
            state=result.state,
            executed=result.executed,
            reason=result.reason,
            processing_states=result.processing_states,
            audit_event_id=outcome_id,
        )

    @staticmethod
    def _resume(history: tuple[str, ...]) -> RequestStateMachine:
        if not history or history[0] != ProcessingState.RECEIVED.value:
            raise ValueError("Recommendation processing history is invalid")
        state = RequestStateMachine()
        for value in history[1:]:
            state.advance(ProcessingState(value))
        if state.state != ProcessingState.HUMAN_REVIEW_REQUIRED:
            raise ValueError("Recommendation is not at the Human review gate")
        return state

    def status(self) -> dict[str, object]:
        return {
            "component": "Living Kernel",
            "ready": True,
            "role": "approved_action_coordinator",
            "brain": False,
            "independent_approval": False,
            "builder": self.builder.status(),
        }
