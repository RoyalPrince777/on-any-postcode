"""Software-only simulator for the OAP Sovereign Digital SoC v0.

The simulator models trusted boot, registers, interrupts, NEXUS messages,
Guardian gate enforcement and HRM-style receipts entirely in memory. It does
not control physical hardware, perform external actions, mutate production,
provision keys, or grant authority. SMI remains the single OAP Brain and Human
Authority remains final.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .organism import BODY_ORGANS, ORGANISM_SIGNAL_PATH, ORGANISM_SYSTEMS
from .silicon_architecture import (
    BLOCKED_HARDWARE_AUTONOMY,
    EXECUTION_ZONES,
    HUMAN_AUTHORITY_FINAL,
    INDEPENDENT_HARDWARE_AUTHORITY,
    SILICON_GATES,
    validate_silicon_contract,
)
from .silicon_reference_platform import validate_reference_platform_contract

SOC_NAME = "OAP Sovereign Digital SoC"
SOC_VERSION = "0.1.0"
SOC_STATUS = "SOFTWARE_SIMULATOR"
PHYSICAL_CHIP_BUILT = False
RTL_IMPLEMENTED = False
FPGA_LOADED = False
EXTERNAL_EXECUTION_ENABLED = False
INDEPENDENT_SOC_AUTHORITY = False
COGNITIVE_AUTHORITY = "SMI Brain"
FINAL_AUTHORITY = "Human Authority"

# Thirteen future SoC functional blocks plus eight low-level substrate blocks.
# These are simulator concepts, not claims that RTL or silicon exists.
DIGITAL_SOC_BLOCKS: tuple[dict[str, str], ...] = (
    {"id": "cpu", "name": "CPU Cluster", "role": "General compute"},
    {"id": "npu", "name": "NPU", "role": "Bounded intelligence acceleration"},
    {"id": "gpu", "name": "GPU", "role": "Parallel and visual acceleration"},
    {"id": "secure_enclave", "name": "Secure Enclave", "role": "Identity and key isolation"},
    {"id": "hrm_integrity", "name": "HRM Integrity Engine", "role": "Receipt and memory integrity"},
    {"id": "guardian", "name": "Guardian Policy Engine", "role": "Consequence and policy enforcement"},
    {"id": "nexus", "name": "NEXUS Interconnect", "role": "Typed internal message transport"},
    {"id": "media_dsp", "name": "Media DSP", "role": "Audio and media signal processing"},
    {"id": "network", "name": "Network Accelerator", "role": "Bounded network processing"},
    {"id": "memory", "name": "Encrypted Memory Controller", "role": "Protected memory access"},
    {"id": "storage", "name": "Secure Storage Controller", "role": "Protected persistent-state abstraction"},
    {"id": "sensor", "name": "Sensor Hub", "role": "Consented sensor event abstraction"},
    {"id": "power", "name": "Power and Thermal Controller", "role": "Homeostasis telemetry abstraction"},
    {"id": "boot_rom", "name": "Boot ROM and Root of Trust", "role": "Immutable boot-root simulation"},
    {"id": "entropy", "name": "Entropy Engine", "role": "Randomness-source abstraction"},
    {"id": "iommu", "name": "IOMMU and Isolation Engine", "role": "Zone and device-memory isolation"},
    {"id": "interrupts", "name": "Interrupt Controller", "role": "Prioritised event signalling"},
    {"id": "attestation", "name": "Attestation Engine", "role": "Device-state proof abstraction"},
    {"id": "watchdog", "name": "Watchdog and Reflex Controller", "role": "Bounded recovery signalling"},
    {"id": "audit", "name": "Immutable Audit Event Recorder", "role": "Append-only simulator receipts"},
    {"id": "recovery", "name": "Recovery Controller", "role": "Known-good rollback simulation"},
)

REGISTER_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {"name": "SOC_ID", "access": "RO", "reset": "OAP-SOC-SIM-V0"},
    {"name": "SOC_REVISION", "access": "RO", "reset": SOC_VERSION},
    {"name": "BOOT_STATE", "access": "INTERNAL", "reset": "RESET"},
    {"name": "GUARDIAN_STATE", "access": "INTERNAL", "reset": "ENFORCING"},
    {"name": "ACTIVE_ZONE", "access": "INTERNAL", "reset": "Recovery Zone"},
    {"name": "IRQ_PENDING", "access": "INTERNAL", "reset": 0},
    {"name": "NEXUS_TX_COUNT", "access": "INTERNAL", "reset": 0},
    {"name": "HRM_RECEIPT_COUNT", "access": "INTERNAL", "reset": 0},
    {"name": "LAST_BLOCK_REASON", "access": "INTERNAL", "reset": None},
    {"name": "REAL_EXECUTION_COUNT", "access": "RO", "reset": 0},
)

INTERRUPT_LINES = (
    "WATCHDOG",
    "GUARDIAN_BLOCK",
    "NEXUS_MESSAGE",
    "HRM_RECEIPT",
    "SENSOR_EVENT",
    "RECOVERY_REQUEST",
    "THERMAL_ALERT",
)

NEXUS_MESSAGE_TYPES = (
    "SIGNAL",
    "CONTEXT",
    "RECOMMENDATION",
    "APPROVAL_RECEIPT",
    "ORGAN_INTENT",
    "HEALTH_EVENT",
    "AUDIT_EVENT",
)

# Digital SoC messages may model the canonical organism path, but the SoC is
# never itself inserted as a second cognitive authority.
NEXUS_ENDPOINTS = tuple(dict.fromkeys((*ORGANISM_SIGNAL_PATH, *(organ["name"] for organ in BODY_ORGANS))))


def _gate_keys() -> tuple[str, ...]:
    return tuple(f"{family}.{gate}" for family, gates in SILICON_GATES.items() for gate in gates)


ALL_GATE_KEYS = _gate_keys()


def validate_digital_soc_contract() -> None:
    """Fail closed if the simulator drifts outside OAP constitutional bounds."""

    validate_silicon_contract()
    validate_reference_platform_contract()
    brains = tuple(system["name"] for system in ORGANISM_SYSTEMS if system["anatomy"] == "Brain")
    if brains != ("SMI",):
        raise ValueError("SMI must remain the single OAP Brain")
    if COGNITIVE_AUTHORITY != "SMI Brain":
        raise ValueError("The Digital SoC may not become a second Brain")
    if FINAL_AUTHORITY != "Human Authority" or not HUMAN_AUTHORITY_FINAL:
        raise ValueError("Human Authority must remain final")
    if INDEPENDENT_HARDWARE_AUTHORITY or INDEPENDENT_SOC_AUTHORITY:
        raise ValueError("The Digital SoC may not gain independent authority")
    if PHYSICAL_CHIP_BUILT or RTL_IMPLEMENTED or FPGA_LOADED:
        raise ValueError("v0 is a software simulator and may not claim physical implementation")
    if EXTERNAL_EXECUTION_ENABLED:
        raise ValueError("v0 may not perform external execution")
    if len(DIGITAL_SOC_BLOCKS) != 21:
        raise ValueError("Digital SoC v0 must retain the 21-block simulator anatomy")
    if len(ALL_GATE_KEYS) != 21 or len(set(ALL_GATE_KEYS)) != 21:
        raise ValueError("Digital SoC v0 must inherit exactly 21 unique silicon gates")
    if tuple(EXECUTION_ZONES) != (
        "Public Zone",
        "Private Zone",
        "SMI Zone",
        "HRM Zone",
        "Guardian Zone",
        "Device Zone",
        "Recovery Zone",
    ):
        raise ValueError("Execution-zone contract has drifted")


def digital_soc_contract() -> dict[str, Any]:
    """Return the read-only simulator architecture contract."""

    validate_digital_soc_contract()
    return {
        "name": SOC_NAME,
        "version": SOC_VERSION,
        "status": SOC_STATUS,
        "blocks": DIGITAL_SOC_BLOCKS,
        "registers": REGISTER_DEFINITIONS,
        "interrupt_lines": INTERRUPT_LINES,
        "nexus_message_types": NEXUS_MESSAGE_TYPES,
        "nexus_endpoints": NEXUS_ENDPOINTS,
        "execution_zones": EXECUTION_ZONES,
        "gate_keys": ALL_GATE_KEYS,
        "cognitive_authority": COGNITIVE_AUTHORITY,
        "final_authority": FINAL_AUTHORITY,
        "physical_chip_built": PHYSICAL_CHIP_BUILT,
        "rtl_implemented": RTL_IMPLEMENTED,
        "fpga_loaded": FPGA_LOADED,
        "external_execution_enabled": EXTERNAL_EXECUTION_ENABLED,
        "independent_soc_authority": INDEPENDENT_SOC_AUTHORITY,
    }


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


@dataclass
class SovereignDigitalSoCSimulator:
    """In-memory, fail-closed model of the OAP Sovereign Digital SoC v0."""

    registers: dict[str, Any] = field(default_factory=dict)
    interrupts: list[str] = field(default_factory=list)
    nexus_messages: list[dict[str, Any]] = field(default_factory=list)
    receipts: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_digital_soc_contract()
        self.reset()

    def reset(self) -> None:
        """Reset simulator state without touching any external system."""

        self.registers = {item["name"]: item["reset"] for item in REGISTER_DEFINITIONS}
        self.interrupts.clear()
        self.nexus_messages.clear()
        self.receipts.clear()

    def read_register(self, name: str) -> Any:
        """Read a simulator register."""

        if name not in self.registers:
            raise KeyError(f"Unknown Digital SoC register: {name}")
        return self.registers[name]

    def _raise_interrupt(self, line: str) -> None:
        if line not in INTERRUPT_LINES:
            raise ValueError(f"Unknown interrupt line: {line}")
        self.interrupts.append(line)
        self.registers["IRQ_PENDING"] = len(self.interrupts)

    def acknowledge_interrupt(self) -> str | None:
        """Acknowledge the oldest simulated interrupt."""

        if not self.interrupts:
            return None
        line = self.interrupts.pop(0)
        self.registers["IRQ_PENDING"] = len(self.interrupts)
        return line

    @staticmethod
    def _family_result(family: str, evidence: Mapping[str, bool]) -> dict[str, Any]:
        gates = SILICON_GATES[family]
        results = tuple(
            {
                "gate": gate,
                "key": f"{family}.{gate}",
                "passed": evidence.get(f"{family}.{gate}") is True,
            }
            for gate in gates
        )
        return {
            "family": family,
            "passed": all(result["passed"] for result in results),
            "results": results,
        }

    def evaluate_21_gates(self, evidence: Mapping[str, bool]) -> dict[str, Any]:
        """Evaluate all 7x3 gates using explicit boolean evidence only."""

        families = tuple(self._family_result(family, evidence) for family in SILICON_GATES)
        passed_count = sum(
            1
            for family in families
            for result in family["results"]
            if result["passed"]
        )
        return {
            "passed": passed_count == 21,
            "passed_count": passed_count,
            "gate_count": 21,
            "families": families,
        }

    def boot(self, hardware_evidence: Mapping[str, bool]) -> dict[str, Any]:
        """Simulate trusted boot using all seven hardware-trust gates."""

        family = self._family_result("hardware_trust", hardware_evidence)
        if not family["passed"]:
            missing = tuple(result["gate"] for result in family["results"] if not result["passed"])
            self.registers["BOOT_STATE"] = "BLOCKED"
            self.registers["ACTIVE_ZONE"] = "Recovery Zone"
            self.registers["LAST_BLOCK_REASON"] = f"hardware_trust:{','.join(missing)}"
            self._raise_interrupt("GUARDIAN_BLOCK")
            return {
                "booted": False,
                "state": "BLOCKED",
                "missing_gates": missing,
                "real_hardware_touched": False,
            }

        self.registers["BOOT_STATE"] = "READY"
        self.registers["ACTIVE_ZONE"] = "Device Zone"
        self.registers["LAST_BLOCK_REASON"] = None
        self._record_receipt("BOOT_READY", {"hardware_trust": True})
        return {
            "booted": True,
            "state": "READY",
            "missing_gates": (),
            "real_hardware_touched": False,
        }

    def nexus_send(
        self,
        *,
        source: str,
        target: str,
        message_type: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Send a typed in-memory NEXUS message between canonical endpoints."""

        if self.registers["BOOT_STATE"] != "READY":
            raise RuntimeError("Digital SoC must be READY before NEXUS messages are accepted")
        if source not in NEXUS_ENDPOINTS or target not in NEXUS_ENDPOINTS:
            raise ValueError("NEXUS source and target must be canonical organism endpoints")
        if message_type not in NEXUS_MESSAGE_TYPES:
            raise ValueError(f"Unsupported NEXUS message type: {message_type}")

        message = {
            "sequence": len(self.nexus_messages) + 1,
            "source": source,
            "target": target,
            "type": message_type,
            "payload": dict(payload),
            "external_delivery": False,
        }
        self.nexus_messages.append(message)
        self.registers["NEXUS_TX_COUNT"] = len(self.nexus_messages)
        self._raise_interrupt("NEXUS_MESSAGE")
        return dict(message)

    def request_consequential_action(
        self,
        action: str,
        gate_evidence: Mapping[str, bool],
    ) -> dict[str, Any]:
        """Simulate consequence gating; never perform the requested real action."""

        if action not in BLOCKED_HARDWARE_AUTONOMY:
            raise ValueError("Action is not registered as a consequential hardware boundary")
        gates = self.evaluate_21_gates(gate_evidence)
        if not gates["passed"]:
            self.registers["LAST_BLOCK_REASON"] = "21_gate_evidence_incomplete"
            self._raise_interrupt("GUARDIAN_BLOCK")
            receipt = self._record_receipt(
                "ACTION_BLOCKED",
                {"action": action, "passed_count": gates["passed_count"]},
            )
            return {
                "action": action,
                "simulation_result": "BLOCKED",
                "gate_result": gates,
                "receipt": receipt,
                "real_execution_performed": False,
            }

        self.registers["LAST_BLOCK_REASON"] = None
        receipt = self._record_receipt(
            "ACTION_AUTHORIZED_FOR_SIMULATION_ONLY",
            {"action": action, "passed_count": 21},
        )
        return {
            "action": action,
            "simulation_result": "AUTHORIZED_FOR_SIMULATION_ONLY",
            "gate_result": gates,
            "receipt": receipt,
            "real_execution_performed": False,
        }

    def _record_receipt(self, event: str, details: Mapping[str, Any]) -> dict[str, Any]:
        body = {
            "sequence": len(self.receipts) + 1,
            "event": event,
            "details": dict(details),
            "store": "SIMULATED_HRM_ONLY",
        }
        digest = hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()
        receipt = {**body, "sha256": digest}
        self.receipts.append(receipt)
        self.registers["HRM_RECEIPT_COUNT"] = len(self.receipts)
        self._raise_interrupt("HRM_RECEIPT")
        return dict(receipt)

    def status(self) -> dict[str, Any]:
        """Return an immutable-style snapshot of current simulator state."""

        return {
            "name": SOC_NAME,
            "version": SOC_VERSION,
            "status": SOC_STATUS,
            "registers": dict(self.registers),
            "interrupts": tuple(self.interrupts),
            "nexus_message_count": len(self.nexus_messages),
            "receipt_count": len(self.receipts),
            "cognitive_authority": COGNITIVE_AUTHORITY,
            "final_authority": FINAL_AUTHORITY,
            "external_execution_enabled": False,
            "real_execution_count": 0,
            "physical_chip_built": False,
            "rtl_implemented": False,
            "fpga_loaded": False,
        }
