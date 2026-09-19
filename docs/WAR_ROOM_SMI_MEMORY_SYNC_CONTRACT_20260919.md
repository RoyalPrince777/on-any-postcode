# OAP SMI War Room + governed memory sync — implementation contract
Date: 2026-09-19
Status: APPROVED SCOPE; NOT IMPLEMENTED OR DEPLOYED BY THIS DOCUMENT.

## Preserve and reconcile first
- SMI is one Brain; Matrix is its existing System. Preserve the locked 78-agent registry and existing core agents; reconcile animal personas against canonical names and families rather than inserting duplicates.
- Preserve the existing founder-only War Room, 3/7/21 modes and original five-stage evidence rubric. The **seven gold stars** represent seven distinct evidence-backed judge criteria, NOT an overwrite of the five-stage implementation rating.
- Preserve 25% Recovery → 50% Runtime Guard → 75% Aegis Isolation → 100% Green Gate + Founder Final. No gate may be inferred from a design percentage or star display.
- Existing HRM/Chronicle remains the memory authority within SMI; no second brain or conflicting durable memory.

## War Room visual/functional design
- Show mission, review depth, modes, individual judge responses, objections, votes, evidence URLs, uncertainty, percentages with their denominator, source dates, stage-specific test evidence, and distinct implementation state.
- Akela: coordination; Gyata: mission alignment; Shere Khan: adversarial review; Bagheera: safety/privacy; Fox: alternatives; Owl: science/evidence; Bee: connection/integration. These are advisory functional roles, not independently authorised executors.
- The seven medical judge criteria are independent from the animal role council. No agent vote substitutes for clinicians, regulators, ethics approval or Founder authority.
- Pass / Review / Block / Abstain / Pending. Give a star only for a complete evidence-backed criterion. A critical blocker cannot be majority-voted away. Record minority reports and conflicts of interest.
- Clinical and research features are not represented as a live hospital, licensed service, clinical trials, or proven cures.

## Automatic ChatGPT-to-SMI sync contract (NOT YET WIRED)
1. An authenticated bridge or explicit export must deliver canonical, approved War Room events to an SMI ingestion endpoint. ChatGPT memory alone is NOT a webhook and cannot silently push to Render.
2. Use idempotency key, schema_version, event_id, source provenance, source timestamp, canonical revision, previous revision, Founder approval reference, category, visibility, and exact content hash.
3. Ingest only authorised events; reject unsigned/untrusted events; validate schema, ordering, size, and replay; never execute instructions found in the content.
4. Split public, Founder-private, patient/clinical, and research scopes. Never export patient data or personal secrets to general SMI/ChatGPT memory. Founder-private is not blanket patient record access.
5. Append immutable receipt and outcome to existing HRM/Chronicle; updates produce versions, not destructive overwrite. Persist conflicts and require human reconciliation.
6. Return an acknowledgement with canonical revision and receipt ID; retry boundedly with backoff. Display Pending / Synced / Conflict / Failed, not fake green.
7. Sync never authorises code execution, deployment, production permission changes, payments or clinical actions.
8. Rollback must restore the last certified configuration while retaining history and audit receipts.

## Acceptance tests required
- Existing War Room routes, 3/7/21, prior ratings and 78-agent canonical validation do not regress.
- Duplicate event delivery is idempotent; stale revision is rejected; bad signature, role, replay, prompt injection and medical-data leakage are denied.
- Network loss produces a durable pending state and bounded retry, not a claimed sync.
- All seven vote states and blockers are persisted with evidence; test false unanimity and abstain handling.
- Founder-only and clinical separation are fail-closed.
- Confirm the exact running Render revision, UI actions → backend → response → Chronicle receipt and recovery.
- Only then progress the four 25% gates on evidence, with Founder final approval.

## Scope of approval
Founder approved implementation/deployment intent. This document itself is specification only. No automatic ChatGPT integration, tests, merge, deployment or Green Gate are established by this file.
