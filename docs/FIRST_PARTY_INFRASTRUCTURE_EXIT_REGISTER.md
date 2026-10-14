# OAP first-party infrastructure: evidence-based exit register

Status: engineering audit; NOT a migration approval or a production-readiness certificate.

## Confirmed from repository configuration (2026-10-14)

| Dependency | Evidence | Exit acceptance |
| --- | --- | --- |
| GitHub | `.github/DEPLOYMENT.md` requires GitHub CI and GHCR immutable image digests | Independently held complete Git history, tested offline clone, reproducible build, independent image registry and release signing; retain existing CI until proved |
| Neon PostgreSQL | `docs/DATABASE_PRIMARY_RECOVERY.md` already prioritises provider-neutral `OAP_PRIMARY_DATABASE_URL_B64`, `OAP_PRIMARY_DATABASE_URL`, and `DATABASE_URL` ahead of Neon aliases | Encrypted database backup, isolated restore, migration/schema compatibility, integrity and restore-time evidence |
| **Neon Managed Auth** | `.github/DEPLOYMENT.md` specifies `NEON_AUTH_BASE_URL`, Founder UUID binding, and private route controls | Independent auth implementation with safe account migration, session revocation, Founder exact-authority checks, negative access tests and rollback; database portability alone is NOT Neon independence |
| Render | `.github/DEPLOYMENT.md` specifies Render runtime-image service, service ID and health checks | Independently operated compute, private route isolation, worker supervision, secrets, immutable deployment and rollback, end-to-end health |
| GHCR | `.github/DEPLOYMENT.md` pins images to GHCR digests | Independent OCI registry and exact digest provenance; tested pull without GHCR |
| OpenAI | `.github/DEPLOYMENT.md` specifies `OAP_AI_PROVIDER=openai` and `OPENAI_API_KEY` | Governed inference path that does not require external provider; no claim that a third-party local model is first-party trained |
| Termux | `backup.sh` hardcodes a Termux Bash interpreter and `~/oap` | Cross-platform backup/developer workflows and tested recovery on independently operated host |

## Immediate discovered weakness: backup.sh

The existing `backup.sh` copies `app.py` and `oap.db` into `~/oap/backups` and prints `Backup Complete`. This is NOT a full Git repository backup, production PostgreSQL backup, Neon Auth export, encrypted off-device backup, or recovery test. The script lacks explicit fail-fast handling and may print success after a failed copy. Do not rely on it for sovereignty or disaster recovery. Strengthen it separately with tests, preserving its existing local-use contract until migration is proven.

## Safe implementation order (not status gates)

1. **Source custody:** mirror Git history to independently controlled storage; verify fresh clone and build; include tags, refs and required LFS objects where applicable. Do not assume a GitHub-generated ZIP is sufficient.
2. **Database recovery:** identify actual production source and retention obligations; obtain authorised encrypted export; restore to isolated PostgreSQL; verify row counts, schema, migrations, roles and application read paths. Never export live user data to repository or CI logs.
3. **Identity continuity:** inventory Managed Neon Auth dependencies and establish a secure, independently operated replacement; test Founder authority and anonymous/private boundaries before switching.
4. **Compute and registry:** prove application, workers and exact immutable image work without Render/GHCR; keep existing production unchanged.
5. **Network and local inference:** prove independent secure ingress, observability and governed inference without provider fallback that silently weakens authority.

## Acceptance rules

- No Green based on docs, mocks, configuration presence, or simulated restore.
- No secret disclosure, automatic migration, provider shutdown, production cutover, or bypass of Founder authorisation.
- A dependency is **independently recoverable** only when an actual isolated recovery test passes and evidence is recorded with date, commit, operator, checks and rollback path.
- Track provider **operation**, software **origin**, and physical **supply chain** separately. Open-source components operated by OAP can meet operational independence without being originally developed by OAP.

## Current verification

Repository files inspected: `backup.sh`, `docs/DATABASE_PRIMARY_RECOVERY.md`, `.github/DEPLOYMENT.md`. No independent clone, database restore, identity migration, build, or runtime test was performed by this audit.
