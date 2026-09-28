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
8. Require the `OAP runtime image` workflow to publish the exact reviewed
   commit to GHCR. Production Core promotion uses the immutable image digest
   recorded in `deploy/render-core-release.json`; do not rebuild Core on
   Render when the image already exists.
9. Merge-add the Auth and exact Founder authority values on Render without
   changing existing secret values. Never store the Founder password in an
   environment variable, source, logs or deployment notes. The browser must
   request only the Founder password; it must not request or display the
   server-side Auth selector.
10. Temporarily merge-add a 32+ character `OAP_FOUNDER_ACTIVATION_TOKEN`, then
   trigger one manual Render deployment of the reviewed commit.
11. After that deployment is live, open `/activate-founder` on the main OAP
    origin and create the Founder password. The route supplies the configured
    Founder email server-side and refuses to run once any managed Auth user
    exists.
12. Bind the resulting exact user UUID to `OAP_HUMAN_AUTHORITY_ID`, remove the
    activation token, and disable new email/password signup in Neon Auth. Wait
    for the resulting Render configuration deployment to become live.
13. Verify every public read route remains anonymous, private anonymous requests
    return redirect/401, and a controlled non-Founder session receives 403 from
    My World, SMI, Mission Control, infrastructure and private assets.
14. Verify `/livez` reports `alive`, `/healthz` reports `healthy`, the SMI gateway
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


## Image-first Core deployment

The production Core service `on-any-postcode` is declared as a Render
`runtime: image` target in `render.yaml`. The image must be pinned by digest,
not by a mutable tag. `deploy/render-core-release.json` records the exact Core
GHCR digest and existing Render service ID. The separate shared-image manifest
remains the SMI baseline until that service is independently promoted and
verified. This keeps the public service identity stable while decoupling Core
releases from Render build-pipeline minutes.

Do not replace Render-managed secrets during image promotion. Do not create a
second Core service merely to bypass a build quota. A release is not Green until
the existing Core service reports the promoted image live, `/healthz` passes,
and the relevant public browser acceptance passes.


## OAP Release Control Plane

Before any production mutation, run `python scripts/release_preflight.py`. The preflight is read-only and fail-closed. It validates the immutable Core and SMI release contracts and checks whether Render image-update authority is actually present.

The machine-readable policy is `deploy/oap-release-control-plane.json`.

Release order is fixed:

1. immutable-image promotion to the existing service;
2. existing-service source deploy only when build capacity is available;
3. otherwise hold production unchanged.

Creating a duplicate service to bypass quota, redeploying a known old image as progress, or claiming Green without live read-back is prohibited.


### Render CLI image fallback

If the deploy-hook and API-key promotion paths are unavailable but an authenticated Render CLI session exists, deploy the exact immutable image to the existing Core service with:

`render deploys create srv-d8gfsv0jo6nc73egdlf0 --image <immutable-image-ref> --wait --confirm -o json`

This path does not require a Render source build and must preserve the existing service ID. Authentication is still provider-controlled; do not store CLI tokens in the repository.
