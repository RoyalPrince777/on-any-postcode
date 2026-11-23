# SMI Matrix — Six-Priority Privacy Intelligence Review

Status: **Founder-approved bounded engineering review, draft PR only**.
No production release, Redmi A5 integration, permission expansion, verified
agent dispatch, hardware access, EMP action, radio interference or network
tracking is claimed.

## Architecture and existing components

This upgrade builds on rather than duplicates:
- `mission_control/agents.py`, `agent_passport_audit.py` and
  `matrix_signal_bus.py`: the seven registered Matrix core roles
  (Neo, Morpheus, Trinity, Oracle, Architect, Keymaker, Seraph); the extended
  candidates remain under separate passport review.
- `mission_control/matrix_privacy_workers.py`: existing coarse offline
  founder-supplied Android privacy review.
- `mission_control/autonomy_levels.py` and
  `mission_control/organism_runtime.py`: canonical runtime action policy.
  Only HEARTBEAT/HEALTH_PROBE classes currently occupy its A3 pilot allowlist.
- `mission_control/matrix_war_room.py`: review-only, no live worker votes,
  no forged proof, no self-approval.
- `docs/OAP_OPERATING_SYSTEM_V0.md`: protected auth, HRM and Founder data
  must never be added to offline PWA caches.

## Six scoped, non-executing priorities

| Priority | Responsible existing role | Scope | Proof gap |
|---|---|---|---|
| On-device Privacy Intelligence | Neo | Review coarse user-supplied tracker/permission/update facts | No Redmi device scan or actual permission reads |
| Identity Shield | Keymaker | Review only unrecognised-login, account-recovery-alert and MFA booleans | No authenticated session/security-log integration |
| Network Intelligence | Architect | Review only coarse connection-change/unrecognised-network counts | No network packets, endpoints, carrier telemetry or interception |
| Offline Recovery | Trinity | Review guide/readiness flags, never offline auth/approval caching | No tested device recovery or verified backup restore |
| Evidence Intelligence | Morpheus | Keep self-report and Unknown separate from authenticated proof | No trusted readback or durable HRM receipt |
| Governed Worker Automation | Seraph | Run read-only existing runtime policy preflight for MATRIX_PRIVACY_REVIEW | Job not authorised/queued; no live worker or device adapter |

Oracle's risk/forecast perspective and the complete existing Matrix seven-role
review remain available through `matrix_privacy_workers`. The six focus
labels do not create six new agent IDs or new system organs.

## Safety and test gates

- Accept only explicitly named booleans and non-negative counts <=1000.
- Reject raw IP addresses, URL histories, credentials, tokens, location traces,
  voiceprints, faces, serials, account identifiers and other non-allowlisted
  data. Do not log or persist individual input facts.
- False positives must be possible: an alert is a reason to *review*, not
  proof of stalking, surveillance, compromise or an identified attacker.
- Missing fields remain `unknown`; no flags never equal Green or "secure".
- Any real Android/OS permission prompt must be visibly consented to on-device.
  The OS and network providers remain disclosed external dependencies;
  "first party" never means total independence from device firmware or carrier.
- Block external actions, device/network probes, automatic blocking,
  network retaliation, EMP devices, jamming, identity changes, HRM writes,
  worker launches, deployment and self-approval in this code path.
- Protected data remain network-only; an offline guide provides instructions
  only, never authorization or stored account recovery secrets.
- Guardian, HRM, War Room, Green Gate, Founder Final are independent gates.

## Evidence acceptance matrix

| Gate | Evidence required | Status in this PR |
|---|---|---|
| Source implementation | Committed module and tests | Implemented in draft |
| Local tests | Exact-head pytest output | Not yet proved |
| CI | Relevant exact-head workflow completion and pass | Not yet proved |
| Existing core preserved | Code review/registry contract | Review required |
| Real device read | Consent-gated Redmi A5 tests | Not implemented |
| Identity/network integration | Authenticated source and minimisation proof | Not implemented |
| Worker dispatch | Canonical allowlist and approval/rollback/receipts | Not implemented |
| Release | Guardian + HRM + Green Gate + Founder Final | Not approved |

**Truth Mode:** only deterministic, founder-supplied, offline review logic
is proposed. No system should label the privacy checks "active live workers".
