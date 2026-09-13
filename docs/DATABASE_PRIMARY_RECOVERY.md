# OAP Primary PostgreSQL Recovery

OAP resolves its production PostgreSQL connection in this order:

1. `OAP_PRIMARY_DATABASE_URL_B64`
2. `OAP_PRIMARY_DATABASE_URL`
3. `DATABASE_URL`
4. legacy `OAP_DB_SECRET_B64`
5. legacy `OAP_NEON_DATABASE_URL_B64`
6. legacy `OAP_NEON_DATABASE_URL`

The provider-neutral primary settings and platform `DATABASE_URL` intentionally win over legacy Neon aliases. This allows an independent PostgreSQL service to carry OAP when Neon is unavailable without deleting the old configuration first.

An explicitly selected but malformed base64 primary value fails closed and does not fall through to another database.

No migration runs at import or startup. On Render, OAP World emits one redacted, read-only startup proof containing only configuration class, reachability, schema readiness, pending migration count and error class. It never logs a database URL, password, identity or row content.

Schema initialization still requires explicit Human Authority approval through the existing `oap-init-postgres --yes` command. Certification issuance remains separately gated and cannot create a profile, grant permissions or grant Founder access.
