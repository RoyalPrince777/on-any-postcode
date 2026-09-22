# SMI Body — exact-character source package and still-layer review

## Physical deliverable; no replacement avatar

This builds actual **pixel-extracted, editable private layer PNGs** from the
exact approved repository image
`static/oap/smi_live_chat_dashboard.jpg`, SHA-256
`f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b`.

It does **not** fabricate eyes, teeth, a hidden jaw, unseen arms, shoulder
occlusion, depth or 3D geometry. It does **not** infer a mask from the original
still. Approved source masks are a necessary input and are **not present in
this PR**. Until then, no real SMI segmented package can be created.

## Founder mask workbench — actual first-party editor

Open `/mission/character-mask-workbench` after Founder sign-in. It verifies
the **exact original JPG SHA-256 in the browser**, then exposes one local
painting canvas per required region (eyes, head, breathing, mouth visemes,
face, hands, upper body). Paint, erase, undo the last stroke, import an
earlier full-size white-alpha PNG and download the current draft. Once all
seven contain painted pixels, the built-in, dependency-free ZIP writer saves
the seven full-canvas PNG masks and a draft-only manifest **to the local
device**. No mask is submitted to a server, third-party editor, external
model, analytics endpoint, microphone or HRM; a page reload does not retain
the private masks, so save your ZIP before leaving the page.

The workbench exports PNGs with **white RGB and variable alpha**; the
first-party extractor now accepts these as well as conventional L-mode
grayscale masks. Coloured alpha photos are rejected, and all masks must
match the original image dimensions. Unzip the locally downloaded draft in
a private directory and **review the masks before supplying them to the
extractor**. Drawing a mark or exporting a ZIP does not record approval,
generate occluded anatomy, or turn on motion.

## Prepare the real editable input

In a private local directory OUTSIDE `static/`, prepare exactly seven
**full-original-canvas grayscale L-mode or white-alpha RGBA PNG masks**, each named:

`eyes.png`, `head.png`, `breathing.png`, `mouth_visemes.png`,
`face.png`, `hands.png`, `upper_body.png`.

White reveals the corresponding **original pixels**; black makes them
transparent; gray is feathered alpha. Masks must be manually reviewed against
the exact same image, not approximations from a generic model or newly
generated SMI. Overlap between face/head/eyes is permitted for visual review;
the actual occlusion order requires an explicit human choice. Masked visible
pixels do not include hidden regions: those need separately reviewed
reconstruction before any head turn, mouth-opening or arm lift.

## Build privately; do not auto-publish

```bash
python scripts/build_smi_character_source.py \
  --masks /private/smi-reviewed-masks \
  --output /private/smi-packages/source-v1
```

The script rejects the wrong original, any absent/empty/symlinked, wrong-format
or wrong-sized mask, public `static/` input/output, and existing output.
It reads and crops **all seven masks before writing** to a private staged
directory. The result contains seven original-source RGBA PNGs with exact
offsets and mask digests, plus a private manifest. No public routes, avatars,
API calls, audio capture, database/HRM writes, network telemetry or motion.
Never commit the private mask/source package to GitHub.

For local still-image inspection, call
`oap.smi.character_layer_review.render_still_layer_review(..., layer_order=tuple(LAYERS))`
with the same private package and an unused private output PNG. It checks the
real source digest, verified package files, bbox registration and each
layer's original RGB pixels before rendering. It composites an editable
**still**, not true expression, body movement or lip-sync.

## Browser-local source-layer export (draft, stacked PR #484)

The same Founder workbench now has **Download seven source layers · DRAFT**.
After the exact original JPEG hash check and all seven nonempty hand-painted
masks, it crops RGBA layers from the original's decoded pixels **inside the
browser**, bundles seven PNGs and a `source-package.json` with source SHA-256,
per-layer PNG SHA-256 and registration boxes, and downloads them locally.
It never sends the artwork or masks to the server. No masks present means no
layer output; the original source JPEG is already in the repository, but it
does not by itself reveal anatomical segmentation or occluded parts.

The browser export is a separate draft-review format, **not** a substitute for
the existing Python extractor's independently verified private package.
The browser applies binary alpha at threshold 128 so selected pixels contain
the original RGB rather than guessed/interpolated hidden colors. Review rough
edges, overlap, depth and occlusion before any animation; do not mistake the
test-painted masks for approved SMI body segments. Each output is DRAFT and
cannot enable motion, lip-sync, public publishing or Founder Final.

## What it does NOT approve

Source-derived masks are **not** seven independently usable body parts.
A still source cannot reveal hidden teeth or hands; alpha crops alone cannot
give physically plausible head pivots, correct occlusion, viseme geometry,
continuous audio synchronization or real gestures. Existing PR #462 passive
rig, PR #463 private byte-verifier and PR #464 geometry-schema gate remain
unchanged. The mask generator and still compositor cannot set
`active`, `motion_proven` or `human_authority_approved` true.

**Next work** after real approved masks: inspect alignment and missing hidden
regions, reconstruct only with human approval, choose depth/order and pivots,
then build tested motion deformation and speech synchronisation in the same
first-party character controller. User consent, STOP, reduced-motion,
accessible still fallback and Human Authority remain binding.

No production deployment or claim of Body 7/7 arises from this PR. Live-proof
reporting is deliberately out of scope.
