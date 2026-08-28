# OAP RTL Memory Guard / IOMMU Proof Slice v0

## Purpose

This slice moves the OAP Sovereign Digital SoC another step from software simulation toward hardware-description proof. It implements address-to-zone classification, protected-region policy and IOMMU-style DMA-domain checks in SystemVerilog.

It does not implement physical memory, a DMA transfer engine, an FPGA bitstream or a fabricated chip.

## Canonical execution zones

The slice preserves the seven OAP execution zones:

1. Public Zone
2. Private Zone
3. SMI Zone
4. HRM Zone
5. Guardian Zone
6. Device Zone
7. Recovery Zone

The numeric RTL encoding is an implementation detail; the architectural names and boundaries remain canonical.

## Address map represented by this proof

| Address range | Zone | Policy |
| --- | --- | --- |
| `0x00000000..0x0000ffff` | Recovery | Read-class only; writes fail closed |
| `0x10000000..0x10000fff` | Guardian | Same-zone protected |
| `0x10001000..0x10002fff` | Device | Shared device/MMIO class |
| `0x10003000..0x10003fff` | Guardian | Same-zone protected |
| `0x20000000..0x200fffff` | HRM | Same-zone protected |
| `0x21000000..0x210fffff` | SMI | Same-zone protected |
| `0x22000000..0x220fffff` | Private | Same-zone protected |
| `0x23000000..0x230fffff` | Public | Shared public class |
| `0x24000000..0x240fffff` | Device | Shared device buffer class |

Addresses outside the map fail closed.

## Protected access rule

Private, SMI, HRM, Guardian and Recovery regions are protected. A requester must originate from the same zone to access those regions, with an additional immutable rule that Recovery/boot-ROM writes are always blocked.

Public and Device regions are shareable classes in this proof slice.

## IOMMU-style DMA proof

The DMA interface receives a seven-bit trusted domain mask and source/target addresses. The slice:

- decodes source and target zones;
- requires both zones to be present in the domain mask;
- blocks any transfer classification involving Recovery;
- fails closed for unmapped addresses;
- raises the Guardian violation interrupt on a block.

An `dma_allow` result means only **policy classification succeeded**. There is deliberately no data-transfer path in this module, so no bytes move anywhere.

## Read-only status

The MMIO status surface exposes:

- Guardian enforcing = `1`;
- Human Authority final = `1`;
- real DMA enabled = `0`;
- external execution enabled = `0`;
- Guardian interrupt state;
- violation count;
- most recent access/DMA classification.

Attempts to write protected read-only status registers are themselves counted as Guardian violations.

## Testbench proof

The self-checking testbench verifies:

1. Guardian enforcement and Human Authority status are immutable.
2. Real DMA and external execution remain disabled.
3. Public memory can be classified as shared.
4. Cross-zone Private access is blocked.
5. Same-zone Private access is allowed.
6. Recovery writes fail closed.
7. A Public + Device DMA domain can classify a Public-to-Device request as allowed without transferring data.
8. That same domain cannot expand into HRM.
9. Unknown addresses fail closed.
10. Protected MMIO writes fail closed and cannot enable DMA/execution.
11. Guardian violations are counted and interrupt state is observable/acknowledgeable.

A passing RTL simulation prints:

`OAP_RTL_MEMORY_GUARD_V0_PASS`

## Truth boundary

This slice does **not** mean:

- real memory isolation hardware has been fabricated;
- a physical IOMMU exists;
- DMA occurs;
- an FPGA image has been generated or loaded;
- a secure element has been provisioned;
- SMI has become hardware or another Brain;
- hardware can approve consequential actions;
- Human Authority can be bypassed.

The module is a governed RTL proof of isolation logic only.

## Authority doctrine

**Human Authority -> OAP software -> Guardian policy -> hardware execution**

Hardware proves, isolates and enforces. It does not rule.
