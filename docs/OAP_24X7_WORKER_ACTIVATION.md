# OAP 24/7 Organism Worker Activation

Status: deployment-ready specification only. This document does not provision infrastructure or incur cost.

## Purpose

Run the existing bounded Digital Organism worker continuously so the same production cycle can execute without a chat request:

OAP CORE observation/coherence/recovery/proposals → SMI bounded autonomy → whole-organism autonomy → runtime receipts.

Human Authority remains final. The worker has no independent authority to deploy, publish externally, capture payments, transfer money, dispatch drivers, change permissions, run production migrations, activate eSIMs/carriers, expose precise public tracking, approve recommendations or self-apply improvements.

## Existing production prerequisites

Before activation, all of the following must already be true:

- PostgreSQL base schema is initialized.
- Migration `0004_organism_runtime` is applied.
- `oap_runtime_jobs`, `oap_runtime_workers`, `oap_runtime_schedules`, `oap_runtime_dead_letters` and `oap_runtime_receipts` exist.
- The only runtime job types remain `RUNTIME_HEARTBEAT` and `RUNTIME_HEALTH_PROBE`.
- OAP CORE, SMI and whole-organism autonomy handlers all return `consequential_action=false`.

Production verification on 26 AUGUSTINE 2026 confirmed the runtime schema is present, while `active_workers=0` and no worker heartbeat has yet been recorded.

## Render background worker contract

Use a dedicated Render Background Worker rather than embedding a daemon inside Gunicorn.

- Name: `oap-organism-runtime`
- Repository: `RoyalPrince777/on-any-postcode`
- Branch: `main`
- Region: same operational region as the OAP services unless a later infrastructure review changes it
- Build command: `pip install -r requirements.txt`
- Start command: `python -m mission_control.organism_worker`
- Minimum instance count: 1
- Auto deploy: explicit choice; current OAP deployment discipline uses manual promotion after governed CI

The worker must receive the same production PostgreSQL connection used by the OAP organism through a secret/environment reference. Never hard-code or commit a database password or connection string.

Optional tuning variables already supported by the worker:

- `OAP_WORKER_ID`
- `OAP_WORKER_POLL_SECONDS`
- `OAP_WORKER_HEARTBEAT_SECONDS`
- `OAP_WORKER_SCHEDULER_SECONDS`
- `OAP_WORKER_RECOVERY_SECONDS`
- `OAP_WORKER_LEASE_SECONDS`

Default values are already bounded in code and are acceptable for first activation.

## Activation gate

Do not call the worker green merely because the service starts. Green requires all of these proofs:

1. Render service is LIVE on the intended governed commit.
2. `oap_runtime_workers` contains one ACTIVE worker on that revision.
3. Worker heartbeat remains fresh across multiple intervals.
4. Scheduler enqueues heartbeat and health-probe jobs.
5. Jobs are completed with runtime receipts.
6. OAP CORE, SMI and whole-organism cycle results all report `consequential_action=false`.
7. No unexpected dead-letter growth occurs.
8. No production error/5xx evidence appears because of worker activation.
9. Human Authority remains final and independent execution remains false.

## Stop / rollback

Stopping or scaling the worker to zero must not break the public OAP web service. Graceful SIGTERM moves the worker through DRAINING to STOPPED and finishes only the currently bounded job. Stale leases are recoverable by the next approved worker instance.

If runtime evidence becomes unhealthy, stop the worker first, preserve receipts/audit evidence, diagnose the bounded job failure, and only reactivate after the governed test/deploy gate is green.

## Cost boundary

A continuously running Render Background Worker is paid infrastructure. Creating or activating it requires explicit cost approval from Human Authority. Documentation, tests and readiness checks may proceed without that approval; provisioning may not.
