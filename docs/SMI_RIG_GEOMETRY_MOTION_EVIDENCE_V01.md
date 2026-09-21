# SMI exact character · geometry and motion evidence v0.1

**Scope:** The approved still image remains the only visual character. The
inert client rig in merged PR #462 and offline private layer byte verifier in
merged PR #463 remain the only previous Body foundations. No rendered motion
is enabled by this document, module or its tests.

## New offline structural contract

`oap.smi.character_rig_geometry.inspect_geometry(bundle, asset_report)`
accepts only the exact approved source SHA-256, a *previously byte-checked*
seven-layer asset report and seven geometry records. Every layer must contain
named normalized 2-D anchors and a bounded, strictly increasing motion
timeline. The mouth layer also requires bounded viseme/audio timestamp
**metadata**, not actual audio. Missing layers, out-of-range/NaN coordinates,
coincident essential anchors, duplicate/out-of-order times, excessive deltas,
missing mouth metadata and incompatible source hashes fail closed.

Even all seven structurally consistent records produce only
`schema_only_requires_independent_visual_motion_and_audio_proof`.
`active`, `emits_frames`, `identity_proven`, `geometry_proven`,
`motion_proven`, `speech_sync_proven` and
`human_authority_approved` are always **false**. These result fields are
hardcoded; neither manifest-supplied `founder_approved` nor a fake
`enable_rig` value can flip them.

## What real proof would require

1. Founder-reviewed **actual** segmented eyes, head, breathing torso, mouth,
   face, both hands and upper body derived from the approved image; actual
   origin/source identities and private layer hashes.
2. Human visual inspection of the overlays, pivot placement, occlusion,
   repeated poses and identity preservation. A JSON coordinate does not
   establish that a landmark matches a real pixel.
3. A verified motion runtime that deforms those layers convincingly without
   clipped edges, identity drift or false body-language descriptions.
4. Mouth visemes aligned to the **audio actually played**, not just typed
   text, generated metadata or predicted phoneme timestamps.
5. Immediate STOP across animation, voice and listening, stale callback
   suppression, manual restart and reduced-motion still fallback.
6. Signed-in Android proof, accessibility, consent and resource use.
7. Human Authority's explicit final approval of the *real* result.

The existing 25/50/75/100% four quarters are unchanged; this is a design and
regression-checkpoint within them, **not** a fifth gate or Body 7/7.
No public route, extra brain, alternative avatar, third-party telemetry,
background microphone, persisted voice/text or HRM write. The private
segmented source assets and production rig are **not present** in this PR.
