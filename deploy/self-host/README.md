# Self-host compose notes (not production-certified)

This is the **smallest app/database/HTTPS skeleton**, not a live PTT release.

- Copy a reviewed secrets file to `deploy/self-host/.env`; never commit it.
- Set `OAP_HOSTNAME`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` and every application-required secret and database connection variable as determined by the existing runtime.
- Validate `docker compose -f deploy/self-host/compose.yaml config` before deployment.
- Database and Gunicorn ports are private; gateway alone publishes HTTP/HTTPS.
- Ensure the production Flask application uses PostgreSQL credentials matching the database service; this configuration **does not assume** a particular existing app DB environment-variable name.
- Run the repository's **explicit, verified** migration procedure; do not assume migration 0013 was applied.
- Confirm proxy headers, trusted hosts, HTTPS cookie policy, CSRF, rate limits and administrative-route isolation.
- Configure off-host encrypted backup/restore and disk monitoring before public traffic.
- **TURN is deliberately not included** until short-lived credential issuance and firewall/relay rules are implemented and reviewed. Current browser `iceServers: []` means public cross-network PTT is NOT ready.
- Do not change DNS, enable public PTT, or assert Green without Founder Final and physical-device evidence.

See `docs/OAP_PTT_SELF_HOST_RELEASE_CONTRACT.md`.
