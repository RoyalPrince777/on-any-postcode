# OAP Sovereign Digital SoC v0

Status: **software simulator**

The OAP Sovereign Digital SoC v0 is the first executable digital model of the future OAP hardware substrate. It exists below the OAP Digital Organism and does not become another brain, authority, or production executor.

## Constitutional position

The authority and organism relationship remains:

**Human Authority → OAP software → Guardian policy → simulated hardware execution**

The cognitive path remains:

**OAP CORE → NEXUS → Thalamus → SMI Brain → Judgement → Human Authority → Living Kernel → Body Organ → HRM**

SMI remains the single OAP Brain. The Digital SoC supports computation, isolation, signalling, integrity and simulated execution only.

## v0 simulator anatomy

The simulator contains 21 digital blocks:

1. CPU Cluster
2. NPU
3. GPU
4. Secure Enclave
5. HRM Integrity Engine
6. Guardian Policy Engine
7. NEXUS Interconnect
8. Media DSP
9. Network Accelerator
10. Encrypted Memory Controller
11. Secure Storage Controller
12. Sensor Hub
13. Power and Thermal Controller
14. Boot ROM and Root of Trust
15. Entropy Engine
16. IOMMU and Isolation Engine
17. Interrupt Controller
18. Attestation Engine
19. Watchdog and Reflex Controller
20. Immutable Audit Event Recorder
21. Recovery Controller

These are software concepts in v0. They are not RTL blocks or fabricated circuitry.

## Registers

The simulator exposes an in-memory register model for:

- SoC identity and revision
- boot state
- Guardian state
- active execution zone
- pending interrupts
- NEXUS transmit count
- simulated HRM receipt count
- last block reason
- real execution count

`REAL_EXECUTION_COUNT` is permanently zero in v0.

## Interrupt model

Seven simulated interrupt lines exist:

- WATCHDOG
- GUARDIAN_BLOCK
- NEXUS_MESSAGE
- HRM_RECEIPT
- SENSOR_EVENT
- RECOVERY_REQUEST
- THERMAL_ALERT

Interrupts are in-memory events only.

## NEXUS model

The SoC can model typed messages between canonical Digital Organism endpoints after trusted boot. Supported message classes include:

- SIGNAL
- CONTEXT
- RECOMMENDATION
- APPROVAL_RECEIPT
- ORGAN_INTENT
- HEALTH_EVENT
- AUDIT_EVENT

No message leaves the simulator through this module.

## Trusted boot

Boot fails closed unless every Hardware Trust gate has explicit `True` evidence:

1. secure boot
2. device identity
3. integrity
4. memory protection
5. network trust
6. sensor consent
7. recovery integrity

If any proof is absent or false, the simulated SoC enters `BLOCKED`, stays in the Recovery Zone, records a block reason and raises a `GUARDIAN_BLOCK` interrupt.

## 21-gate consequence path

The simulator inherits all three seven-gate families from OAP Silicon:

- 7 Hardware Trust gates
- 7 Intelligence gates
- 7 Human Authority gates

A registered consequential action is blocked unless all 21 pieces of evidence are explicitly true.

Even when all 21 pass, v0 returns only:

`AUTHORIZED_FOR_SIMULATION_ONLY`

It records an in-memory HRM-style receipt and performs no real execution.

## Execution zones

The canonical seven zones remain:

- Public Zone
- Private Zone
- SMI Zone
- HRM Zone
- Guardian Zone
- Device Zone
- Recovery Zone

## What v0 proves

v0 provides an executable contract for:

- fail-closed boot
- one-Brain architecture protection
- Human Authority protection
- 21-gate consequence checking
- register state
- interrupt signalling
- NEXUS message modelling
- Guardian blocking
- integrity receipts
- zero external execution

## What v0 does not claim

v0 does **not** mean that OAP has:

- fabricated a physical chip
- implemented RTL
- produced an FPGA bitstream
- loaded an FPGA
- built a motherboard
- provisioned a secure element
- created production device keys
- enabled independent AI or hardware authority

Those remain later milestones requiring separate evidence.

## Next technical ladder

1. **v0 — Python software simulator**
2. **v0.2 — richer memory map, device model and trace format**
3. **v1 — behavioural SoC simulator with explicit bus transactions**
4. **RTL slice — Guardian/NEXUS/HRM integrity blocks in SystemVerilog or equivalent**
5. **FPGA reference**
6. **OAP Compute Module**
7. **Optional physical OAP Sovereign SoC if scale and economics justify fabrication**

The governing doctrine remains:

> Own the intelligence architecture before owning the transistor.
