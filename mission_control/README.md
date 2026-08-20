# OAP Mission Control

This package contains the local-first Mission Control vertical slice for the
existing Flask application.

Current read-only surface:

- `status.py`: separate public and authorized status projections. Public data
  is coarse and redacted; authorized data fails closed until Identity and
  Permission checks exist.
- `views.py`: GET-only `/mission` and `/mission/status` routes. No Mission
  Control POST or execution routes are registered.
- `templates/` and `static/`: server-rendered, auto-escaped workspace and
  gateway assets with no remote dependencies.
- `db.py`: status inspection opens SQLite in read-only/query-only mode. Schema
  changes remain explicit CLI actions and never run from GET requests.
- `audit.py`: audit verification is read-only. The append path is not exposed
  by this slice.

Explicit CLI commands:

- `flask --app app oap-db-status`
- `flask --app app oap-init-db --dry-run --yes`
- `flask --app app oap-verify-audit`

The migration and audit-write path is not implementation-ready yet. Migration
0001 and the append helper require schema reconciliation with the repository's
legacy `audit_logs` table before `oap-init-db` is used. Identity, Permission,
Guardian, Purpose, Constitution, JWT, MFA, CSRF, rate limiting, object-level
authorization, and the approval state machine must be complete and verified
before any mutation route can be registered.
