# SMI → OAP Factory → Studio · Professional Provider Command

Founder-private, upgrade-only addition to the canonical SMI Command Dashboard
(`/mission/smi`). This is **not** a second Factory, a new chat identity, a
provider connection, a licence grant, a render receipt or release approval.

## What is actually implemented

- `GET /mission/studio/providers`: read-only, secret-free model-family
  catalogue and truth states, restricted to a signed-in Founder.
- `POST /mission/studio/providers/preflight`: Founder-only, CSRF-guarded
  validation of selected task, aspect ratio, seconds, rights, consent and
  external-data awareness. No raw brief/media/key accepted, no provider called,
  no charge, no job/receipt fabricated.
- Dashboard: mobile-first violet/gold model selector, director controls,
  local-only scene brief, copy, real preflight findings, links to existing
  `/mission/ollama`, War Room and official model documentation.
- Existing `studio_intelligence`, `studio_media_backend`, private sign-in,
  navigation, My Card, Guardian/HRM and Founder Final remain canonical.

## Model families · truth states

| Family | Function | Existing OAP adapter | Current claim |
| --- | --- | --- | --- |
| OAP Image / OAP Video | Image/edit, video/animate | OpenAI adapter in repo | code-only or configured-unverified, never live-proven by this UI |
| Nano Banana / Gemini Image | Image/edit | None in this change | research only |
| ByteDance Seedance | Text/reference video | None | research only |
| Higgsfield | Creator/video orchestration | None | research only |
| ElevenLabs | Voice/dubbing | None | research only |
| VoiceStudio | Optional on-device voice | None | research only; Android compatibility and model licences need proof |
| OAP Local Compositor | First-party FFmpeg editing | Local tooling in repo | source only; local runtime unverified |

Official references:
- Google Image: https://ai.google.dev/gemini-api/docs/image-generation
- ByteDance Seedance: https://seed.bytedance.com/en/seedance-enterprise/api
- Higgsfield: https://open.higgsfield.ai/quick-start
- ElevenLabs: https://elevenlabs.io/docs/overview/intro
- VoiceStudio: https://github.com/debpalash/VoiceStudio

Provider model identifiers, capabilities and pricing change. Resolve them from
the provider's latest authoritative API documentation *at adapter-review time*.
Never pass a model marketing label straight to an unverified remote endpoint.

## Release boundary

1. Independent code + dependency + permissions + licence review (including AGPL
   for redistributed tools and each downloaded model's own terms).
2. Authenticated private-session mobile smoke test on Redmi A5. Public 5052 must
   not expose Founder models, briefs, routes, CSRF tokens or private assets.
3. Separate real provider adapters with pinned model IDs and API schemas,
   allowlisted outbound hostnames, redaction, timeouts, secret storage and
   receipt-safe handling. No third-party biometric telemetry, voiceprints or
   identity templates. No external transfer without new explicit approval.
4. Provider cost quotation and upper bound; a *server-side* Founder approval
   receipt for that specific operation. Client checkboxes never authorise payment.
5. Idempotent job, STOP/cancel, recovery, asset rights, quality/ffprobe checks,
   content hash, output ownership and retention. Prove actual image/video/audio
   artefacts with device logs, not animations or mocked labels.
6. Independent Guardian and HRM review, Green Gate and explicit Founder Final.

Until then: no auto-repair, no autonomous spending, no provider uploads, no
merge/deploy, no fake Green. Keep War Room and all existing OAP routes intact.
