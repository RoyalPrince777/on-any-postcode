# OAP Cloud V1 — Founder-first, global-ready

This initial control-plane blueprint is **not registered** in the production Flask application and does not provision storage, compute or any cloud infrastructure.

- Endpoint after deliberate integration: `GET /cloud/v1/status`.
- Fail-closed token guard: set `OAP_CLOUD_FOUNDER_TOKEN` as a high-entropy secret on a private, HTTPS-only deployment. This standalone bootstrap token is not a replacement for the existing OAP Founder session/Guardian authentication.
- Do not expose this endpoint publicly or register it until integrated with OAP's existing Founder authorization, rate limits, audit trail and security tests.
- Never place secrets in Git.
- Storage, AOSP workers, artifacts and first boot remain unproven.

Next: inspect existing Founder authentication contracts, integrate without duplicate identity paths, add tests, then provision storage and an isolated temporary Linux AOSP worker.

## SMI Fox-lead execution contract

Founder Final retains final authority. SMI sets the intelligence mission. Captain ALL IN coordinates Morpheus, Akela, Gyata, Owl and other specialists under one mission record. Fox leads OAP Cloud execution, blocker recovery and best-fit specialist selection. Gyata provides sovereign-command judgement within Captain's mission coordination; Morpheus owns architecture, Owl evidence and analysis, and Akela protocol discipline. Akela enforces readiness and stops unverifiable completion claims. Gorilla owns last-line containment and safe shutdown. Guardian owns identity and privacy boundaries; Neo implements; Trinity validates; Shere Khan independently challenges the evidence. Queen Bee coordinates actual background workers, retries and queues **only after workers exist**; Spider maps dependencies and Octopus coordinates cross-service work.

### Release gates (evidence required)

1. Governed CI passes on the exact proposed commit; new commits invalidate older check results.
2. Managed OAP Founder session **and** private bootstrap token are required; ordinary and recovery-only identities are denied. Audit, request limits and CSRF/origin policy must be reviewed before endpoint registration.
3. Drive artifacts are size-bounded, integrity-verified, stored on a real non-symlink root, and cannot overwrite mismatched existing objects. Recovery and quota controls require independent verification.
4. Storage must be independently provisioned and its persistence verified before claiming OAP Drive available. Cloud compute, AOSP image and first boot require separate real runtime evidence.
5. Gorilla blocks public exposure if any security gate fails; Akela records the blocking evidence. No cosmetic percentages, demos as completion or repeat Founder approvals for bounded corrections.

This is an assignment of engineering responsibilities, **not** evidence of running independent AI agents, deployed worker infrastructure, or production readiness.

## Unified upgrade-only mission contract

Scope: OAP Cloud, OAP Drive, future OAP OS, Founder-private access and all security/test/dependency work described in this mission. This is a **planning and code-review contract**, not a deployed capability.

**Authority:** Founder Final > SMI mission governance > Captain ALL IN mission coordination > Fox execution lead > best-fit specialists. Gyata advises on sovereign command within Captain's coordinated mission; no specialist may bypass Founder Final or security gates.

**Standing specialist partnerships:** Fox + Spider + Octopus (execution routes, dependency recovery and cross-system orchestration); Queen Bee + Octopus (worker queues, retries and delivery orchestration when actually provisioned); Morpheus + Owl (architecture and evidence); Neo + Trinity (implementation and integration); Guardian + Gorilla (identity defence and emergency containment); Akela + Shere Khan (release discipline and adversarial review). Gyata advises Captain on competing priorities and escalation. Specialist selection is task-specific; do not pretend every role is an independently deployed agent.

**Upgrade-only operational rules:** Preserve existing working features, deny unauthorised access by default, require evidence on the exact proposed commit, avoid duplicate status reports and repeated approvals for bounded corrections, do not report simulated checks as live proof, do not claim percentages without measurable acceptance criteria, and never weaken security for speed.

**Execution backlog, in priority order:**

