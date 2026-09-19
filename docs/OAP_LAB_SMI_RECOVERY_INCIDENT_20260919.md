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

## SMI 21x War Room — incident review (21 checks, one locked 25% stage)

Evidence classes: PROVEN = direct connector/query/result; OPEN = requires further proof; FAIL = documented adverse event; NOT RUN = no claim of execution. Twenty-one checks are 21 scrutiny passes, **not** 21 sequential deployment gates, 21 independent model judges, or a claimed numeric success score. Three-pass quick mode and seven-pass deep dive are available subsets of this same evidence set. The canonical seven-judge registry and the separate full intelligence-lens catalogue remain intact.

| # | War Room check | Current finding / dissent | State |
|---|---|---|---|
| 01 | Truth-Light | Original default branch and endpoint restored; recovery completion is unproven. | PROVEN / OPEN |
| 02 | Evidence | Snapshot ID, original and derived branch IDs, endpoint ID, counts and hashes recorded; no full incident request log. | PROVEN / OPEN |
| 03 | Gap | Live SMI HRM database host/project identity not independently matched. | OPEN |
| 04 | SWOT | Snapshot preserves a checkpoint; implicit finalize moved production, a serious recovery-control weakness. | PROVEN / FAIL |
| 05 | Risk | Potential missed or split writes during 09:43–09:45 UTC; no-loss claim prohibited. | OPEN |
| 06 | Dependency | Render SMI, Neon HRM, Render Postgres fallback, receipt SQLite fallback must be distinguished. | OPEN |
| 07 | Architecture | OAP Lab is evidence/research; SMI brain, Matrix simulation, War Room and Founder authority remain separate. | PROVEN (design) |
| 08 | Alignment | Existing four equal 25% gates retained; no new stage, no duplicate memory/approval system. | PROVEN (design) |
| 09 | Security | No credentials in dossier; avoid exposing database URLs or payloads in a proof. | PROVEN (review boundary) |
| 10 | Privacy | Aggregate counts/digests only; raw HRM and user records not copied into PR. | PROVEN (review boundary) |
| 11 | Performance | Compute/endpoint swap may have briefly interrupted requests; lack of logs is not availability proof. | OPEN |
| 12 | Resilience | Original branch restored as default, original endpoint reattached; derived branch kept non-default. | PROVEN (control-plane) |
| 13 | UX | Never render snapshot-created or CI-passed as 25% recovered; show incident blocked. | PROVEN (contract), NOT RUN (UI) |
| 14 | Behaviour | Correct prior inaccurate “no branch replaced” claim and retain incident in receipts/audit. | PROVEN (documented correction) |
| 15 | Data | Original four-table counts: 13 HRM receipts, 31 memories, 4 conversations, 12 evidence receipts; current digests stable. | PROVEN (sampled), OPEN (missing writes) |
| 16 | Scenario | Re-run only a reviewed non-finalizing isolated simulation; no repeated implicit-finalize restore. | NOT RUN |
| 17 | Impact | Potential short connection interruption; affected user requests not established. | OPEN |
| 18 | Priority | Preserve original branch, original endpoint, snapshot and all available logs before unrelated features. | PROVEN (priority decision) |
| 19 | Opportunity | Receipt passive GET and explicit Founder CSRF POST proof landed in draft CI-tested code, not deployed. | PROVEN (branch), NOT RUN (live) |
| 20 | Readiness | CI passes draft code but does not prove production recoverability or live memory source. | OPEN |
| 21 | Decision & judgement | HOLD 25% 🔴; 50/75/100 not entered; Founder final after verified recovery. | FAIL-CLOSED |

### Seven-judge challenge / dissent register
The canonical seven judges are review lenses, not seven executed independent models. Apply Shere Khan (adversarial promotion/finalize path), Bagheera (evidence sufficiency), Agent Smith (endpoint-swap escape), Lion (human authority), Morpheus (alternate recovery scenarios), Akela (dependency/pack coordination), and Owl (continuity and audit history) to the same 21-check dossier. **Judges were assigned review questions in this document, not executed as a live model run.** Any later live judge result must carry a real timestamp, version, receipt, dissent and Founder decision.

### Exit conditions
Only reconsider the 25% gate after (a) matched secret-safe identity of authoritative live store(s), (b) incident-window write/receipt reconciliation or explicit documented irreducible uncertainty, (c) approved snapshot/backups for every authoritative store, (d) a truly isolated non-finalizing restore with verified readback AND no production endpoint movement, (e) any incident impact and rollback audits, and (f) reviewed CI + live production evidence + Founder final. No 21/21 score or percentage is inferred from the checklist.

## Read-only continuity follow-up — 2026-09-19

- Neon still lists the single manual snapshot `snap-nameless-tooth-arw9094g` and the derived branch; original `br-little-pine-arfbcpln` remains primary/default `production`. Snapshot existence is not a certified restore.
- Latest original-branch timestamps: `oap_hrm_receipts` 2026-09-18 19:26:38 UTC (13 rows); `smi_memory_records` 2026-09-19 08:34:08 UTC (31); `smi_conversations` 2026-09-19 01:30:18 UTC (4); `smi_evidence_receipts` 2026-09-19 08:34:08 UTC (12).
- None of those four tables contains an observed record dated within or after the 09:43–09:45 UTC endpoint-switch incident at this check. **This is an absence of evidence, not evidence of no attempted writes, no impact, or complete receipt continuity.** Reconciling attempts requires request/operation/receipt evidence from the live authoritative backend, where available.
- Strict live identity and alternate stores remain unverified. Never conclude that an old latest timestamp alone identifies a backend outage.
