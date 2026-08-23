"""Locked processing state machine for Human Authority governance."""

from __future__ import annotations

from enum import StrEnum


class ProcessingState(StrEnum):
    RECEIVED = "RECEIVED"
    IDENTITY_VERIFIED = "IDENTITY_VERIFIED"
    SMI_REVIEWED = "SMI_REVIEWED"
    GUARDIAN_PASSED = "GUARDIAN_PASSED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    HUMAN_REJECTED = "HUMAN_REJECTED"
    KERNEL_EXECUTED = "KERNEL_EXECUTED"
    EXECUTION_BLOCKED = "EXECUTION_BLOCKED"
    HRM_RECORDED = "HRM_RECORDED"


_ALLOWED_TRANSITIONS: dict[ProcessingState, frozenset[ProcessingState]] = {
    ProcessingState.RECEIVED: frozenset(
        {ProcessingState.IDENTITY_VERIFIED, ProcessingState.EXECUTION_BLOCKED}
    ),
    ProcessingState.IDENTITY_VERIFIED: frozenset(
        {ProcessingState.SMI_REVIEWED, ProcessingState.EXECUTION_BLOCKED}
    ),
    ProcessingState.SMI_REVIEWED: frozenset(
        {ProcessingState.GUARDIAN_PASSED, ProcessingState.EXECUTION_BLOCKED}
    ),
    ProcessingState.GUARDIAN_PASSED: frozenset(
        {
            ProcessingState.HUMAN_REVIEW_REQUIRED,
            ProcessingState.EXECUTION_BLOCKED,
            ProcessingState.HRM_RECORDED,
        }
    ),
    ProcessingState.HUMAN_REVIEW_REQUIRED: frozenset(
        {
            ProcessingState.HUMAN_APPROVED,
            ProcessingState.HUMAN_REJECTED,
            ProcessingState.EXECUTION_BLOCKED,
        }
    ),
    ProcessingState.HUMAN_APPROVED: frozenset(
        {ProcessingState.KERNEL_EXECUTED, ProcessingState.EXECUTION_BLOCKED}
    ),
    ProcessingState.HUMAN_REJECTED: frozenset({ProcessingState.EXECUTION_BLOCKED}),
    ProcessingState.KERNEL_EXECUTED: frozenset({ProcessingState.HRM_RECORDED}),
    ProcessingState.EXECUTION_BLOCKED: frozenset({ProcessingState.HRM_RECORDED}),
    ProcessingState.HRM_RECORDED: frozenset(),
}


class InvalidStateTransition(ValueError):
    """Raised when a component attempts to bypass the governance path."""


class RequestStateMachine:
    """Small deterministic state machine with an immutable public history."""

    def __init__(self) -> None:
        self._state = ProcessingState.RECEIVED
        self._history = [self._state]

    @property
    def state(self) -> ProcessingState:
        return self._state

    @property
    def history(self) -> tuple[str, ...]:
        return tuple(state.value for state in self._history)

    def advance(self, next_state: ProcessingState) -> None:
        allowed = _ALLOWED_TRANSITIONS[self._state]
        if next_state not in allowed:
            raise InvalidStateTransition(
                f"Cannot move from {self._state.value} to {next_state.value}"
            )
        self._state = next_state
        self._history.append(next_state)

    def block_and_record(self) -> None:
        """Follow the only valid blocked path from the current pre-terminal state."""

        can_block = (
            self._state == ProcessingState.HUMAN_REJECTED
            or ProcessingState.EXECUTION_BLOCKED
            in _ALLOWED_TRANSITIONS[self._state]
        )
        if can_block:
            self.advance(ProcessingState.EXECUTION_BLOCKED)
        elif self._state != ProcessingState.EXECUTION_BLOCKED:
            raise InvalidStateTransition(
                f"Cannot block a request from {self._state.value}"
            )
        self.advance(ProcessingState.HRM_RECORDED)
