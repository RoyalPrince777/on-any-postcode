# OAP Silicon Reference Platform v1

Status: **SPECIFICATION READY**

This document defines the Generation 1 hardware contract beneath the OAP Digital Organism. It does not claim that a physical OAP device, custom board, FPGA, secure element deployment, or chip has been manufactured.

## Mission

**Own the intelligence architecture before owning the transistor.**

Locked design principle:

- Human Authority above software.
- Software above hardware execution.
- Hardware proves, isolates and enforces — it does not rule.

## Generation 1 objective

Move from the current Generation 0 Android/Termux Home Node to a dedicated, vendor-neutral Home Node that can run continuously, prove its software revision and trust state, recover safely, and preserve the existing OAP Human Authority boundary.

The specification does **not** force a purchase. A real bill of materials must be selected later using current price, availability, security support, power use, supply-chain evidence and Human Authority approval.

## Seven hardware capability classes

1. **General Compute** — 64-bit CPU, virtual memory, thermal telemetry and sustained background operation.
2. **Memory and Storage** — at least 4 GiB RAM, persistent storage, encryption capability and a recoverable system image.
3. **Hardware Trust** — verified/secure boot capability, device-unique key storage, signed update verification and recovery/rollback.
4. **Network** — Ethernet or Wi-Fi, encrypted transport, local-network operation and outbound connectivity control.
5. **AI and Media Acceleration** — optional NPU/GPU/media acceleration, always with a software fallback.
6. **Power and Recovery** — clean shutdown, power-loss recovery, watchdog capability and power/temperature observability.
7. **Local I/O** — local recovery/console access and a service interface.

## Software baseline

The Generation 1 node must support the OAP Home Node worker, OAP CORE, the bounded SMI runtime, Guardian policy, HRM receipts, PostgreSQL client access and signed update verification on a 64-bit Linux base.

## Trust boot path

**Hardware Root → Boot Firmware Verification → Kernel Verification → OAP Runtime Verification → Guardian Policy Load → OAP CORE Start → SMI Bounded Runtime Start → Home Node Heartbeat**

A device is not considered healthy merely because it powers on. The live OAP heartbeat must also become fresh.

## Governed update path

1. Human Authority selects a revision.
2. Signature and provenance are verified.
3. Compatibility checks pass.
4. A recovery point is prepared.
5. The update is staged.
6. Human Authority approves activation.
7. The node activates the revision.
8. Health and heartbeat are verified.
9. HRM records the outcome.

OAP software may observe, validate, stage or propose. It may not independently approve consequential activation.

## Recovery contract

Generation 1 must provide a known-good image, local recovery access, configuration backup without secret disclosure, rollback/recovery after failed activation and proof of a fresh heartbeat after recovery.

## Operational signals

The node should expose coarse, non-secret operational evidence for device identity, boot integrity, software revision, heartbeat freshness, CPU load, memory pressure, storage health, temperature, power, network, Guardian state and dead-letter count.

## Seven acceptance gates

A physical candidate remains **NOT PROVEN** until all seven are evidenced:

1. Canonical OAP Silicon contract validates.
2. Verified boot-chain evidence exists.
3. Unique device identity evidence exists.
4. Encrypted-storage evidence exists.
5. OAP worker is ready with a fresh heartbeat.
6. Rollback/recovery has been genuinely tested.
7. Human Authority boundary is verified.

Passing these gates means a candidate satisfies the reference contract. It does not grant the hardware independent authority.

## Consequential hardware actions

Firmware activation, trust-key rotation, boot-policy change, permission change, production revision activation, network-policy expansion and factory reset remain Human Authority-gated.

## Current truth

- OAP Silicon Architecture v1: **built in software and governed by tests**.
- Generation 0 Termux Home Node: **current active reference runtime** when live heartbeat evidence is present.
- Generation 1 reference specification: **ready**.
- Generation 1 physical device: **not yet built or purchased**.
- Custom OAP silicon/SoC: **not required now**.

The next physical milestone, when justified, is to evaluate real off-the-shelf ARM or RISC-V candidates against this contract rather than buying hardware first and designing governance around it afterward.
