# OAP Silicon Architecture — Master v1

OAP Silicon is the hardware sovereignty layer beneath the OAP Digital Organism.
It defines the hardware contract now without pretending that OAP fabricates a custom
chip today.

## Mission

**Own the intelligence architecture before owning the transistor.**

## Locked design principle

1. **Human Authority above software.**
2. **Software above hardware execution.**
3. **Hardware proves, isolates and enforces — it does not rule.**

These are constitutional boundaries. Future OAP devices, reference boards, FPGA
prototypes and custom silicon must preserve them.

## Canonical stack

OAP Silicon → OAP Home Node → OAP CORE → NEXUS → Thalamus → SMI Brain →
Judgement → Human Authority → Living Kernel → Digital Organs → HRM

OAP Silicon provides trusted compute beneath the organism. It does not become another
brain and it does not become a sovereign decision maker.

## Seven silicon layers

1. **OAP Root** — secure boot, device identity, signed firmware, key storage,
   tamper evidence and rollback protection.
2. **OAP Compute Fabric** — CPU, GPU, NPU, DSP and optional FPGA resources.
3. **OAP Memory Fabric** — protected memory, encrypted storage, HRM integrity and
   isolation between workloads.
4. **OAP NEXUS Fabric** — typed, capability-scoped internal hardware messaging.
5. **OAP Sense Fabric** — consented and auditable camera, microphone, location,
   motion, environment, network and power telemetry.
6. **OAP Network Fabric** — encrypted Wi-Fi, Ethernet, Bluetooth, peer-to-peer and
   future cellular/mesh capability.
7. **OAP Guardian Fabric** — secret isolation, workload verification, domain
   separation, consequence locks and security receipts.

## Seven execution zones

- Public Zone
- Private Zone
- SMI Zone
- HRM Zone
- Guardian Zone
- Device Zone
- Recovery Zone

SMI must never receive unrestricted raw access to all zones. Access is scoped by
capability and policy.

## 7 × 3 = 21 silicon gates

### Hardware Trust — 7

Secure boot, device identity, integrity, memory protection, network trust, sensor
consent and recovery integrity.

### Intelligence — 7

Input validity, model provenance, context integrity, confidence, policy,
consequence classification and explainability.

### Human Authority — 7

Identity, permission, intent, scope, approval, receipt and audit.

A consequential action may not cross the hardware boundary merely because an AI
component recommends it.

## Authority chain

Human Authority → OAP Software → Guardian Policy → Hardware Execution

Hardware execution is deliberately last. It may prove state, isolate workloads,
reject unauthorised operations and produce receipts. It may not promote itself into
an independent authority.

## Consequential hardware autonomy remains blocked

The hardware layer does not independently approve recommendations, deploy software,
publish externally, capture payments, transfer money, pay royalties, dispatch people,
change permissions or roles, run production migrations, hand parcels to external
carriers, activate physical Post Offices, activate eSIMs, switch carriers, expose
precise public tracking, self-promote, or self-apply improvements.

## Reference platform generations

### Generation 0 — active reference

**Android/Termux Home Node on existing silicon.**

This is the present production reference. OAP owns the software/runtime contract while
using commodity ARM hardware.

### Generation 1 — planned

Dedicated ARM or RISC-V mini computer running the OAP Home Node stack.

### Generation 2 — future

OAP Home Node appliance with a secure element and local AI accelerator.

### Generation 3 — future

FPGA reference platform for programmable OAP trust and acceleration logic.

### Generation 4 — future

OAP compute module/reference board specification.

### Generation 5 — optional future

OAP Sovereign SoC, potentially RISC-V/ASIC, only if scale and workloads justify
custom fabrication.

## Future OAP Sovereign SoC blocks

A future SoC may contain a CPU cluster, NPU, GPU, Secure Enclave, HRM Integrity
Engine, Guardian Policy Engine, NEXUS interconnect, media DSP, network accelerator,
encrypted memory controller, secure storage controller, sensor hub and power/thermal
controller.

This is a design target, not a claim that physical OAP silicon currently exists.

## ISA strategy

OAP should not invent a new instruction set first. The progression is:

Existing ARM hardware → RISC-V experimentation → FPGA validation → optional custom
RISC-V/ASIC.

Future OAP-specific hardware operations may accelerate trust, attestation, sealing,
HRM integrity, capability checks, authority gating and secure zeroisation, but only
after the software architecture has proven the need.

## Sovereignty ladder

Own the software → own the runtime → own the data → own the network logic → own the
hardware design → own the silicon IP → optionally manufacture through a foundry.

OAP does not need to own a semiconductor fabrication plant to own its architecture or
silicon IP.

## Constitutional invariant

**Human Authority remains final. Hardware is evidence and enforcement, not rule.**
