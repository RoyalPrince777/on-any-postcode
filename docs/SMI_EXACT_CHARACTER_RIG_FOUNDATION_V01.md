# SMI exact-character rig foundation v0.1 · DESIGN ONLY

**Scope:** Preserve the exact, already-approved SMI Live Chat artwork and
state bus. No image modification, substitute character, generated layers,
fake animation, background listening, production activation, data writes,
voice/text storage or visible Live Status.

## Existing proof vs gap

- The first-party artwork is `static/oap/smi_live_chat_dashboard.jpg`.
  Its repository-approved SHA-256 is
  `f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b`.
  Keep existing immutable artwork tests.
- `smi_live_character_state.js` is the canonical state bus. Presence CSS
  currently varies glow/scale/position of a still. That is NOT tracked body
  language, skeletal deformation, visemes or visual speech synchronization.
- New `smi_exact_character_rig.js` is an inert, passive seven-layer
  contract connected to that bus. It renders **zero** frames and reports
  **zero** proven layers regardless of incoming claims or state. Its
  snapshot is available to private first-party code only. It makes no
  network requests, microphone requests, recordings or durable writes.
- STOP is sticky: late events cannot resume; a separate explicit human
  reset may clear the STOP marker but never activates rig output.

## Future seven-layer evidence contract

| Layer | Required evidence before motion can be labelled real |
|---|---|
| Eyes | Approved identity-preserving eye regions, landmarks, gaze/blink tracking and tests. |
| Head | Approved head segmentation/pivots, motion boundaries, camera consistency. |
| Breathing | Valid independent torso layers and physically restrained breathing curves. |
| Mouth visemes | Approved mouth geometry; phoneme/viseme timing aligned to actually played audio with STOP cancellation. |
| Face | Approved expressions, landmarks and identity-preserving deformation tests. |
| Hands | Both approved hand regions, segmentation and safe gesture curves. |
| Upper body | Approved torso/shoulder geometry, consistent depth, independent rig. |

All seven require approved originating assets, exact source hash/provenance,
manual identity and quality approval, accessible reduced-motion fallback,
layer interaction tests, genuine replay/synchronisation evidence and Human
Authority final. A still photograph or CSS filter passes none of these.

## 3× / 7× / 21× war-room gate

- **Mind 1–7:** source identity, one surface, invisible Live Status,
  canonical controls, thinking panel, state bus and evidence-only claims.
- **Body 8–14:** seven layer contracts above; do not conflate listener/
  thinker/speaker/paused/stopped labels with rig movement.
- **Soul 15–21:** typed consent, local approved learning, private HRM
  provenance, corrections, cancellation, youth/privacy safeguards,
  signed-in Android evidence and Founder Final remain independent gates.

The existing four quarters remain the ONLY protocol. This foundation is
a design/test checkpoint, **not** independent 50%, 75% or 100% production
certification. No activation, merge, deployment or private-data mutation
is authorised by this document or its CI.
