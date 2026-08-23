# OAP PostgreSQL foundation

This upgrade preserves SQLite for local Termux operation and adds PostgreSQL as
the production persistence backend. It does not provision a database, apply a
migration, activate an agent or expose an execution route.

## Governed activation order

1. Human Authority selects and approves a Render PostgreSQL plan.
2. Create the managed database and link its internal `DATABASE_URL` to the web
   service. Never paste the URL into source control or logs.
3. Confirm a current managed backup when migrating an existing initialized
   database. Set `OAP_DATABASE_BACKUP_CONFIRMED=true` only for that migration
   command.
4. Inspect the pending plan:

   ```sh
   flask --app app oap-init-db --dry-run
   ```

5. Human Authority separately approves migration execution.
6. Run the explicit migration command once:

   ```sh
   flask --app app oap-init-db --yes
   ```

7. Remove `OAP_DATABASE_BACKUP_CONFIRMED` and verify:

   ```sh
   flask --app app oap-db-status --json
   flask --app app oap-verify-audit
   ```

Application startup and every GET route remain migration-free. When PostgreSQL
is unreachable or incomplete, public status remains redacted and fail-closed.

## Preserved governance

Intelligence proposes, Guardian protects, Builder creates, Identity validates,
Sovereign decides, HRM remembers, and the Organism grows. Human Authority is
the only final authority.
