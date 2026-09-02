# OAP production deployment: Render + Neon

OAP runs as two Render web services: one public front door and one separate
private SMI gateway. Production secrets remain dashboard-managed and are not
committed to `render.yaml`.

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
OAP_PUBLIC_ORIGIN=https://on-any-postcode.onrender.com
OAP_SMI_PUBLIC_ORIGIN=https://oap-smi.onrender.com
OAP_SMI_GATEWAY_SECRET=<same 32+ character secret on both Render services>
OPENAI_API_KEY=<provider secret>
OAP_AI_PROVIDER=openai
OAP_AI_MODEL=<approved model>
OAP_AGENT_REGISTRY_APPROVED=true
```

`NEON_AUTH_BASE_URL` is configuration, not a credential. Database, provider and
session secrets must never appear in source, logs, deployment notes or health
responses.

The public My World entry must resolve through `OAP_SMI_PUBLIC_ORIGIN` to
`/mission?mode=mission`; relative `/mission` links on the public service
intentionally return `404`. The SMI allowlist admits only Auth, Mission, health,
private assets and the Founder-gated `/my-world` ecosystem-form routes. It must
not admit public signup or arbitrary public-service routes.

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
9. Temporarily merge-add a 32+ character `OAP_FOUNDER_ACTIVATION_TOKEN`, then
   trigger one manual Render deployment of the reviewed commit.
10. After that deployment is live, open `/activate-founder` on the main OAP
    origin and create the Founder password. The route supplies the configured
    Founder email server-side and refuses to run once any managed Auth user
    exists.
11. Bind the resulting exact user UUID to `OAP_HUMAN_AUTHORITY_ID`, remove the
    activation token, and disable new email/password signup in Neon Auth. Wait
    for the resulting Render configuration deployment to become live.
12. Verify every public read route remains anonymous, private anonymous requests
    return redirect/401, and a controlled non-Founder session receives 403 from
    My World, SMI, Mission Control, infrastructure and private assets.
13. Verify `/livez` reports `alive`, `/healthz` reports `healthy`, the SMI gateway
    returns the same healthy upstream state, and Render logs contain no new errors
    or `5xx` responses.

## Post-deploy verification

```bash
curl -fsS https://on-any-postcode.onrender.com/livez
curl -fsS https://on-any-postcode.onrender.com/healthz
curl -sS -o /dev/null -w '%{http_code}\n' \
  https://on-any-postcode.onrender.com/mission/brain/status
curl -sS -o /dev/null -w '%{http_code}\n' \
  https://oap-smi.onrender.com/mission/brain/status
```

The main-origin Mission probe must return `404`; the same private API through
the SMI gateway must return `401` without a session. Private HTML routes must
redirect to `/enter-my-world`; public OAP World and product routes must stay
available.

## Provider hardening after first release

There is no general web signup route for the private Founder identity. The
zero-user activation ceremony is temporary, code-gated, server-selected, and
closes after the first identity exists. Remove its token after use. The normal
OAP private login accepts only the password. Public browsing must not be tied to
registration. Before business or creator monetisation opens, implement a
separate verified onboarding and entitlement flow and test recovery with
controlled accounts. Do not turn the private login into public self-signup.
