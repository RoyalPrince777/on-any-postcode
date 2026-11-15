# OAP Studio Intelligence — source-code build map

**Scope:** Upgrade the existing Founder-only OAP Studio under SMI. No second Factory, parallel auth stack, new publishing rail, or fake feature completion.

## Canonical source already in the repository (re-use, do not duplicate)

| Capability | Canonical path | Verified source intent | Remaining live proof |
|---|---|---|---|
| Studio coordinator / generation receipt | `mission_control/studio_intelligence.py` | Workspace routing, 21-stage contract, image/video job wrapper, HRM receipt | Actual provider render and artifact |
| Provider adapter | `mission_control/studio_media_backend.py` | OpenAI image generation/edit, image-reference video creation, job status/content | Credentials, live backend, video-input editing |
| Private Founder routes | `mission_control/views.py` | Founder-only+CSRF Studio API | Device session, runtime verification |
| Canonical SMI UI | `mission_control/templates/ollama_chat.html`, `mission_control/static/smi_media_controls.js`, `mission_control/static/smi_chat_final.js` | Studio launch, Create/Edit/Refine/Animate, Same Character | Real edit timeline and full upload UX |
| Mission/workspace steps | `mission_control/studio_workspace_orchestrator.py` | Non-consequential planning, owner checkpoints, next handoff | Real execution worker |
| Asset inventory | `mission_control/smi_founder_assets.py` | Owner-scoped Studio image indexes | Owned video blobs, hashes, quotas, retention |
| Rights check | `mission_control/rights_studio_adapter.py` | Rights Core mapping, publication deny by default | Per-person rights/consent evidence and video lineage |
| Public presentation only | `templates/studio_public.html`, `mission_control/public_studio_runtime.py` | Public read-only UI | No public access to Founder generation |
| Voice and synchronisation foundations | `mission_control/smi_reply_voice_local.py`, `mission_control/static/smi_reply_audio_player.js`, `mission_control/smi_real_reply_motion_bridge.js` | SMI speech and embodiment hooks | Studio voice asset chain and timestamped mouth-motion proof |
| Character geometry foundations | `oap/smi/character_rig_geometry.py`, `mission_control/static/smi_exact_character_rig.js` | Existing SMI character/rig work | Suitable actor full-body rig, tracking acceptance |
| Character-swap preflight (draft) | `mission_control/studio_character_swap.py` | UUID input and duration validation, hard-deny payment/render | Owner verification, live quote, adapter and render |
| Studio tests | `tests/test_oap_studio_intelligence.py`, `tests/test_studio_character_swap.py`, `tests/test_rights_studio_adapter.py` | API/receipt/governance coverage | End-to-end authenticated real-device evidence |

## External code to evaluate (link rather than wholesale vendor into OAP)

All packages remain behind first-party Studio interfaces. Pin revisions and review licensing **before** compiling or redistributing.

1. **FFmpeg + ffprobe** — clip probe/trim/transcode, compose layers/audio/subtitles, export MP4. https://ffmpeg.org/ and https://github.com/FFmpeg/FFmpeg . Default licensing LGPL; some compiled options enable GPL; codec patent considerations still apply.
2. **OpenTimelineIO** — timeline interchange and edit decision model. https://github.com/AcademySoftwareFoundation/OpenTimelineIO . Verify the license of the selected revision before adoption.
3. **MediaPipe** — body/hand landmarks and pose tracking for mobile-to-render job transfer. https://github.com/google-ai-edge/mediapipe . Investigate Android memory/CPU impact and license of model/task bundles.
4. **SAM 2** — instance masks to track an actor across frames. https://github.com/facebookresearch/sam2 . Apache 2.0 for referenced code/checkpoints; heavyweight GPU work should run on an authorised worker, not assumed local Redmi A5.
5. **whisper.cpp** — offline speech recognition, subtitles, words/timestamps. https://github.com/ggml-org/whisper.cpp . MIT license; model weights may have additional terms.
6. **Remotion** — optional React-based composition/rendering. https://github.com/remotion-dev/remotion . **Source-available, not OSI open source**; free/commercial eligibility is restricted by license and business type. Do not treat it as a free first-party dependency without review.
7. **Higgsfield Genjutsu** — optional remote provider for image-referenced source-video subject replacement. Not first-party/open-source code. Must have an owner-scoped provider adapter; provider account, quote and explicit spend consent all required. No credential or automation bypass.

## Missing first-party code (build on top of above, in priority order)

### A. Owned media input + job contract
- Owner-uploaded source MP4 and character PNG/JPEG, validated MIME, hash, byte size, duration, frame rate, resolution and licensing/consent metadata.
- Private immutable asset IDs; reject guessed UUIDs, unauthorised external URLs, non-owned files, arbitrary filesystem paths.
- One canonical StudioJob record: idempotency key, owner, source hashes, character lock, target subject, model/provider, requested edit, max credits, quote expiry, state, STOP, result and retention.
- Existing SMI/Guardian/HRM controls stay the authority; provider never approves itself.
- Durable preflight receipt: distinguishes `prepared`, `quoted`, `approved`, `submitted`, `rendered`, `verified`, `released` (do not create a 21-step human interface).

### B. Real media processing
- FFprobe parser and guarded FFmpeg trim/transcode worker with time/memory/output bounds, no shell string interpolation, temp directories inside owner-scoped processing root.
- Preserve original audio where licensed; no audio or motion quality claims before the output is checked.
- Video-subject masks/pose/occlusion via SAM 2/MediaPipe on authorised compute; character consistency registry (one approved identity).
- Optional Higgsfield adapter or other provider implementing prepare_quote / submit_after_approval / poll / fetch with safe ownership checks and spending cap.
- Local render fallback for overlays/compositing with FFmpeg where sufficient; distinguish graphic overlay from actual AI person replacement.

### C. Editing, sound, release
- Timeline object, clip trimming, transitions, titles, captions, sound mixing, version history and output manifests.
- Voice/subtitle adapters should build on existing SMI voice/speech components; do not clone identities without consent.
- Founder private mobile editor: upload, preview, select subject, lock character, quote, explicit Founder approval, progress, STOP, verified MP4.
- Rights/consent, retention and asset lineage checked before any public OAP TV/Market/Distribution publication.
- Device acceptance: Redmi A5 / Termux route, real 30s clip, output MP4 with preserved second person, correct identity and audio, no UI duplication.

## PR #1409 boundaries

Branch: `smi-studio-character-swap-gate-20261115`.
A **draft** feature; preparation does not create or pay for a Higgsfield job. Previously quoted 210 Higgsfield credits were an external quote for a 29.7s clip, **not** SMI price proof. Do not auto-spend, merge, deploy, or mark production Green. Keep all further Studio upgrades on this existing PR unless a truly independent concern justifies a separate branch.

## Acceptance evidence for first release

- Targeted Python tests + Ruff pass on exact latest head.
- Authenticated Founder can use the private Studio; anonymous/public requests denied.
- Files are owned and verified by server; no raw provider references trusted from request.
- Quote is fetched live and bound cryptographically or transactionally to owner/inputs, model, duration, credits, expiry.
- Explicit Founder credit consent matches that quote; single idempotent submission; STOP halts if possible; no duplicate charge.
- On success output is downloaded, checked with ffprobe, hashed, indexed privately, presented for review; failure shows the real error and safe retry.
- Guardian and HRM evidence present. Founder separately approves any external release.
- Real-device validation; no deployment claim without first-party runtime evidence.

*OAP Law: Research has no ceiling. Deployment has boundaries.*
