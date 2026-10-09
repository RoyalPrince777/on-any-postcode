# OAP Cloud V1 — Founder-first, global-ready

This initial control-plane blueprint is **not registered** in the production Flask application and does not provision storage, compute or any cloud infrastructure.

- Endpoint after deliberate integration: `GET /cloud/v1/status`.
- Fail-closed token guard: set `OAP_CLOUD_FOUNDER_TOKEN` as a high-entropy secret on a private, HTTPS-only deployment. This standalone bootstrap token is not a replacement for the existing OAP Founder session/Guardian authentication.
- Do not expose this endpoint publicly or register it until integrated with OAP's existing Founder authorization, rate limits, audit trail and security tests.
- Never place secrets in Git.
- Storage, AOSP workers, artifacts and first boot remain unproven.

Next: inspect existing Founder authentication contracts, integrate without duplicate identity paths, add tests, then provision storage and an isolated temporary Linux AOSP worker.

## SMI Fox-lead execution contract

Founder Final retains approval authority; Gyata sets sovereign priorities. Fox leads blocker recovery and selects the smallest best-fit specialist group; Captain ALL IN maintains one mission record. Akela enforces readiness and stops unverifiable completion claims. Gorilla owns last-line containment and safe shutdown. Guardian owns identity and privacy boundaries; Neo implements; Trinity validates; Shere Khan independently challenges the evidence. Queen Bee coordinates actual background workers, retries and queues **only after workers exist**; Spider maps dependencies and Octopus coordinates cross-service work.

### Release gates (evidence required)

1. Governed CI passes on the exact proposed commit; new commits invalidate older check results.
2. Managed OAP Founder session **and** private bootstrap token are required; ordinary and recovery-only identities are denied. Audit, request limits and CSRF/origin policy must be reviewed before endpoint registration.
3. Drive artifacts are size-bounded, integrity-verified, stored on a real non-symlink root, and cannot overwrite mismatched existing objects. Recovery and quota controls require independent verification.
4. Storage must be independently provisioned and its persistence verified before claiming OAP Drive available. Cloud compute, AOSP image and first boot require separate real runtime evidence.
5. Gorilla blocks public exposure if any security gate fails; Akela records the blocking evidence. No cosmetic percentages, demos as completion or repeat Founder approvals for bounded corrections.

This is an assignment of engineering responsibilities, **not** evidence of running independent AI agents, deployed worker infrastructure, or production readiness.
