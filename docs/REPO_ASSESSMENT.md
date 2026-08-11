# Repository Assessment — KEEP / UPGRADE / MERGE / REMOVE-DUPLICATE

Repository: RoyalPrince777/on-any-postcode
Branch: smi-mission-control-slice (working branch)

Date: 2026-08-11
Author: copilot (automated assessment)

Purpose
- Produce a concise assessment of the existing repository prior to implementing the OAP Sovereign Mission Control vertical slice. This document identifies what to keep, what to upgrade, what to merge, and what duplicate or unrelated items to avoid changing.

Summary of inspection
- Flask application entry point: `app.py` (confirmed). This file contains the current UI and routes for the existing application (signal, team rooms, flags, profiles).
- Multiple SQLite files exist at repo root (`oap.db`, `oap_world.db`, `oap_public.db`, and others). There is an existing canonical `oap.db` present in the repository root — this should be treated as the canonical local DB file unless configuration overrides it.
- No `oap/security` module found in the repository; a prior "production-hardening" branch referenced such modules but they are not present here. Therefore reusing `oap/security/mfa.py` is conditional: if present in the target branch, we will wire it; otherwise we will harden whatever MFA helper exists.
- Requirements: `requirements.txt` contains `Flask==3.0.3` and `gunicorn`. No other framework dependencies are present.
- Static assets: `static/` directory present.
- No Alembic or migration framework is present in this repository root (no alembic.ini or alembic folder found).
- No tests present currently (no `tests/` directory yet).

Existing primary routes (from app.py):
- GET `/` (home) — renders main HTML template
- POST `/signal` — posts a signal
- POST `/room` — posts a team room message
- POST `/flag` — increments a flag count
- POST `/myworld` — creates a profile entry

Canonical database path
- The repository includes `oap.db` in the repo root. For local-first Termux usage, we will honor a canonical path resolved via configuration: environment variable `OAP_DATABASE_PATH` or default to `./oap.db` in repository root. We will NOT create a second `oap.db` in another path.

KEEP (do not remove)
- app.py: preserve as the Flask application entry point and existing routes; do not remove or replace.
- Existing SQLite files: preserve them. Use the main `oap.db` unless configuration indicates otherwise.
- Static assets and other scripts (backup, scan_routes): preserve and do not remove.
- World Cup/team data and routes: preserve functionality exactly; new features must not break or remove these.

UPGRADE (extend/reuse)
- Add `mission_control/` blueprint that integrates into app.py (do not replace app.py). Register blueprint within app startup.
- Add a safe, idempotent SQLite initialization helper (not auto-running on import). Provide a CLI entrypoint (`flask oap-init-db` or similar) and a programmatic API `ensure_schema()` that can be invoked during safe startup checks.
  - The helper MUST back up the current SQLite DB before applying schema upgrades (e.g., copy `<db>.bak.YYYYMMDDHHMMSS`).
  - The helper MUST run migrations inside a transaction, enable foreign keys, use WAL if supported, set busy timeout, and be idempotent.
- Reuse and harden existing MFA code if present (`oap/security/mfa.py`) and integrate encryption key via environment variable (no secrets committed).
- Implement audit chain and approval state machine in a new module; ensure that audit events are append-only and compatibly extend the existing storage.

MERGE (co-locate / merge similar tables)
- Inspect existing DB schema before adding tables. If `identities`, `permissions`, `audit_events` or similar tables already exist, extend them with new columns (where compatible) rather than creating parallel tables.
- If existing tables are missing needed fields (e.g., event sequence number), add columns via the migration helper in a backward-compatible way.

REMOVE-DUPLICATE (do not create duplicates)
- Do not create duplicate identity or permissions tables. Prefer to extend existing tables.
- Do not duplicate `/health` routes — inspect existing implementations and merge health checks.
- Do not add a second web application or switch to FastAPI. No FastAPI runtime is to be added.

Immediate risks and observations
- The repository currently lacks a formal migration system; adding schema changes must be done carefully and idempotently with backups.
- The claimed `oap/security` modules are not present. The user requested reusing `oap/security/mfa.py`; before doing so we will check the `smi-production-hardening` branch to ensure those files are present. If not, we will import the MFA code from that branch or implement a compatible hardened replacement.
- No CI or tests exist — tests and a CI workflow will be added as part of the slice.

Next steps (following commit order requested by policy)
1. Create `docs/REPO_ASSESSMENT.md` (this file) — done.
2. Implement canonical configuration and safe SQLite initialization helper (`mission_control/db.py`), callable via CLI and programmatic API.
3. Implement append-only audit chain module (`mission_control/audit.py`) and add DB schema only after verifying existing tables.
4. Implement approval state machine (`mission_control/state_machine.py`) and persistent tables (approvals, approval_transitions, approval_signatures) via the migration helper.
5. Integrate identity, permission, guardian checks and MFA (reusing existing module if present).
6. Implement mission_control blueprint, templates and static assets.
7. Add tests and CI.

Commit policy
- All changes will be small, reversible commits targeted to branch `smi-mission-control-slice`.
- No destructive operations or deletions of existing app behavior will be made.
- Each schema change will be accompanied by a backup of `oap.db` in the same directory with timestamped suffix.

If you approve this assessment, I will proceed with the canonical configuration and safe SQLite migration helper (step 2).