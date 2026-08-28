# OAP Sovereign Digital SoC v0.2

## Purpose

v0.2 makes the OAP Sovereign Digital SoC simulator more hardware-shaped while remaining entirely software-only and in-memory.

It extends v0 with:

- a deterministic memory map,
- memory-mapped I/O (MMIO),
- protected execution-zone memory,
- bus read/write transactions,
- prioritised interrupts,
- simulated DMA with IOMMU-style region domains,
- measured boot digests,
- simulated attestation,
- cycle/event tracing,
- one simulation-only interface for each of the 13 OAP body organs.

## Constitutional boundary

SMI remains the single OAP Brain. Human Authority remains final.

v0.2 does **not**:

- access real MMIO,
- perform real DMA,
- produce hardware-backed attestation,
- execute a real body organ action,
- deploy code,
- change permissions,
- move money,
- control a vehicle,
- activate telecom services,
- touch production infrastructure,
- implement RTL,
- load an FPGA,
- claim a fabricated OAP chip exists.

## Memory map

The simulator defines ten non-overlapping regions:

1. Boot ROM — Recovery Zone
2. Guardian MMIO — Guardian Zone
3. NEXUS MMIO — Device Zone
4. Interrupt MMIO — Device Zone
5. Attestation MMIO — Guardian Zone
6. HRM Protected Memory — HRM Zone
7. SMI Protected Memory — SMI Zone
8. Private Memory — Private Zone
9. Public Memory — Public Zone
10. Device Buffer — Device Zone

Protected HRM, SMI, Private and Guardian regions fail closed when accessed from another zone.

## MMIO

Seven simulated MMIO registers represent Guardian state, NEXUS state, interrupt state and attestation state. Access permissions are enforced in software. A read-only register cannot be written and a write-only register cannot be read.

No physical memory address is accessed.

## Interrupt priorities

The software interrupt controller uses this priority order:

1. Guardian Block
2. Thermal Alert
3. Watchdog
4. Recovery Request
5. HRM Receipt
6. NEXUS Message
7. Sensor Event

This makes protection/recovery events pre-empt ordinary simulated device traffic.

## DMA and IOMMU simulation

A device receives an explicit list of memory regions it may use. A DMA request is permitted only when both source and target belong to that domain.

Cross-domain requests are blocked and raise a Guardian interrupt.

Successful requests only copy bytes inside Python memory. `real_dma` is always false.

## Measured boot

After all seven Hardware Trust gates pass, v0.2 creates SHA-256 measurements for simulated boot components such as:

- Boot ROM
- kernel
- OAP runtime
- Guardian

These measurements are deterministic evidence inside the simulator. They are not TPM PCRs, secure-enclave measurements or hardware root-of-trust claims.

## Simulated attestation

The attestation path binds:

- a caller nonce,
- boot measurements,
- SoC simulator version,
- 21-gate count,
- SMI as cognitive authority,
- Human Authority as final authority.

The result is hashed but explicitly marked:

- `hardware_backed: false`
- `store: SIMULATED_ONLY`

## Organ interfaces

All 13 canonical OAP body organs receive a simulation-only interface. An organ intent travels as a typed NEXUS `ORGAN_INTENT` message from the Living Kernel to the organ endpoint.

The returned record always states `organ_execution_performed: false`.

This creates a hardware/software boundary model without granting the SoC authority to run an organ.

## Why this milestone matters

v0 proved the constitutional SoC model.

v0.2 introduces the abstractions needed before RTL work can be sensible:

**memory map → MMIO → bus → interrupts → isolation → DMA/IOMMU → measured boot → attestation → organ interfaces**

The next hardware-development milestone should be a small **RTL proof slice**, not a complete chip: normally Guardian + NEXUS + interrupt/HRM receipt logic around a simple open RISC-V-compatible test environment or FPGA simulation.
