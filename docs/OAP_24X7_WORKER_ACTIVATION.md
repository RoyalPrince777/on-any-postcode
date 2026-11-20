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

## SMI-only autonomous mission continuation

The existing `RUNTIME_HEALTH_PROBE` is scheduled every **300 seconds** by the
Digital Organism database scheduler **when its worker is actually running**.
It now also reads the exact heads and required GitHub Actions workflows for
the already approved SMI VPN/privacy missions (PR #1413 and #1411), using
the optional least-privilege `OAP_SMI_GITHUB_READ_TOKEN`. No ChatGPT task,
separate cron service, second brain, new job type, schema or button press is
required. Without this token, monitoring remains unconfigured, never Green.

- Failed exact-head CI → automatically inspect the failed run and classify
  bounded error evidence; select repair diagnosis before feature growth.
- Pending, missing, skipped, stale or conflicting evidence → HOLD / reobserve
  on the next existing health cycle, with no success claim.
- All required checks passed on the exact PR head → automatically select
  **target-runtime and device proof** as the next safe step, not merge/release.
- The normal worker completion records the output in existing runtime receipts.
  SMI/Captain planning stays read-only. It does not modify GitHub code, approve
  changes, execute production recovery or attest the Redmi/VPN/World runtime.

This is the first **evidence-triggered continuation slice**, not verified
autonomous development of all OAP World modules. Founder-approved bounded work
can advance without repeated approvals only within the already permitted
execution pathways. GitHub Builder file writes require exact signed action
receipts in the existing Living Kernel; Green Gate and Founder Final remain
mandatory for consequential promotion. A running worker, configured secrets,
fresh receipts and actual target evidence are still required before claiming
live 24/7 autonomy.

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


## OAP-controlled Linux VPS (no new worker code)

The canonical worker can run under `systemd` on an OAP-controlled Linux VPS.
The reviewed service template is `ops/organism/oap-organism-worker.service`.
This is **not** the Render deployment contract and does not require Termux.
It runs only the existing `mission_control.organism_worker` process; it does
not create a new scheduler, agent, autonomy level, database, inference endpoint
or production deployment authority.

**Host prerequisites (must be confirmed by Founder):**
- An approved Linux VPS with a reviewed, immutable OAP checkout at
  `/opt/on-any-postcode`, Python virtualenv and installed requirements.
- An unprivileged `oap` service user, without interactive shell or sudo.
- A private `/etc/oap/organism-worker.env` readable by that user (e.g.
  root:oap, mode 0640) containing the already approved production PostgreSQL
  connection. Use secret references where supported; never put values in Git.
- Optional read-only GitHub token: `OAP_SMI_GITHUB_READ_TOKEN`. If absent,
  GitHub mission monitoring remains unconfigured/UNKNOWN.
- Founder approval of the exact deployment revision and its environment.

The service has `ProtectSystem=strict`, `NoNewPrivileges`, a limited
restart budget, graceful SIGTERM and **no** `git pull`, install, migrate,
permission change, publication, release or production-action command.

After a reviewed host setup and Founder Final approval, an authorised
operator may install and activate the template:

```bash
sudo install -m 0644 ops/organism/oap-organism-worker.service /etc/systemd/system/oap-organism-worker.service
sudo systemctl daemon-reload
sudo systemctl enable --now oap-organism-worker
sudo systemctl is-active oap-organism-worker
```

**Proof before Green:** On the intended production database confirm that the
worker revision matches the approved checkout; the heartbeat is fresh across
multiple intervals; scheduled jobs complete with new durable receipts; dead
letters and errors are not growing; and the Guardian/HRM/Human Authority
boundaries still report no consequential execution. A stale `ACTIVE` row or
old receipts alone never prove liveness. Do not mark the service Green after
`systemctl is-active` alone.

To contain a faulty worker on the approved VPS without changing the public
web-service runtime:

```bash
sudo systemctl stop oap-organism-worker
```

Preserve audit receipts, diagnose failure and re-verify before restart.
No connection to or deployment on an OAP-controlled VPS is established by
this repository addition.
