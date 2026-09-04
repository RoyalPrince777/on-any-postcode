# OAP ISAC Spatial Intelligence v1

## Status

OAP owns the software contract and governance. A physical over-the-air testbed is **not** claimed until real radio evidence is connected and measured.

## OAP pipeline

```text
Authorised 5G/O-RAN radio measurements
        ↓
OAP Radio Adapter
        ↓
SRS / I-Q frame validation
        ↓
OAP Edge feature extraction
        ↓
CIR / channel-spatial features
        ↓
Local Positioning Intelligence
        ↓
Guardian RF minimisation
        ↓
Matrix RF event
        ↓
Matrix World State
        ↓
Founder-only ISAC Spatial Dashboard
```

## Supported software adapter contracts

- `oai_flexric_llc_e2sm` — intended for OpenAirInterface + FlexRIC + O-RAN Low Layer Control service-model integration.
- `oai_direct_srs` — direct authorised OAI SRS extraction adapter contract.
- `generic_authorised_srs_json` — bounded development/integration contract for authorised SRS/CSI-like I/Q frames.

These are replaceable upstream adapters. They never become OAP identity or authority.

## Implemented software

- bounded SRS I/Q ingestion
- deterministic local inverse-DFT/CIR feature extraction
- fixed 32-dimensional OAP spatial feature contract
- local calibration model and positioning estimate contract
- environment-change detection from feature deltas
- privacy-reduced Matrix RF events
- occupancy heatmap state
- calibrated multi-device collision-risk analysis
- Founder-only dashboard and read-only status endpoint
- explicit authorised development ingest/calibration endpoints
- physical-testbed and accuracy claims fail closed
- Guardian RF blocks raw I/Q from Matrix events

## Permanent Guardian RF boundaries

- raw RF remains local where practical
- no raw I/Q is included in Matrix events
- no biometric identity
- no covert personal tracking
- no through-wall personal surveillance
- no hidden-emotion inference
- no neighbouring-property sensing without an appropriate basis
- sensing must be authorised and user-controllable where applicable
- retention and purpose must be bounded

## Physical testbed path

A compatible lab can use an OAI 5G SA gNB with a supported radio frontend such as USRP or an O-RAN 7.2 RU, FlexRIC as Near-RT RIC, and an LLC E2SM/xApp path that exports authorised uplink SRS I/Q to the OAP adapter.

Before OAP marks the physical testbed green:

1. lawful/authorised spectrum and lab conditions are confirmed;
2. OAI or equivalent gNB is operating over the air;
3. FlexRIC/LLC E2SM or equivalent SRS source is connected;
4. authorised UE SRS measurements reach OAP Edge;
5. a real room/site calibration dataset is collected;
6. positioning error is measured on held-out locations;
7. object/environment-change detection is measured;
8. multi-device occupancy/collision signals are measured;
9. Guardian RF minimisation is audited;
10. signed evidence is recorded before any public accuracy claim.

## Accuracy rule

No centimetre, decimetre or sub-metre positioning claim is made from software readiness alone. Accuracy is environment-, radio-, antenna-, bandwidth-, calibration- and model-dependent and must be measured on the real OAP testbed.

## Upstream research references

BubbleRAN's 2026 ISAC demonstrations are treated as external research evidence only. Their documented pattern uses OpenAirInterface, FlexRIC/O-RAN LLC service-model access to SRS I/Q, channel/CIR processing and radio-based positioning/environment sensing. OAP implements an original first-party contract around those general standards/research patterns and does not copy BubbleRAN product identity or proprietary platform internals.

## Human Authority

ISAC Spatial Intelligence may observe, analyse and recommend. It does not autonomously reconfigure radio networks, transmit, change spectrum settings, identify people, or certify accuracy. Human Authority remains final.
