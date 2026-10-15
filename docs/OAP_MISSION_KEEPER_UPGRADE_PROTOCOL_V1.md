# OAP Mission Keeper — Upgrade-Only Protocol v1

Status: proposed governance contract; not deployed automation.
Authority: Founder Final. SMI is the one intelligence brain. Captain ALL IN A.I. is mission keeper, not an independent authority.

## Canonical mission record
Each mission has: stable mission_id, system, scope, historical_baseline_percent (nullable), measured_completion_percent (nullable), completion_basis, evidence_refs, evidence_checked_at, accountable_lead, supporting_roles, state, blockers, next_action, rollback_route, guardian_decision, hrm_receipt, founder_decision.

Historical percentages MUST NOT be relabelled as verified completion. Unknown measured completion stays null. A passing unit test is not proof of a deployed operating system.

## State transitions
proposed -> scoped -> implemented -> tested -> merged -> deployed -> operational. A transition requires evidence specific to that state. blocked and recovery_required are explicit states, not cosmetic percentage deductions. A blocked mission retains its last independently verified state as a separate field; recovery returns only to that state after a documented repair, rerun of the failing gate, and accountable review. A later transition still requires its own evidence. Never skip evidence gates or infer a transition from a PR description.

## Gate decisions and authority\nGuardian decisions are scoped security findings (allow, deny, or review), not proof of runtime operation. HRM receipts identify immutable evidence references, exact commit/build target, timestamp, and reviewer; a receipt alone is not an approval. Founder decisions record the approved scope and reserved actions. A transition to tested requires test evidence; merged requires a merge SHA; deployed requires deployment evidence; operational requires observed runtime proof. Before security-sensitive deployment, Guardian must allow the exact scope and HRM must record the evidence. Public release, device flashing, provider execution, and other Founder-reserved actions require separate explicit Founder authorisation. A missing, stale, or denied required gate blocks advancement. Advisory agents cannot override these decisions.\n\n## Mission-to-100 evidence gates
1. Inspect and reuse existing code, passports, and architecture before adding modules.
2. Name one accountable lead and only necessary supporting roles; no duplicate authority.
3. Verify agent passports before activation. Advisory role selection never implies spawned workers.
4. Preserve SMI single-brain, Guardian enforcement, HRM evidence, and Founder Final.
5. Security remains fail-closed; never relax a live gate to make CI green.
6. Require real tests when available; never represent a simulation or a mock as live proof.
7. Record exact commit, CI run, device/build target, and test result.
8. Keep provider credentials, OS flashing, payments, and public activation disabled until separately authorised and verified.
9. On failure, preserve logs, identify root cause, repair bounded scope, and rerun the exact failing gate.
10. No repeated approval for already-approved bounded work; no automatic merge or release without applicable Founder authority.
11. Upgrade-only: preserve functioning paths, compatibility, rollback and data.
12. Report Done / Next / Recovery in one concise board, with unresolved items explicitly marked.

## Current historical technology baselines (not measured verification)
- SMI / OAP Core: 96%
- OAP Browser Shell: 89%
- OAP Android APK: 92%
- OAP Engine HTML: 78%
- OAP Engine DOM: 65%
- OAP Engine CSS: 48%
- Signed OS Image: 5%
- Verified Boot / OTA / Recovery: 8%
- Complete OAP OS Boot: 0%
- Technology Sovereignty: 17%

## OAP Android acceptance
Target an AOSP-supported virtual device first. Record exact AOSP revision, build host, target, reproducible build invocation, boot evidence, Guardian boundary tests, SMI isolation, update signing, rollback and recovery. Do not flash the Founder's current Android device without device-specific recovery proof and separate authorisation. OAP Digital Silicon is software research, not manufactured hardware. The bounded instruction interpreter in `mission_control/digital_silicon_instruction_core.py` supports only LI, ADD, ADDI, XOR and HALT; it is not RISC-V, a CPU, a boot chain, or an operating system. Its isolated tests do not establish device boot or runtime sovereignty.

## Alliance role mapping (advisory, not worker activation)
Architect: OS architecture; Neo: engineering review; Spider: dependencies; Octopus: integration orchestration; Fox: local-first build portability; Bagheera + Seraph: boundary/security review; Tigress: precise implementation; Shere Khan: adversarial checks; Elephant: evidence/recovery; Owl: independent assessment; Queen Bee: distributed coordination only when independent worker streams exist; Captain: mission register and consolidated report; Guardian: security gate (system, not agent); HRM: evidence system; Founder: final authority.

## Matrix Alliance: protection, recovery and twin verification (advisory only)
Tank and Dozer are brothers with distinct responsibilities: Tank protects functioning paths and operational continuity; Dozer plans bounded repair and recovery. Neither can override Guardian security decisions or initiate unapproved production changes.
The Twins form a paired evidence-review protocol, not duplicate authorities or presumed active workers. Twin One records the expected state and its acceptance criteria; Twin Two independently checks observed state and discrepancies. Independence requires distinct evidence review, not merely repeating one result. Disagreements remain unresolved blockers until reviewed by the accountable lead and recorded by HRM; Guardian governs security-sensitive outcomes and Founder retains reserved decisions.
These names describe proposed specialist assignments only. Verify existing agent passports and registrations before any runtime activation; no worker creation, monitoring, merge, or deployment follows from this document.

## Passport discrepancies to reconcile before activation
Tigress vs Tygress; historical Mouse removal vs later Founder restoration; Agent Smith candidate vs registered role. Never silently invent registration or activate candidates.

## Existing open Digital Silicon gate
Draft PR #1242, commit 65e2cabd9b06c7eb17d208fdde995e8b3ec73dfe: runtime image succeeded; 5,447 regression tests passed; overall governed checks failed because bounded external live routing Green Gate warmup did not become ready. This is a historical commit-specific CI snapshot, not a standing acceptance receipt. Recheck the exact candidate commit and applicable live gates before advancement; do not mark full Green.

## Acceptance for this protocol
Documentation review and explicit Founder approval are required before implementation. This file alone does not constitute an agent upgrade, automatic tracking, runtime enforcement, or operating-system deployment.