1. Validate governed CI and negative CSRF/identity regression tests on the latest commit.
2. Add per-identity/IP request limiting, privacy-safe audit events, strict payload limits and storage quotas; test fail-closed paths.
3. Independently verify canonical Founder identity, CSRF and session integration before registering the Cloud blueprint in the real application.
4. Provision and verify durable storage only with authorised infrastructure decisions; demonstrate persistence and recovery on real infrastructure.
5. Introduce Queen Bee worker orchestration only after real workers/queues exist; add retry, idempotency, failure containment and dependency health checks.
6. Build an actual AOSP image on suitable provisioned compute and prove emulator first boot and security/recovery separately. Never label Android debug APK CI as OAP OS first boot.

**Current evidence boundary:** A passed workflow applies only to its exact commit. PR merge, production deployment, persistent storage, cloud workers, AOSP image and first boot each need their own verification.

## Mission-to-100 evidence scoring (no cosmetic progress)

Display percentages, stars, council votes and a review **without altering the existing execution workflow**. A percentage is earned only by evidence-backed acceptance gates; unfinished, failed or unknown gates contribute zero. Each of the following ten gates contributes exactly **10 percentage points** to the overall mission, and each requires independent evidence:

1. Coordination contract committed and governed CI passed on its exact commit.
2. Android debug build completed with an archived successful workflow and identifiable artifact (debug build only).
3. Drive manifest and local storage integrity tests passed on the exact current commit.
4. Founder identity, bootstrap bearer and CSRF denial/acceptance tests passed on the exact current commit.
5. Body-size, request-limiting and privacy-safe audit tests passed on the exact current commit.
6. Security/adversarial review and recovery/containment tests passed.
7. Cloud blueprint integrated safely with real application session and authorization, with production-like tests passed.
8. Durable Drive provisioned with real persistence, quotas and recovery evidence.
9. Cloud compute and reliable workers provisioned, exercised and verified.
10. AOSP emulator image built, booted and security/recovery verified on real compute.

Score = 10 × number of fully evidenced gates; 100% means all ten gates passed. Partial work is reported as **in progress** beside the gate, never as invented fractional points. Do not transfer proof from an earlier commit to the current commit without rerunning affected checks. Stars: 1★ = 0–19%; 2★ = 20–39%; 3★ = 40–59%; 4★ = 60–79%; 5★ = 80–99%; 7★ = 100% and final independent review. Stars are **labels for evidence score**, not quality guarantees. Council votes are recommendations with named rationale, never invented votes from live autonomous agents.

**Permanent upgrade-only rules:** no unnecessary stages, repeated status loops, demo-as-completion, simulation in place of available real tests, duplicate reports, repeated approvals for already-authorised bounded work, cosmetic percentages, stopping after every minor fix, false Green, or security weakening. Continue meaningful batches of implementation + tests, inspect real CI logs, correct failures and report only materially changed evidence. Founder Final remains the sole final approval authority.

## SMI adversarial council: competing votes at mission end

At each substantive mission review, Captain ALL IN requests **independent role-based recommendations** from the smallest relevant specialists. Specialists may vote **FOR**, **AGAINST**, or **ABSTAIN**, challenge each other's proposals, offer alternatives, and record dissent. Fox proposes the execution route; Spider challenges dependencies; Octopus challenges orchestration complexity; Queen Bee assesses real worker readiness; Guardian and Gorilla assess security/containment; Morpheus and Owl assess architecture/evidence; Akela and Shere Khan independently challenge the proof. Agents may recommend an alternative leader, but no role automatically replaces Founder Final.

The **end-of-mission report** must show: proposed decision; each relevant agent's recommendation and concrete reason; FOR/AGAINST/ABSTAIN totals; strongest counterargument and response; evidence links (commit, CI, runtime); measured Mission-to-100 percentage and stars; DONE / NEXT / RECOVERY; outstanding blockers; Captain's synthesis; and Founder Final decision or **pending**. Never fabricate actual autonomous-agent votes: until agent runtime voting is implemented and audited, label votes **SMI simulated role assessments** or **proposed recommendations**, not independently cast ballots. A majority cannot override failed tests, security controls, external legal requirements, or Founder Final. Avoid polling all agents on routine fixes or repeatedly reopening approved decisions.
