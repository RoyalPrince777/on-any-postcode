"""Bounded brain-to-body contract for Embodied SMI.

This module gives the single SMI brain a first-party presentation state machine.
It does not create another intelligence, approval authority or execution path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import live_signals

EMBODIMENT_STATES = (
    "IDLE",
    "LISTENING",
    "THINKING",
    "PRESENTING",
    "SPEAKING",
    "PAUSED",
    "DEGRADED",
    "BLOCKED",
    "STOPPED",
)
AUTHORITY_STATES = (
    "INFORMATION",
    "RECOMMENDATION",
    "REVIEW_REQUIRED",
    "HUMAN_APPROVAL_REQUIRED",
    "BLOCKED",
)
MOTOR_INTENTS = (
    "REST",
    "LISTEN",
    "THINK",
    "SPEAK",
    "EXPLAIN",
    "POINT",
    "COMPARE",
    "WARN",
    "ACKNOWLEDGE",
    "PRESENT",
    "STOP",
)
FALLBACK_MODES = ("FULL", "REDUCED", "VOICE", "TEXT")
PRIVACY_SCOPES = ("PUBLIC", "PROTECTED", "FOUNDER_ONLY")

TRUTH_EXPRESSION = {
    "healthy": "CALM_POSITIVE",
    "learning": "ATTENTIVE",
    "warning": "MEASURED",
    "critical": "WARNING",
    "offline": "NEUTRAL",
}

_ALLOWED_TRANSITIONS = {
    "IDLE": {"LISTENING", "THINKING", "PRESENTING", "SPEAKING", "BLOCKED", "STOPPED"},
    "LISTENING": {"THINKING", "IDLE", "BLOCKED", "STOPPED"},
    "THINKING": {"PRESENTING", "SPEAKING", "PAUSED", "DEGRADED", "BLOCKED", "STOPPED"},
    "PRESENTING": {"SPEAKING", "IDLE", "PAUSED", "DEGRADED", "BLOCKED", "STOPPED"},
    "SPEAKING": {"PRESENTING", "IDLE", "PAUSED", "DEGRADED", "BLOCKED", "STOPPED"},
    "PAUSED": {"THINKING", "PRESENTING", "SPEAKING", "IDLE", "BLOCKED", "STOPPED"},
    "DEGRADED": {"PRESENTING", "SPEAKING", "IDLE", "BLOCKED", "STOPPED"},
    "BLOCKED": {"IDLE", "STOPPED"},
    "STOPPED": set(),
}

_PRIVACY_RANK = {"PUBLIC": 0, "PROTECTED": 1, "FOUNDER_ONLY": 2}


def _clean_enum(value: object, allowed: tuple[str, ...], *, field_name: str) -> str:
    clean = str(value or "").strip().upper()
    if clean not in allowed:
        raise ValueError(f"invalid_{field_name}")
    return clean


def _truth(signal: object) -> dict[str, str]:
    item = live_signals.get_signal(signal)
    signal_id = str(item["id"])
    if signal_id not in TRUTH_EXPRESSION:
        signal_id = "warning"
        item = live_signals.get_signal(signal_id)
    return {
        "id": signal_id,
        "emoji": str(item["emoji"]),
        "label": str(item["label"]),
        "expression": TRUTH_EXPRESSION[signal_id],
    }


def _privacy_allowed(source: str, destination: str) -> bool:
    return _PRIVACY_RANK[destination] >= _PRIVACY_RANK[source]


@dataclass
class EmbodimentController:
    """Stateful presentation controller with no independent intelligence."""

    session_id: str
    state: str = "IDLE"
    fallback_mode: str = "FULL"
    truth_signal: str = "warning"
    authority_state: str = "INFORMATION"
    motor_intent: str = "REST"
    privacy_scope: str = "PROTECTED"
    presentation_scope: str = "PROTECTED"
    speech: str = ""
    panel_refs: tuple[str, ...] = field(default_factory=tuple)
    capture_allowed: bool = False

    def __post_init__(self) -> None:
        if not str(self.session_id or "").strip():
            raise ValueError("session_id_required")
        self.state = _clean_enum(self.state, EMBODIMENT_STATES, field_name="state")
        self.fallback_mode = _clean_enum(
            self.fallback_mode, FALLBACK_MODES, field_name="fallback_mode"
        )
        self.authority_state = _clean_enum(
            self.authority_state, AUTHORITY_STATES, field_name="authority_state"
        )
        self.motor_intent = _clean_enum(
            self.motor_intent, MOTOR_INTENTS, field_name="motor_intent"
        )
        self.privacy_scope = _clean_enum(
            self.privacy_scope, PRIVACY_SCOPES, field_name="privacy_scope"
        )
        self.presentation_scope = _clean_enum(
            self.presentation_scope, PRIVACY_SCOPES, field_name="presentation_scope"
        )
        if not _privacy_allowed(self.privacy_scope, self.presentation_scope):
            raise PermissionError("embodiment_privacy_scope_blocked")
        self.truth_signal = _truth(self.truth_signal)["id"]

    def transition(self, target: object, *, human_restart: bool = False) -> dict[str, Any]:
        target_state = _clean_enum(target, EMBODIMENT_STATES, field_name="state")
        if self.state == "STOPPED":
            if not human_restart or target_state != "IDLE":
                raise PermissionError("human_restart_required")
            self.state = "IDLE"
            self.motor_intent = "REST"
            return self.snapshot()
        if target_state not in _ALLOWED_TRANSITIONS[self.state]:
            raise ValueError("invalid_embodiment_transition")
        self.state = target_state
        if target_state == "STOPPED":
            return self.stop()
        return self.snapshot()

    def present(
        self,
        *,
        speech: object = "",
        truth_signal: object = "warning",
        authority_state: object = "INFORMATION",
        motor_intent: object = "PRESENT",
        panel_refs: tuple[str, ...] | list[str] = (),
        privacy_scope: object | None = None,
        presentation_scope: object | None = None,
    ) -> dict[str, Any]:
        if self.state == "STOPPED":
            raise PermissionError("human_restart_required")
        authority = _clean_enum(
            authority_state, AUTHORITY_STATES, field_name="authority_state"
        )
        motor = _clean_enum(motor_intent, MOTOR_INTENTS, field_name="motor_intent")
        source_scope = _clean_enum(
            privacy_scope if privacy_scope is not None else self.privacy_scope,
            PRIVACY_SCOPES,
            field_name="privacy_scope",
        )
        destination_scope = _clean_enum(
            presentation_scope
            if presentation_scope is not None
            else self.presentation_scope,
            PRIVACY_SCOPES,
            field_name="presentation_scope",
        )
        if not _privacy_allowed(source_scope, destination_scope):
            self.state = "BLOCKED"
            self.authority_state = "BLOCKED"
            self.motor_intent = "STOP"
            self.speech = ""
            self.panel_refs = ()
            self.capture_allowed = False
            raise PermissionError("embodiment_privacy_scope_blocked")

        truth = _truth(truth_signal)
        if authority == "BLOCKED" or truth["id"] == "critical":
            motor = "WARN" if authority != "BLOCKED" else "STOP"
        self.truth_signal = truth["id"]
        self.authority_state = authority
        self.motor_intent = motor
        self.privacy_scope = source_scope
        self.presentation_scope = destination_scope
        self.speech = str(speech or "").strip()[:12000]
        self.panel_refs = tuple(
            dict.fromkeys(str(item).strip()[:120] for item in panel_refs if str(item).strip())
        )[:21]
        self.state = "SPEAKING" if self.speech else "PRESENTING"
        return self.snapshot()

    def pause(self) -> dict[str, Any]:
        if self.state == "STOPPED":
            raise PermissionError("human_restart_required")
        self.state = "PAUSED"
        self.motor_intent = "REST"
        return self.snapshot()

    def stop(self) -> dict[str, Any]:
        """Immediate presentation stop. Safe to call repeatedly."""
        self.state = "STOPPED"
        self.authority_state = "BLOCKED"
        self.motor_intent = "STOP"
        self.speech = ""
        self.panel_refs = ()
        self.capture_allowed = False
        return self.snapshot()

    def degrade(self) -> dict[str, Any]:
        order = list(FALLBACK_MODES)
        current = order.index(self.fallback_mode)
        if current < len(order) - 1:
            self.fallback_mode = order[current + 1]
        self.state = "DEGRADED"
        if self.fallback_mode == "TEXT":
            self.motor_intent = "REST"
            self.capture_allowed = False
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        truth = _truth(self.truth_signal)
        return {
            "session_id": self.session_id,
            "state": self.state,
            "fallback_mode": self.fallback_mode,
            "truth": truth,
            "authority_state": self.authority_state,
            "motor_intent": self.motor_intent,
            "privacy_scope": self.privacy_scope,
            "presentation_scope": self.presentation_scope,
            "speech": self.speech,
            "panel_refs": self.panel_refs,
            "capture_allowed": self.capture_allowed,
            "intelligence_owner": "SMI",
            "brain_count_added": 0,
            "independent_intelligence": False,
            "independent_execution": False,
            "human_authority_final": True,
        }


def status() -> dict[str, Any]:
    return {
        "component": "SMI Embodiment Controller",
        "configured": True,
        "states": EMBODIMENT_STATES,
        "authority_states": AUTHORITY_STATES,
        "motor_intents": MOTOR_INTENTS,
        "fallback_modes": FALLBACK_MODES,
        "privacy_scopes": PRIVACY_SCOPES,
        "stop_priority": ("STOP", "PRIVACY", "SAFETY", "SPEECH", "MOTION"),
        "intelligence_owner": "SMI",
        "brain_count_added": 0,
        "independent_intelligence": False,
        "independent_execution": False,
        "execution_state_exposed": "EXECUTE" in AUTHORITY_STATES,
        "human_authority_final": True,
        "no_fake_green": True,
    }



def bounded_runtime_guard_proof() -> dict[str, Any]:
    """Exercise Embodiment authority, truth, privacy and STOP guards in memory."""

    controller = EmbodimentController("runtime-guard-proof")
    no_execute_state = "EXECUTE" not in AUTHORITY_STATES
    unknown_motor_blocked = False
    privacy_blocked = False
    restart_blocked = False

    try:
        controller.present(motor_intent="RAW_OVERRIDE")
    except ValueError:
        unknown_motor_blocked = True

    try:
        controller.present(
            speech="private",
            privacy_scope="FOUNDER_ONLY",
            presentation_scope="PUBLIC",
        )
    except PermissionError:
        privacy_blocked = True

    controller = EmbodimentController("runtime-guard-stop-proof")
    controller.present(
        speech="active",
        truth_signal="warning",
        authority_state="RECOMMENDATION",
        motor_intent="EXPLAIN",
    )
    stopped = controller.stop()
    try:
        controller.present(speech="self resume blocked")
    except PermissionError:
        restart_blocked = True

    warning_truth_preserved = stopped["truth"]["id"] == "warning"
    output_cleared = bool(
        stopped["speech"] == ""
        and stopped["panel_refs"] == ()
        and stopped["capture_allowed"] is False
        and stopped["motor_intent"] == "STOP"
    )
    passed = all(
        (
            no_execute_state,
            unknown_motor_blocked,
            privacy_blocked,
            restart_blocked,
            warning_truth_preserved,
            output_cleared,
        )
    )
    return {
        "passed": passed,
        "no_execute_state": no_execute_state,
        "unknown_motor_blocked": unknown_motor_blocked,
        "privacy_blocked": privacy_blocked,
        "restart_blocked": restart_blocked,
        "truth_preserved": warning_truth_preserved,
        "stop_output_cleared": output_cleared,
        "brain_count_added": 0,
        "production_state_mutated": False,
        "execution_authority_expanded": False,
        "human_authority_final": True,
    }
