# OAP production deployment: Render + Neon

OAP runs as one Render web service with one public front door and a verified
private zone. Production secrets remain dashboard-managed and are not committed
to `render.yaml`.

## Architecture

| Zone | Routes | Access |
|---|---|---|
| OAP World | `/`, `/world`, The Spot, public Link Up, learning, events and directories | Open; no account or password |
| Public health | `/livez`, `/healthz` | Public, redacted |
| Approved account actions | Private Link Up messages, market listing, SIKA requests | Managed Neon Auth; onboarding remains separate |
| My World | `/my-world`, `POST /myworld`, owner workspaces | Managed Neon Auth + exact Founder authority |
| SMI | `/mission/ollama`, chat and conversations | Managed Neon Auth + exact Founder authority |
| Mission Control | `/mission`, agents, brain, organism, infrastructure | Managed Neon Auth + exact Founder authority |

## Required Render environment

Set these through the Render dashboard or a merge-safe environment update. Never
replace the complete environment map just to add one key.

```text
DATABASE_URL=<Neon pooled production connection string>
NEON_AUTH_BASE_URL=<branch-specific Managed Neon Auth URL>
OAP_AUTH_REQUIRED=true
OAP_SESSION_SECRET=<unique high-entropy value>
OAP_HUMAN_AUTHORITY_EMAIL=<server-side Founder Auth selector; never rendered>
OAP_HUMAN_AUTHORITY_ID=<exact verified Founder UUID after setup>
OPENAI_API_KEY=<provider secret>
OAP_AI_PROVIDER=openai
OAP_AI_MODEL=<approved model>
OAP_AGENT_REGISTRY_APPROVED=true
```

`NEON_AUTH_BASE_URL` is configuration, not a credential. Database, provider and
session secrets must never appear in source, logs, deployment notes or health
responses.

## Safe release sequence

1. Create a Neon recovery branch from production.
2. Provision Managed Neon Auth on the production branch.
3. Verify `neon_auth.user.id` is UUID and the required public OAP schema exists.
4. Run `python -m compileall -q app.py mission_control oap`.
5. Run `ruff check app.py mission_control oap tests`.
6. Run `python -m pytest -q`.
7. Push the exact reviewed source to `main` and require green GitHub CI.
8. Merge-add the Auth and exact Founder authority values on Render without
   changing existing secret values. Never store the Founder password in an
   environment variable, source, logs or deployment notes. The browser must
   request only the Founder password; it must not request or display the
   server-side Auth selector.
9. Trigger one manual Render deployment of the reviewed commit.
10. Verify every public read route remains anonymous, private anonymous requests
    return redirect/401, and a controlled non-Founder session receives 403 from
    My World, SMI, Mission Control, infrastructure and private assets.
11. Verify `/healthz` reports `12/12`, SMI reports `21/21`, and Render logs contain
    no new errors or `5xx` responses.

## Post-deploy verification

```bash
curl -fsS https://on-any-postcode.onrender.com/livez
curl -fsS https://on-any-postcode.onrender.com/healthz
curl -sS -o /dev/null -w '%{http_code}\n' \
  https://on-any-postcode.onrender.com/mission/brain/status
```

The private API probe must return `401` without a session. Private HTML routes
must redirect to `/enter-my-world`; public OAP World and product routes must stay
available.

## Provider hardening after first release

There is no web signup route for the private Founder identity. Provision and
recover that managed identity out of band; the OAP private login accepts only
the password. Public browsing must not be tied to registration. Before business
or creator monetisation opens, implement a separate verified onboarding and
entitlement flow and test recovery with controlled accounts. Do not turn the
private login into public self-signup.
