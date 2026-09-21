# SMI first-party request trace — PR #472 (draft, evidence boundary)

This record captures source-code inspection, not a production runtime attestation. Keep the pull request draft; do not merge, deploy, or claim the four-stage Green Gate from these checks.

## Private text route
- `mission_control/smi_chat_runtime.py` installs `_grounded_provider` as `_core._provider`, and `_gateway_provider` calls `oap_inference_gateway.generate`.
- `oap_inference_gateway.generate` attempts loopback inference, then the authenticated Home Node bridge. Its compatibility callback for private chat now raises `first_party_inference_required`, including if local/bridge attempts fail or private media is unsupported.
- The raw external `_core._provider` remains as a compatibility export, and the `smi_chat_runtime_core.py` file still contains a direct external Responses API implementation. All other imports and direct call sites must be reviewed before asserting universal enforcement.

## Local inference boundary
- Configurable `OAP_INFERENCE_LOCAL_URL` is checked for HTTP(S) and a localhost/127.0.0.1/::1 hostname; embedded URL credentials and HTTP redirects are rejected.
- Source inspection and regression checks do not attest OS/container DNS, proxy configuration, egress firewall, or actual deployed runtime.

## Home Node bridge
- `home_node_bridge.submit_inference` requires a configured shared secret and a recently present worker. It queues work in process memory.
- Confirm worker identity, location, custody of request bytes at the hosted relay, authenticated poll/result handling, secret rotation, TLS, cancellation, retention and network egress. An OAP-controlled worker by itself does not certify the full bridge transport or hosting boundary.

## Private multimodal route
- `smi_chat_runtime_core.py` calls `media_intelligence.prepare` before generation. Audio transcription in `media_intelligence.py` uses an external API; private audio is now rejected ahead of that call.
- Private image/file/video inference has no certified first-party replacement in this PR. Blocking external fallback intentionally reduces functionality until first-party multimodal inference is provided.

## Other first-party scope
- `public_studio_runtime.py` still has an external compatibility engine via `generate_public`. Public prompts and tools must be classified separately; no universal OAP-first-party claim.
- `mission_control/telemetry.py` has optional outbound Datadog delivery. Default-off is not proof that production has no telemetry or external transmissions.
- Identity, private HRM writes, audit, outbound network traffic and the deployed exact SHA require observed end-to-end receipts; a code-level green cannot substitute.

## Required witnessed proof
1. Verify the exact active app commit, environment, and the full Founder request call path without exposing secrets.
2. Exercise private text, files, image, audio, and video under blocked external egress; assert no external AI/network calls occur and all unsupported modalities fail closed before preprocessing.
3. Disable local inference and Home Node independently and together; prove no external fallback or HRM persistence of a fabricated answer.
4. Prove Home Node worker custody and transport, and check direct raw-provider call sites.
5. Test outbound telemetry disabled and network egress denied at infrastructure level.
6. Keep changes draft until all relevant CI, adversarial tests, rollback evidence and Founder final approval are recorded.

CI #2182 passed on `f3796bbb` before this documentation commit. This document alone does not advance certified percentages or runtime gates.
