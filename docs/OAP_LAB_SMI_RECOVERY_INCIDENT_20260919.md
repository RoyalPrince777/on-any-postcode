# OAP LAB — SMI 25% recovery incident evidence dossier
Date: 2026-09-19
Status: INCIDENT OPEN / STEP 1 BLOCKED. No Green Gate claim.

## Ownership and boundaries
OAP Lab is the research, discovery and engineering home; Human Lab is one division. SMI supplies analysis; Matrix Simulation tests isolated scenarios; War Room reviews conflicting evidence; Guardian enforces isolation; Human Founder authorises real-world changes. This dossier does not create another database, controller, memory store, agent, approval authority, public status card or deployment path.

## Current verified recovery state
- Neon project: oap-hrm-fallback, ID blue-heart-80559481. Its identity as the authoritative *live SMI* memory store has NOT been established.
- Original branch: br-little-pine-arfbcpln, name production, restored as primary/default/ready.
- Original endpoint: ep-square-poetry-ar044jl7, restored to original branch, reported active.
- Snapshot: snap-nameless-tooth-arw9094g, manually created 2026-09-19 09:43:41 UTC.
- Snapshot-derived branch: br-nameless-forest-arjp9w0y, name oap-hrm-snapshot-restore-isolated-20260919, non-default/non-primary; it currently lacks an accessible compute for read-only SQL queries.
- Danger: restore_snapshot with implicit finalize promoted snapshot as production and moved original endpoint; original branch/name/default and endpoint were returned after discovering the unintended change. The original endpoint's restoration required deletion of only the newly-created temporary endpoint. A brief compute restart or missed/split writes cannot be excluded.
- Retest of original branch: oap_hrm_receipts 13; smi_memory_records 31; smi_conversations 4; smi_evidence_receipts 12. Subsequent content fingerprints matched the first post-incident fingerprints; this DOES NOT prove that absent or interrupted writes never occurred.
- Neon branch telemetry unavailable in this region; SMI Render logs returned no entries for the incident window. Neither result proves absence of failed requests.
- Independent Render Postgres fallback may be a separate store; never assume its backup is covered by this Neon snapshot.

## Lab experiment controls
1. **Observe** read-only source provenance and current service metadata. Never print database URL, keys, record payloads or sensitive personal data.
2. **Correlate** existing request IDs, receipt IDs and timestamps (if first-party evidence becomes available) across application, receipt store and audit log; distinguish observed records from potentially absent writes.
3. **Compare** original and snapshot-derived tables only using an independently vetted non-production read-only compute; do not repoint the original endpoint, promote the restored branch, or imply that aggregate counts rule out split writes.
4. **Simulate** rollback and failure injection only in Matrix Simulation/OAP Lab; label simulation outcomes separately from any live restore evidence.
5. **Prove** an isolated restore without production endpoint reassignment under a reviewed explicit non-finalizing procedure; require pre/post branch and endpoint assertions, row-level-safe digests, and a stop/rollback plan. Do NOT repeat the failed default-finalize restore.
6. **Review** with War Room and Guardian: include failure modes, dissent, incident chronology, unresolved unknowns and exact evidence references; Founder approves consequential actions.

## Locked four-stage gate
- 25% Rollback / Recovery: RED BLOCKED pending continuity reconciliation, authoritative store proof and a safely proven isolated restore; never convert snapshot existence to recovery certification.
- 50% Runtime Guard: NOT ENTERED.
- 75% Aegis Isolation / Recovery: NOT ENTERED.
- 100% Green Gate + Founder Final: NOT ENTERED.

## OAP Lab result
This is a real research dossier and explicit experimental protocol, not a claim that the Lab dashboard, restore automation, ChatGPT-to-SMI sync, live memory proof, or 25% gate is deployed or green. The governed receipt-status correction is committed and CI-passed in this draft PR, but remains unmerged and undeployed.
