"""Hardware-shaped extension for the software-only OAP Sovereign Digital SoC v0.2.

This module extends the v0 simulator with a deterministic memory map, MMIO,
protected memory regions, bus transactions, prioritised interrupts, DMA/IOMMU
checks, boot measurements, attestation, event tracing and organ interfaces.
Everything remains in memory. No physical hardware, production system, external
network, payment, permission, deployment or other consequential action is
performed here.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any

from .organism import BODY_ORGANS
from .silicon_architecture import EXECUTION_ZONES, SILICON_GATES
from .sovereign_digital_soc import (
    ALL_GATE_KEYS,
    COGNITIVE_AUTHORITY,
    EXTERNAL_EXECUTION_ENABLED,
    FINAL_AUTHORITY,
    SovereignDigitalSoCSimulator,
    validate_digital_soc_contract,
)

SOC_V02_VERSION = "0.2.0"
SOC_V02_STATUS = "HARDWARE_SHAPED_SOFTWARE_SIMULATOR"
REAL_DMA_ENABLED = False
REAL_MMIO_ENABLED = False
REAL_ATTESTATION_ENABLED = False
REAL_ORGAN_EXECUTION_ENABLED = False

MEMORY_MAP: tuple[dict[str, Any], ...] = (
    {"name": "BOOT_ROM", "base": 0x0000_0000, "size": 0x0001_0000, "zone": "Recovery Zone", "access": "RX"},
    {"name": "GUARDIAN_MMIO", "base": 0x1000_0000, "size": 0x0000_1000, "zone": "Guardian Zone", "access": "RW"},
    {"name": "NEXUS_MMIO", "base": 0x1000_1000, "size": 0x0000_1000, "zone": "Device Zone", "access": "RW"},
    {"name": "IRQ_MMIO", "base": 0x1000_2000, "size": 0x0000_1000, "zone": "Device Zone", "access": "RW"},
    {"name": "ATTEST_MMIO", "base": 0x1000_3000, "size": 0x0000_1000, "zone": "Guardian Zone", "access": "RO"},
    {"name": "HRM_PROTECTED", "base": 0x2000_0000, "size": 0x0010_0000, "zone": "HRM Zone", "access": "RW"},
    {"name": "SMI_PROTECTED", "base": 0x2100_0000, "size": 0x0010_0000, "zone": "SMI Zone", "access": "RW"},
    {"name": "PRIVATE_MEMORY", "base": 0x2200_0000, "size": 0x0010_0000, "zone": "Private Zone", "access": "RW"},
    {"name": "PUBLIC_MEMORY", "base": 0x2300_0000, "size": 0x0010_0000, "zone": "Public Zone", "access": "RW"},
    {"name": "DEVICE_BUFFER", "base": 0x2400_0000, "size": 0x0010_0000, "zone": "Device Zone", "access": "RW"},
)

MMIO_REGISTERS: tuple[dict[str, Any], ...] = (
    {"name": "GUARDIAN_STATUS", "address": 0x1000_0000, "access": "RO", "reset": 1},
    {"name": "GUARDIAN_LAST_BLOCK", "address": 0x1000_0008, "access": "RO", "reset": 0},
    {"name": "NEXUS_TX", "address": 0x1000_1000, "access": "WO", "reset": 0},
    {"name": "NEXUS_STATUS", "address": 0x1000_1008, "access": "RO", "reset": 0},
    {"name": "IRQ_PENDING", "address": 0x1000_2000, "access": "RO", "reset": 0},
    {"name": "IRQ_ACK", "address": 0x1000_2008, "access": "WO", "reset": 0},
    {"name": "ATTEST_STATUS", "address": 0x1000_3000, "access": "RO", "reset": 0},
)

INTERRUPT_PRIORITIES = {
    "GUARDIAN_BLOCK": 0,
    "THERMAL_ALERT": 1,
    "WATCHDOG": 2,
    "RECOVERY_REQUEST": 3,
    "HRM_RECEIPT": 4,
    "NEXUS_MESSAGE": 5,
    "SENSOR_EVENT": 6,
}

ORGAN_INTERFACES: tuple[dict[str, str], ...] = tuple(
    {
        "organ_id": organ["id"],
        "organ_name": organ["name"],
        "interface": f"ORGAN::{organ['id']}",
        "mode": "SIMULATION_ONLY",
    }
    for organ in BODY_ORGANS
)


def _stable_hash(value: Mapping[str, Any]) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def validate_v02_contract() -> None:
    """Fail closed if v0.2 becomes real hardware control or a second Brain."""

    validate_digital_soc_contract()
    if COGNITIVE_AUTHORITY != "SMI Brain":
        raise ValueError("SMI must remain the single Brain")
    if FINAL_AUTHORITY != "Human Authority":
        raise ValueError("Human Authority must remain final")
    if EXTERNAL_EXECUTION_ENABLED:
        raise ValueError("External execution must remain disabled")
    if any((REAL_DMA_ENABLED, REAL_MMIO_ENABLED, REAL_ATTESTATION_ENABLED, REAL_ORGAN_EXECUTION_ENABLED)):
        raise ValueError("v0.2 must remain a software-only simulator")
    if len(ALL_GATE_KEYS) != 21:
        raise ValueError("v0.2 must inherit all 21 silicon gates")
    if len(ORGAN_INTERFACES) != 13:
        raise ValueError("v0.2 must expose exactly 13 simulated organ interfaces")
    if set(INTERRUPT_PRIORITIES) != {
        "WATCHDOG",
        "GUARDIAN_BLOCK",
        "NEXUS_MESSAGE",
        "HRM_RECEIPT",
        "SENSOR_EVENT",
        "RECOVERY_REQUEST",
        "THERMAL_ALERT",
    }:
        raise ValueError("Interrupt contract drifted")
    ranges = sorted((region["base"], region["base"] + region["size"], region["name"]) for region in MEMORY_MAP)
    for previous, current in pairwise(ranges):
        if previous[1] > current[0]:
            raise ValueError(f"Memory regions overlap: {previous[2]} and {current[2]}")


@dataclass
class SovereignDigitalSoCV02Simulator(SovereignDigitalSoCSimulator):
    """Hardware-shaped but entirely in-memory Digital SoC v0.2 simulator."""

    memory: dict[int, int] = field(default_factory=dict)
    mmio: dict[int, int] = field(default_factory=dict)
    bus_trace: list[dict[str, Any]] = field(default_factory=list)
    event_trace: list[dict[str, Any]] = field(default_factory=list)
    boot_measurements: list[dict[str, str]] = field(default_factory=list)
    dma_domains: dict[str, tuple[str, ...]] = field(default_factory=dict)
    cycle: int = 0

    def __post_init__(self) -> None:
        validate_v02_contract()
        super().__post_init__()
        self.mmio = {item["address"]: item["reset"] for item in MMIO_REGISTERS}

    def reset(self) -> None:
        super().reset()
        self.memory.clear()
        self.mmio = {item["address"]: item["reset"] for item in MMIO_REGISTERS}
        self.bus_trace.clear()
        self.event_trace.clear()
        self.boot_measurements.clear()
        self.dma_domains.clear()
        self.cycle = 0

    def _tick(self, event: str, details: Mapping[str, Any]) -> None:
        self.cycle += 1
        self.event_trace.append({"cycle": self.cycle, "event": event, "details": dict(details)})

    @staticmethod
    def _region_for(address: int) -> dict[str, Any]:
        for region in MEMORY_MAP:
            if region["base"] <= address < region["base"] + region["size"]:
                return region
        raise ValueError(f"Address outside Digital SoC memory map: 0x{address:08x}")

    @staticmethod
    def _mmio_definition(address: int) -> dict[str, Any]:
        for register in MMIO_REGISTERS:
            if register["address"] == address:
                return register
        raise ValueError(f"Unknown MMIO register: 0x{address:08x}")

    def bus_read(self, address: int, *, requester_zone: str) -> int:
        """Simulate a memory/MMIO bus read with zone enforcement."""

        region = self._region_for(address)
        if requester_zone not in EXECUTION_ZONES:
            raise ValueError("Unknown requester zone")
        if region["zone"] in {"HRM Zone", "SMI Zone", "Private Zone", "Guardian Zone"} and requester_zone != region["zone"]:
            self._tick("BUS_BLOCK", {"address": address, "requester_zone": requester_zone, "target_zone": region["zone"]})
            raise PermissionError("Protected memory region access denied")
        if "R" not in region["access"]:
            raise PermissionError("Region is not readable")

        if region["name"].endswith("MMIO"):
            definition = self._mmio_definition(address)
            if "R" not in definition["access"]:
                raise PermissionError("MMIO register is not readable")
            value = self.mmio[address]
        else:
            value = self.memory.get(address, 0)
        record = {"cycle": self.cycle + 1, "op": "READ", "address": address, "zone": requester_zone, "value": value}
        self.bus_trace.append(record)
        self._tick("BUS_READ", record)
        return value

    def bus_write(self, address: int, value: int, *, requester_zone: str) -> None:
        """Simulate a memory/MMIO write; no real MMIO is ever touched."""

        region = self._region_for(address)
        if requester_zone not in EXECUTION_ZONES:
            raise ValueError("Unknown requester zone")
        if region["zone"] in {"HRM Zone", "SMI Zone", "Private Zone", "Guardian Zone"} and requester_zone != region["zone"]:
            self._tick("BUS_BLOCK", {"address": address, "requester_zone": requester_zone, "target_zone": region["zone"]})
            raise PermissionError("Protected memory region access denied")
        if "W" not in region["access"]:
            raise PermissionError("Region is not writable")

        if region["name"].endswith("MMIO"):
            definition = self._mmio_definition(address)
            if "W" not in definition["access"]:
                raise PermissionError("MMIO register is not writable")
            self.mmio[address] = int(value)
        else:
            self.memory[address] = int(value) & 0xFF
        record = {"cycle": self.cycle + 1, "op": "WRITE", "address": address, "zone": requester_zone, "value": int(value)}
        self.bus_trace.append(record)
        self._tick("BUS_WRITE", record)

    def raise_prioritised_interrupt(self, line: str) -> None:
        """Raise an interrupt and keep the pending list ordered by priority."""

        self._raise_interrupt(line)
        self.interrupts.sort(key=lambda item: INTERRUPT_PRIORITIES[item])
        self.registers["IRQ_PENDING"] = len(self.interrupts)
        self.mmio[0x1000_2000] = len(self.interrupts)
        self._tick("IRQ_RAISED", {"line": line, "priority": INTERRUPT_PRIORITIES[line]})

    def acknowledge_interrupt(self) -> str | None:
        line = super().acknowledge_interrupt()
        self.mmio[0x1000_2000] = len(self.interrupts)
        if line is not None:
            self._tick("IRQ_ACK", {"line": line})
        return line

    def configure_dma_domain(self, device: str, allowed_regions: tuple[str, ...]) -> None:
        """Configure a simulated IOMMU domain after validating named regions."""

        region_names = {region["name"] for region in MEMORY_MAP}
        if not allowed_regions or any(region not in region_names for region in allowed_regions):
            raise ValueError("DMA domain contains unknown or empty region set")
        self.dma_domains[device] = tuple(allowed_regions)
        self._tick("IOMMU_DOMAIN", {"device": device, "regions": allowed_regions})

    def dma_transfer(self, device: str, source: int, target: int, length: int) -> dict[str, Any]:
        """Simulate DMA only when both source and target belong to the device domain."""

        if length <= 0 or length > 4096:
            raise ValueError("DMA simulation length must be between 1 and 4096 bytes")
        allowed = set(self.dma_domains.get(device, ()))
        source_region = self._region_for(source)
        target_region = self._region_for(target)
        permitted = source_region["name"] in allowed and target_region["name"] in allowed
        if not permitted:
            self.raise_prioritised_interrupt("GUARDIAN_BLOCK")
            self._tick("DMA_BLOCK", {"device": device, "source": source, "target": target})
            return {"permitted": False, "bytes": 0, "real_dma": False}

        for offset in range(length):
            self.memory[target + offset] = self.memory.get(source + offset, 0)
        self._tick("DMA_COMPLETE", {"device": device, "source": source, "target": target, "bytes": length})
        return {"permitted": True, "bytes": length, "real_dma": False}

    def boot(self, hardware_evidence: Mapping[str, bool], *, components: Mapping[str, str] | None = None) -> dict[str, Any]:
        result = super().boot(hardware_evidence)
        if not result["booted"]:
            self._tick("BOOT_BLOCKED", {"missing_gates": result["missing_gates"]})
            return result

        components = components or {
            "boot_rom": "oap-boot-rom-sim",
            "kernel": "oap-linux-sim",
            "runtime": "oap-runtime-sim",
            "guardian": "oap-guardian-sim",
        }
        self.boot_measurements = [
            {"component": name, "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest()}
            for name, value in sorted(components.items())
        ]
        self.mmio[0x1000_3000] = 1
        self._tick("BOOT_MEASURED", {"measurement_count": len(self.boot_measurements)})
        return {**result, "measurements": tuple(self.boot_measurements)}

    def attest(self, nonce: str) -> dict[str, Any]:
        """Return a deterministic simulator attestation; never a hardware-backed proof."""

        if self.registers["BOOT_STATE"] != "READY":
            raise RuntimeError("Attestation requires READY boot state")
        if not nonce:
            raise ValueError("Attestation nonce is required")
        payload = {
            "soc": "OAP Sovereign Digital SoC",
            "version": SOC_V02_VERSION,
            "nonce": nonce,
            "boot_measurements": tuple(self.boot_measurements),
            "gate_count": len(ALL_GATE_KEYS),
            "cognitive_authority": COGNITIVE_AUTHORITY,
            "final_authority": FINAL_AUTHORITY,
            "hardware_backed": False,
            "store": "SIMULATED_ONLY",
        }
        digest = _stable_hash(payload)
        self._tick("ATTESTATION", {"sha256": digest})
        return {**payload, "sha256": digest}

    def organ_signal(self, organ_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Route a simulated organ intent through NEXUS without executing the organ."""

        match = next((item for item in ORGAN_INTERFACES if item["organ_id"] == organ_id), None)
        if match is None:
            raise ValueError("Unknown OAP organ interface")
        message = self.nexus_send(
            source="Living Kernel",
            target=match["organ_name"],
            message_type="ORGAN_INTENT",
            payload={"interface": match["interface"], **dict(payload)},
        )
        self._tick("ORGAN_SIGNAL", {"organ_id": organ_id, "sequence": message["sequence"]})
        return {**message, "organ_execution_performed": False}

    def v02_status(self) -> dict[str, Any]:
        return {
            "version": SOC_V02_VERSION,
            "status": SOC_V02_STATUS,
            "memory_regions": len(MEMORY_MAP),
            "mmio_registers": len(MMIO_REGISTERS),
            "organ_interfaces": len(ORGAN_INTERFACES),
            "bus_transactions": len(self.bus_trace),
            "events": len(self.event_trace),
            "boot_measurements": len(self.boot_measurements),
            "dma_domains": len(self.dma_domains),
            "real_dma_enabled": REAL_DMA_ENABLED,
            "real_mmio_enabled": REAL_MMIO_ENABLED,
            "real_attestation_enabled": REAL_ATTESTATION_ENABLED,
            "real_organ_execution_enabled": REAL_ORGAN_EXECUTION_ENABLED,
            "real_execution_count": self.registers["REAL_EXECUTION_COUNT"],
            "cognitive_authority": COGNITIVE_AUTHORITY,
            "final_authority": FINAL_AUTHORITY,
        }


def v02_contract() -> dict[str, Any]:
    validate_v02_contract()
    return {
        "version": SOC_V02_VERSION,
        "status": SOC_V02_STATUS,
        "memory_map": MEMORY_MAP,
        "mmio_registers": MMIO_REGISTERS,
        "interrupt_priorities": INTERRUPT_PRIORITIES,
        "organ_interfaces": ORGAN_INTERFACES,
        "silicon_gates": SILICON_GATES,
        "gate_count": len(ALL_GATE_KEYS),
        "cognitive_authority": COGNITIVE_AUTHORITY,
        "final_authority": FINAL_AUTHORITY,
        "real_dma_enabled": REAL_DMA_ENABLED,
        "real_mmio_enabled": REAL_MMIO_ENABLED,
        "real_attestation_enabled": REAL_ATTESTATION_ENABLED,
        "real_organ_execution_enabled": REAL_ORGAN_EXECUTION_ENABLED,
    }
