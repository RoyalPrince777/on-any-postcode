# Factory Studio graphics capability acquisition — draft

One canonical Studio, existing Founder provider catalogue and preflight. No new renderer, queue, provider payment, upload or deployment. Source links are discovery, not installed dependencies. No source or weights copied by this change.

## First-party acquisition order
1. Babylon.js and local glTF Transform/meshoptimizer: keep existing TDA engine; review pinned revisions, licences and notices, validate output and local decoders.
2. Blender as isolated worker for mesh cleanup, UVs, rigging and PBR texture baking; review GPL integration/distribution.
3. TripoSR and TRELLIS: approved GPU worker, pinned code/weights, dependency and licence review; record asset origin, output hash, duration, worker identity and errors.
4. Audio2Face or Rhubarb: approved owned voice and rig, separate SDK/model terms, map output to morph targets. No biometric identification or external upload.
5. Codex CLI: open agent harness, separate inference backend and network policy. Claude, Meshy, Tripo API and Substance: optional licensed tools; no automatic spending or egress. Unreal: reference only.

## Handoff
Existing Studio -> existing Organiser/worker registry -> approved asset store -> GLB + manifest -> existing TDA Babylon.js loader (port 5052). Do not start a parallel engine. No implementation of this handoff is claimed by this catalogue patch.

Redmi A5 acceptance target (not measured): stable 30 FPS gameplay in Mitcham, lower resolution/LOD/texture sizes on thermal or frame-budget pressure; optional 60 FPS only where measured sustainable. Offline load after assets are installed, no missing decoder or external fetch. Record exact device, browser, commit, asset hash, p50/p95 frame time, crash and memory/thermal observations. Verify visual quality, gameplay controls and rollback. Independent Guardian/HRM and Founder Final required. No Green for code, catalogue or CI alone.

## Local asset inspection implementation
`studio_local_media.inspect_owned_glb` is a bounded read-only helper for authenticated owner-scoped callers. Checks container layout, strict self-contained URI policy, buffer length and SHA-256; not full glTF validation, rendering, dispatch, optimization or native worker evidence. No route or queue added. Tests cover malformed, external and traversal inputs. Runtime wiring requires existing authenticated worker and asset ownership proof.

## Native optimization source acquired
MIT meshoptimizer v1.0 vertex cache/fetch subset is vendored in `third_party/meshoptimizer` at upstream commit `73583c335e541c139821d0de2bf5f12960a04941`. Unmodified upstream files and full MIT notice retained, with blob provenance in UPSTREAM.json. Native C++ compile/run acceptance checks triangle preservation and vertex remapping. This is source acquisition, not full meshoptimizer, GLB rewrite, GPU performance, Studio dispatch or TDA runtime proof. No new permission or executor. Build only in the existing authorized engineering environment; do not promote on CI alone.
