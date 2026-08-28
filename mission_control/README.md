# OAP Mission Control

This package contains the local-first Mission Control vertical slice for the
existing Flask application.

Runtime support requires Python 3.11 or newer.
The repository-wide duplicate and legacy-name review is recorded in
`docs/ARCHITECTURE_CONFLICT_AUDIT.md`.

Current read-only surface:

- `status.py`: separate public and authorized status projections. Public data
  is coarse and redacted; authorized data fails closed until Identity and
  Permission checks exist.
- `agents.py`: one canonical registry for seven Intelligence worlds containing
  seven OAP-owned families, confirmed Soul–Mind–Body passports and separately scoped
  external providers. Unapproved roles and brain assignments remain empty.
- `infrastructure.py`: the locked Maps, Weather, eSIM and Connectivity scope,
  with duplicate/overlap validation and honest provider-readiness states.
  Navigation remains a related hub, Mobility remains a separate OAP layer and
  system health remains a shared Mission Control projection.
- `linkup.py`: the canonical read-only model for The Link. Directory and Inbox
  remain Communications views, while Community Power is linked without an
  ownership transfer. Public output contains no identities or conversations.
- `languages.py`: the validated, read-only OAP World language hub. It provides
  seven continent paths, starter lessons, deterministic conjugation drills and
  reviewed official South London links without learner tracking or provider calls.
- `brain.py`: coarse SMI implementation and activation readiness. It reports
  code versus runtime connection honestly and never constructs or runs SMI.
- `organism.py`: canonical Digital Organism registry and duplicate-boundary
  validation. It locks SMI as the single brain, Living Kernel as the heart,
  the seven Intelligence worlds, seven existing families, agent Soul–Mind–Body, and Human Authority as
  the only final authority.
- `war_room.py`: Founder-only, read-only evidence aggregation for command,
  Intelligence worlds, all Digital Organs, infrastructure/runtime and silicon.
  Five-star ratings advance only through approved scope, implementation,
  verification, runtime proof and operational certification; no later stage may
  skip an earlier missing gate.
- `views.py`: GET-only `/mission`, `/mission/agents`,
  `/mission/brain`, `/mission/brain/status`, `/mission/war-room`,
  `/mission/war-room/status`, `/mission/infrastructure`,
  `/mission/linkup`, `/mission/organism`, and `/mission/status` routes. No
  Mission Control POST or execution routes are registered; `/mission/chat` and
  `/mission/brain/run` are intentionally absent.
- `templates/` and `static/`: server-rendered, auto-escaped workspace and
  gateway assets with no remote dependencies.
- `db.py`: status inspection opens SQLite in read-only/query-only mode. Schema
  changes remain explicit CLI actions and never run from GET requests.
- `audit.py`: audit verification is read-only. The append path is not exposed
  by this slice.

Implemented internal runtime under `oap/`:

- One SMI coordinator with fourteen biological regions, NEXUS input routing,
  canonical Registry selection, explicit provider assignments, Aegis,
  Guardian and War Room consequence review.
- Identity and Permission adapters that fail closed, HRM contextual memory,
  a hash-chained audit log and versioned World state.
- Recommendation-only action planning, action-bound and single-use signed
  Human Authority receipts, a Living Kernel gate, an empty-by-default Builder
  registry, and proposal-only Evolution. World writes can run only as a
  registered Builder handler through Living Kernel.

Explicit CLI commands:

- `flask --app app oap-db-status`
- `flask --app app oap-init-db --dry-run --yes`
- `flask --app app oap-verify-audit`

Migrations 0001 and 0002 now share the canonical audit, approval-ledger and SMI
runtime schemas, and migration loading no longer executes source text directly.
They still must be reviewed against the repository's legacy databases and
applied only through the explicit CLI after a Human Authority-approved backup.
Public mutation routes remain disabled until authenticated Identity records,
web-session protection, provider assignments and Builder handlers are approved
and wired.
