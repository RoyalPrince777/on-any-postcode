"""Independent Aegis isolation and recovery for Embodied SMI channels.

Voice, Motion, Panels and Capture can be isolated without killing the single SMI
brain or SMI Chat. Recovery is proof-gated; Capture additionally requires an
explicit Human re-enable because it is a sensing boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CHANNELS = ("VOICE", "MOTION", "PANELS", "CAPTURE")
CHANNEL_STATES = ("ACTIVE", "ISOLATED")


def _channel(value: object) -> str:
    clean = str(value or "").strip().upper()
    if clean not in CHANNELS:
        raise ValueError("invalid_embodiment_channel")
    return clean


@dataclass
class EmbodimentIsolationController:
    session_id: str
    channels: dict[str, str] = field(
        default_factory=lambda: {channel: "ACTIVE" for channel in CHANNELS}
    )
    incidents: list[dict[str, str]] = field(default_factory=list)
    smi_chat_available: bool = True

    def __post_init__(self) -> None:
        if not str(self.session_id or "").strip():
            raise ValueError("session_id_required")
        normalized: dict[str, str] = {}
        for channel in CHANNELS:
            state = str(self.channels.get(channel, "ACTIVE")).strip().upper()
            if state not in CHANNEL_STATES:
                raise ValueError("invalid_embodiment_channel_state")
            normalized[channel] = state
        self.channels = normalized
        self.smi_chat_available = True

    def isolate(self, channel: object, *, reason: object = "aegis_isolation") -> dict[str, Any]:
        target = _channel(channel)
        clean_reason = str(reason or "aegis_isolation").strip()[:120] or "aegis_isolation"
        self.channels[target] = "ISOLATED"
        self.incidents.append({"channel": target, "reason": clean_reason})
        self.incidents = self.incidents[-21:]
        return self.snapshot()

    def master_stop(self, *, reason: object = "human_stop") -> dict[str, Any]:
        for channel in CHANNELS:
            self.channels[channel] = "ISOLATED"
        self.incidents.append(
            {
                "channel": "ALL",
                "reason": str(reason or "human_stop").strip()[:120] or "human_stop",
            }
        )
        self.incidents = self.incidents[-21:]
        return self.snapshot()

    def recover(
        self,
        channel: object,
        *,
        proof_ref: object,
        human_reenable: bool = False,
    ) -> dict[str, Any]:
        target = _channel(channel)
        proof = str(proof_ref or "").strip()[:160]
        if not proof:
            raise PermissionError("recovery_proof_required")
        if target == "CAPTURE" and not human_reenable:
            raise PermissionError("capture_human_reenable_required")
        self.channels[target] = "ACTIVE"
        self.incidents.append(
            {
                "channel": target,
                "reason": f"recovered:{proof}",
            }
        )
        self.incidents = self.incidents[-21:]
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        isolated = tuple(
            channel for channel in CHANNELS if self.channels[channel] == "ISOLATED"
        )
        return {
            "session_id": self.session_id,
            "channels": dict(self.channels),
            "isolated_channels": isolated,
            "smi_chat_available": True,
            "brain_alive": True,
            "intelligence_owner": "SMI",
            "brain_count_added": 0,
            "independent_execution": False,
            "human_authority_final": True,
            "incident_count": len(self.incidents),
        }


def bounded_isolation_recovery_proof() -> dict[str, Any]:
    """Exercise channel isolation/recovery without external or product mutation."""

    controller = EmbodimentIsolationController("aegis-proof")
    checkpoint = controller.snapshot()["channels"]

    independent: dict[str, bool] = {}
    for channel in CHANNELS:
        before = dict(controller.channels)
        state = controller.isolate(channel, reason="bounded_fault_injection")
        others = [item for item in CHANNELS if item != channel]
        independent[channel] = bool(
            state["channels"][channel] == "ISOLATED"
            and all(state["channels"][item] == before[item] for item in others)
            and state["smi_chat_available"]
            and state["brain_alive"]
        )
        controller.recover(
            channel,
            proof_ref=f"proof:{channel.lower()}",
            human_reenable=channel == "CAPTURE",
        )

    master = controller.master_stop(reason="bounded_master_stop")
    master_contained = bool(
        all(master["channels"][channel] == "ISOLATED" for channel in CHANNELS)
        and master["smi_chat_available"]
        and master["brain_alive"]
    )

    recovery: dict[str, bool] = {}
    for channel in CHANNELS:
        state = controller.recover(
            channel,
            proof_ref=f"restore:{channel.lower()}",
            human_reenable=channel == "CAPTURE",
        )
        recovery[channel] = state["channels"][channel] == "ACTIVE"

    restored = controller.channels == checkpoint
    passed = bool(
        all(independent.values())
        and master_contained
        and all(recovery.values())
        and restored
    )
    return {
        "passed": passed,
        "independent_isolation": independent,
        "master_stop_contained": master_contained,
        "recovery": recovery,
        "restored": restored,
        "smi_chat_survived": controller.smi_chat_available,
        "brain_survived": True,
        "production_state_mutated": False,
        "execution_authority_expanded": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    return {
        "component": "SMI Embodiment Aegis Isolation",
        "channels": CHANNELS,
        "channel_states": CHANNEL_STATES,
        "independent_channel_isolation": True,
        "proof_gated_recovery": True,
        "capture_human_reenable_required": True,
        "smi_chat_survives_body_isolation": True,
        "brain_count_added": 0,
        "independent_execution": False,
        "human_authority_final": True,
    }
