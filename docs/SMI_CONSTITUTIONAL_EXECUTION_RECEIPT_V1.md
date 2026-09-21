# SMI Constitutional Execution Contract — bounded receipt slice

Status: DRAFT / NON-PRODUCTION / NO AUTHORITY EXPANSION
Owner: ON ANY POSTCODE
Human Authority: final
Implementation scope: existing SYNC_INTERNAL_RECORD only.

## Why this slice

The existing mission_control.governed_action_pipeline has a registered internal
action, a pre-existing signed Human Authority decision receipt, Guardian and
Judgement requirements, and a durable HRM receipt path. This change adds an
independent caller-side completion gate: a persistence result cannot become
pipeline_complete=True without matching receipt identity and checksum,
verified write/read-back, no transferred authority, and no secret exposure.

This is not a claim that every upstream proof is independently established by
this function. In particular action_performed, evidence_proven, and the 7-7-7
check values are supplied by the caller. Those require a trusted executor,
evidence source, and integrated execution tests.

## Exact boundary

- No new allowed actions, no payments or bookings, and no A6/A7 enablement.
- No new database schema, externally visible feature, or production deployment.
- No change to Human Authority, Guardian, Green Gate, HRM or emergency STOP.
- No green claim from a mock or static unit test.
- A missing/mismatched durability result raises ActionBlocked, never success.

## Current gap: exact-action approval binding

approval_service.record_decision signs a digest of RECORD_HUMAN_DECISION
for a recommendation. The current governed_action_pipeline.authorize_action
checks the receipt signature, decision, identity and expiry, but does not
itself establish that the signed digest authorises the exact
SYNC_INTERNAL_RECORD payload, amount/scope (when applicable), or single-use
consumption. This is a design gap to resolve before expanding execution.

Before permitting any consequential executable action, establish exact-action
approval/intent binding, single-use/replay behaviour, and a trusted executor
that cannot accept self-reported outcome evidence. Do not broaden the action
allowlist as a shortcut.

## Acceptance evidence

1. A matching durable receipt can yield a completed receipt result.
2. Missing fields, mismatched IDs/checksum, false read-back/write fields,
   transferred authority, and disclosed secrets block completion.
3. A missing evidence flag blocks before persistence.
4. Unregistered/external actions block before persistence.
5. Existing pipeline and sovereign-control regressions pass in CI.
6. Production certification also requires independently observed authorisation,
   actual execution, audit/Chronicle, restart/replay, recovery and outcome proof.

## Four-stage gate

- 25% — code review, bounded specification, tested recovery/rollback.
- 50% — runtime authority and STOP/replay/receipt enforcement.
- 75% — Aegis failure injection, isolation, restart and reconciliation.
- 100% — exact deployed version, independent outcome evidence, Founder Final.

A merged PR or passing unit suite does not automatically satisfy stages 50–100.
